from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count
from users.permissions import IsAdminOrReadOnly
from .models import SoftwareCatalog, InstalledSoftware, License, SoftwareVulnerability
from .serializers import (
    SoftwareCatalogSerializer,
    SoftwareCatalogDetailSerializer,
    InstalledSoftwareSerializer,
    LicenseSerializer,
    SoftwareVulnerabilitySerializer,
    LicenseInstallationSerializer,
    AssetWithLicenseStatusSerializer,
)
from .version_utils import generate_vulnerability_warnings, get_vulnerable_installations


class SoftwareCatalogPagination(PageNumberPagination):
    """
    Custom pagination class for software catalog.
    Allows clients to request custom page sizes up to max_page_size.
    """
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 500


class SoftwareCatalogViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows softwares to be viewed or edited.

    Supports:
    - Search: ?search=Adobe (searches name and developer)
    - Ordering: ?ordering=name or ?ordering=-installed_count
    - Pagination: ?page=2&page_size=50
    """

    queryset = SoftwareCatalog.objects.annotate(
        installed_count=Count('installations', distinct=True),
        license_count=Count('licenses', distinct=True)
    ).prefetch_related('software_vulnerabilities').order_by('name')
    permission_classes = [IsAuthenticated]
    pagination_class = SoftwareCatalogPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'developer']
    ordering_fields = ['name', 'developer', 'installed_count', 'license_count']

    def get_serializer_class(self):
        """Use detail serializer for retrieve action"""
        if self.action == 'retrieve':
            return SoftwareCatalogDetailSerializer
        return SoftwareCatalogSerializer


class InstalledSoftwareViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows softwares (installed) to be viewed or edited.
    """

    queryset = InstalledSoftware.objects.all()
    serializer_class = InstalledSoftwareSerializer
    permission_classes = [IsAuthenticated]


class LicenseViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows licences to be viewed or edited.

    Supports:
    - Filter by availability: ?available=true (shows licenses with available slots)
    """

    queryset = License.objects.all()
    serializer_class = LicenseSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        """Filter licenses by availability if requested"""
        queryset = super().get_queryset()

        # Filter by available licenses (those with unused slots)
        available = self.request.query_params.get('available', None)
        if available and available.lower() == 'true':
            # Annotate with usage count and filter where usage < quantity
            from django.db.models import Count, F
            queryset = queryset.annotate(
                usage_count=Count('installations')
            ).filter(usage_count__lt=F('quantity'))

        return queryset

    @action(detail=True, methods=['get'])
    def eligible_assets(self, request, pk=None):
        """
        Get all assets that have this license's software installed.
        Shows which ones have a license assigned and which don't.
        Only returns assets that have an employee assigned.
        """
        license = self.get_object()

        # Get all installations of this software, filtering only assets with employee assigned
        installations = InstalledSoftware.objects.filter(
            software=license.software,
            asset__employee__isnull=False  # Only assets with employee
        ).select_related('asset', 'asset__employee', 'license')

        # Build response data
        assets_data = []
        for inst in installations:
            # Generate masked license key if license exists
            license_key_masked = None
            if inst.license and inst.license.license_key:
                if len(inst.license.license_key) > 4:
                    license_key_masked = f"****-****-****-{inst.license.license_key[-4:]}"
                else:
                    license_key_masked = "Sin clave"

            assets_data.append({
                'id': inst.asset.id,
                'inventory_code': inst.asset.inventory_code,
                'brand': inst.asset.brand,
                'model': inst.asset.model,
                'asset_type': inst.asset.asset_type,
                'version': inst.version or '',
                'install_date': inst.install_date,
                'has_license': inst.license is not None,
                'license_assigned': license_key_masked,
                'installed_software_id': inst.id,
                'employee_name': f"{inst.asset.employee.first_name} {inst.asset.employee.last_name}",
                'employee_rut': inst.asset.employee.rut,
            })

        serializer = AssetWithLicenseStatusSerializer(assets_data, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def assign(self, request, pk=None):
        """
        Assign this license to an asset.
        Expects: {"installed_software_id": <id>}
        """
        license = self.get_object()
        installed_software_id = request.data.get('installed_software_id')

        if not installed_software_id:
            return Response(
                {'error': 'installed_software_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            installation = InstalledSoftware.objects.get(id=installed_software_id)
        except InstalledSoftware.DoesNotExist:
            return Response(
                {'error': 'Software instalado no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verify software matches
        if installation.software != license.software:
            return Response(
                {'error': 'El software del asset no coincide con el software de la licencia'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify it doesn't already have a license
        if installation.license is not None:
            return Response(
                {'error': f'Este asset ya tiene una licencia asignada ({installation.license.license_key_display})'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify we haven't exceeded quantity
        current_usage = license.installations.count()
        if current_usage >= license.quantity:
            return Response(
                {'error': f'No hay licencias disponibles (En uso: {current_usage}/{license.quantity})'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Assign the license
        installation.license = license
        installation.save()

        return Response({
            'success': True,
            'message': f'Licencia asignada a {installation.asset.inventory_code}',
            'in_use_count': license.installations.count()
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def unassign(self, request, pk=None):
        """
        Unassign this license from an asset.
        Expects: {"installed_software_id": <id>}
        """
        license = self.get_object()
        installed_software_id = request.data.get('installed_software_id')

        if not installed_software_id:
            return Response(
                {'error': 'installed_software_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            installation = InstalledSoftware.objects.get(id=installed_software_id)
        except InstalledSoftware.DoesNotExist:
            return Response(
                {'error': 'Software instalado no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verify it has this license assigned
        if installation.license != license:
            return Response(
                {'error': 'Este asset no tiene esta licencia asignada'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Unassign the license
        installation.license = None
        installation.save()

        return Response({
            'success': True,
            'message': f'Licencia desasignada de {installation.asset.inventory_code}',
            'in_use_count': license.installations.count()
        })


class SoftwareVulnerabilityViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing software vulnerabilities.
    Only admins can create/update/delete.
    """
    queryset = SoftwareVulnerability.objects.select_related('software').all()
    serializer_class = SoftwareVulnerabilitySerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['cve_id', 'title', 'software__name']
    ordering_fields = ['severity', 'created_at', 'safe_version_from']


@api_view(['POST'])
@permission_classes([IsAdminUser])
def scan_vulnerabilities(request):
    """
    Scan all installed software and generate ComplianceWarning entries
    for vulnerable installations.

    Also cleans up obsolete warnings for deleted vulnerabilities
    and resolved software updates.

    Only accessible by admin users.
    """
    try:
        result = generate_vulnerability_warnings()
        warnings_created = result['warnings_created']
        warnings_cleaned = result['warnings_cleaned']

        messages = []
        if warnings_created > 0:
            messages.append(f'{warnings_created} nueva(s) advertencia(s) creada(s)')
        if warnings_cleaned > 0:
            messages.append(f'{warnings_cleaned} advertencia(s) obsoleta(s) limpiada(s)')
        if not messages:
            messages.append('No se detectaron cambios')

        return Response({
            'success': True,
            'warnings_created': warnings_created,
            'warnings_cleaned': warnings_cleaned,
            'message': f'Escaneo completado. {". ".join(messages)}.'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def vulnerable_assets_list(request):
    """
    Get list of all assets with vulnerable software installations.
    Does NOT create warnings, just returns the data.
    """
    try:
        vulnerable = get_vulnerable_installations()
        return Response({
            'count': len(vulnerable),
            'results': vulnerable
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
