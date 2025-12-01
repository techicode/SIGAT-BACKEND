from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters
from django.utils import timezone
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404
from datetime import timedelta

from .models import AssetCheckin, ComplianceWarning, AuditLog, HardwareObsolescenceRules
from .serializers import (
    AssetCheckinSerializer,
    AssetCheckinPublicSerializer,
    ComplianceWarningSerializer,
    AuditLogSerializer,
    HardwareObsolescenceRulesSerializer,
    ObsoleteAssetSerializer,
    AgentHardwareReportSerializer,
    AgentReportResponseSerializer,
)
from .hardware_checker import get_obsolete_assets
from assets.models import Asset
from users.models import Employee
from software.models import License


class ComplianceWarningFilter(filters.FilterSet):
    """Custom filter for ComplianceWarning with 'active' parameter"""
    active = filters.BooleanFilter(method='filter_active', label='Active warnings only')

    class Meta:
        model = ComplianceWarning
        fields = {
            'status': ['exact'],
        }

    def filter_active(self, queryset, name, value):
        """Filter for active warnings (NUEVA or EN_REVISION)"""
        if value:
            return queryset.filter(
                Q(status=ComplianceWarning.StatusChoices.NEW) |
                Q(status=ComplianceWarning.StatusChoices.IN_REVIEW)
            )
        return queryset


class AuditLogFilter(filters.FilterSet):
    """Custom filter for AuditLog with date range and action filters"""
    date_from = filters.DateTimeFilter(field_name='timestamp', lookup_expr='gte', label='From date')
    date_to = filters.DateTimeFilter(field_name='timestamp', lookup_expr='lte', label='To date')

    class Meta:
        model = AuditLog
        fields = {
            'action': ['exact'],
            'target_table': ['exact'],
            'system_user': ['exact'],
        }


class AssetCheckinViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows checkins to be viewed or edited.

    Custom actions:
    - POST /asset-checkins/generate/ - Generate checkins for all employees with assets (admin only)
    - GET /asset-checkins/stats/ - Get checkin statistics (admin only)
    """

    queryset = AssetCheckin.objects.select_related('asset', 'employee').all().order_by("-requested_at")
    serializer_class = AssetCheckinSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def generate(self, request):
        """
        Generate check-in requests for all employees who have assigned assets.
        Creates one AssetCheckin per asset assigned to an employee.

        Returns list of created check-ins with their unique tokens.
        """
        # Get all assets that have an employee assigned
        assets_with_employees = Asset.objects.filter(
            employee__isnull=False
        ).select_related('employee')

        if not assets_with_employees.exists():
            return Response(
                {"detail": "No hay assets asignados a empleados."},
                status=status.HTTP_400_BAD_REQUEST
            )

        created_checkins = []
        for asset in assets_with_employees:
            # Create a new checkin for this asset
            checkin = AssetCheckin.objects.create(
                asset=asset,
                employee=asset.employee,
                status=AssetCheckin.StatusChoices.PENDING
            )
            created_checkins.append(checkin)

        serializer = self.get_serializer(created_checkins, many=True)
        return Response(
            {
                "message": f"{len(created_checkins)} check-ins generados exitosamente.",
                "checkins": serializer.data
            },
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def stats(self, request):
        """
        Get statistics about check-ins.

        Returns:
        - total: Total check-ins
        - pending: Pending check-ins
        - completed: Completed check-ins
        """
        total = AssetCheckin.objects.count()

        stats_by_status = AssetCheckin.objects.values('status').annotate(
            count=Count('id')
        )

        # Convert to dictionary for easier access
        stats_dict = {item['status']: item['count'] for item in stats_by_status}

        return Response({
            "total": total,
            "pending": stats_dict.get(AssetCheckin.StatusChoices.PENDING, 0),
            "completed": stats_dict.get(AssetCheckin.StatusChoices.COMPLETED, 0),
        })


class ComplianceWarningViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows compliances warning to be viewed or edited.

    Supports:
    - Search: ?search=NB001 (searches asset inventory code)
    - Filters: ?status=NUEVA or ?active=true (for NUEVA + EN_REVISION)
    - Ordering: ?ordering=-detection_date
    """

    queryset = ComplianceWarning.objects.select_related('asset', 'resolved_by').all().order_by("-detection_date")
    serializer_class = ComplianceWarningSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ComplianceWarningFilter
    search_fields = ['asset__inventory_code', 'category', 'description']
    ordering_fields = ['detection_date', 'status']

    def perform_update(self, serializer):
        """
        Update resolved_by based on status:
        - NUEVA: Clear resolved_by (nobody attending yet)
        - EN_REVISION: Set to current user (being reviewed)
        - RESUELTA: Set to current user (resolved)
        - FALSO_POSITIVO: Set to current user (marked as false positive)
        """
        status = serializer.validated_data.get('status')

        if status == ComplianceWarning.StatusChoices.NEW:
            # Clear resolved_by when returning to NEW status
            serializer.save(resolved_by=None)
        elif status in [
            ComplianceWarning.StatusChoices.IN_REVIEW,
            ComplianceWarning.StatusChoices.RESOLVED,
            ComplianceWarning.StatusChoices.FALSE_POSITIVE
        ]:
            # Set current user as the one attending/resolving
            serializer.save(resolved_by=self.request.user)
        else:
            # Shouldn't happen, but keep as fallback
            serializer.save()


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    Returns aggregated statistics for the dashboard.

    Returns:
        - total_assets: Total count of all assets
        - assigned_employees: Count of employees with at least one asset assigned
        - active_warnings: Count of warnings with status NUEVA or EN_REVISION
        - expiring_licenses: Count of licenses expiring in the next 30 days
    """

    # Total assets
    total_assets = Asset.objects.count()

    # Employees with at least one asset assigned
    assigned_employees = (
        Employee.objects.filter(assets__isnull=False).distinct().count()
    )

    # Active warnings (NUEVA or EN_REVISION)
    active_warnings = ComplianceWarning.objects.filter(
        Q(status=ComplianceWarning.StatusChoices.NEW)
        | Q(status=ComplianceWarning.StatusChoices.IN_REVIEW)
    ).count()

    # Licenses expiring in the next 30 days
    today = timezone.now().date()
    thirty_days_later = today + timedelta(days=30)
    expiring_licenses = License.objects.filter(
        expiration_date__isnull=False,
        expiration_date__gt=today,
        expiration_date__lte=thirty_days_later,
    ).count()

    stats_data = {
        "total_assets": total_assets,
        "assigned_employees": assigned_employees,
        "active_warnings": active_warnings,
        "expiring_licenses": expiring_licenses,
    }

    return Response(stats_data, status=status.HTTP_200_OK)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing audit logs (read-only, admin only).

    Supports:
    - Filters: ?action=CREATE&target_table=assets_asset&system_user=1
    - Date range: ?date_from=2024-01-01T00:00:00Z&date_to=2024-12-31T23:59:59Z
    - Search: ?search=NB001 (searches in details JSON)
    - Ordering: ?ordering=-timestamp
    """
    queryset = AuditLog.objects.select_related('system_user').all().order_by("-timestamp")
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = AuditLogFilter
    search_fields = ['action', 'target_table', 'details']
    ordering_fields = ['timestamp', 'action', 'target_table']


@api_view(['GET', 'PUT'])
@permission_classes([IsAdminUser])
def hardware_obsolescence_rules(request):
    """
    GET: Retrieve current hardware obsolescence rules
    PUT: Update hardware obsolescence rules

    Only accessible by admin users.
    """
    rules = HardwareObsolescenceRules.get_rules()

    if request.method == 'GET':
        serializer = HardwareObsolescenceRulesSerializer(rules)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = HardwareObsolescenceRulesSerializer(rules, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(updated_by=request.user)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obsolete_assets_list(request):
    """
    GET: Retrieve list of all assets considered obsolete based on current rules.

    Returns list of assets with reasons for obsolescence.
    """
    obsolete_data = get_obsolete_assets()
    serializer = ObsoleteAssetSerializer(obsolete_data, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def checkin_by_token(request, token):
    """
    GET: Retrieve check-in details by unique token (public, no auth required).

    Used by employees to access their check-in form via unique URL.
    """
    checkin = get_object_or_404(AssetCheckin, unique_token=token)

    # Check if already completed
    if checkin.status == AssetCheckin.StatusChoices.COMPLETED:
        return Response(
            {
                "detail": "Este check-in ya fue completado.",
                "checkin": AssetCheckinPublicSerializer(checkin).data
            },
            status=status.HTTP_200_OK
        )

    serializer = AssetCheckinPublicSerializer(checkin)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AllowAny])
def submit_checkin(request, token):
    """
    POST: Submit check-in response (public, no auth required).

    Expected payload:
    {
        "physical_state": "Excelente / Bueno / Regular / Malo",
        "performance_satisfaction": 1-5,
        "notes": "Optional notes"
    }
    """
    checkin = get_object_or_404(AssetCheckin, unique_token=token)

    # Check if already completed
    if checkin.status == AssetCheckin.StatusChoices.COMPLETED:
        return Response(
            {"detail": "Este check-in ya fue completado."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Update checkin with employee response
    serializer = AssetCheckinPublicSerializer(checkin, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save(
            status=AssetCheckin.StatusChoices.COMPLETED,
            completed_at=timezone.now(),
            checkin_date=timezone.now()
        )
        return Response(
            {
                "detail": "Check-in completado exitosamente. ¡Gracias!",
                "checkin": serializer.data
            },
            status=status.HTTP_200_OK
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def agent_hardware_report(request):
    """
    POST: Receive hardware report from SIGAT Windows agent (no auth required for MVP).

    This endpoint processes hardware information sent by the agent running on client computers.
    It will auto-create new assets if the BIOS UUID doesn't exist, or update existing ones.

    Expected payload structure:
    {
        "sistema_operativo": {
            "nombre": "Microsoft Windows 11 Pro",
            "version": "10.0.22621",
            "arquitectura": "AMD64"
        },
        "hardware": {
            "identificador_unico": "BIOS-UUID-HERE",
            "cpu": "Intel Core i7-9750H",
            "memoria_ram_gb": 16.0,
            "placa_base": {
                "fabricante": "Dell Inc.",
                "modelo": "0H2H4Y"
            },
            "almacenamiento": [
                {
                    "modelo": "Samsung SSD 970 EVO Plus 1TB",
                    "numero_serie": "S4EWNX0N123456",
                    "capacidad_gb": 953.87,
                    "espacio_libre_gb": 234.12
                }
            ],
            "gpus": ["NVIDIA GeForce GTX 1650"]
        },
        "software_instalado": [  # Optional
            {
                "nombre": "Microsoft Office",
                "desarrollador": "Microsoft Corporation",
                "version": "16.0.15831"
            }
        ]
    }

    Returns:
    {
        "success": true,
        "message": "Hardware report processed successfully",
        "asset_created": true/false,
        "asset_id": 123,
        "inventory_code": "AUTO-20241130-001",
        "warnings_generated": 2,
        "changes_detected": ["CPU changed", "RAM changed"]
    }
    """
    from assets.models import ComputerDetail, StorageDevice, GraphicsCard
    from software.models import SoftwareCatalog, InstalledSoftware
    from django.db import transaction

    # Validate payload
    serializer = AgentHardwareReportSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {
                "success": False,
                "message": "Invalid payload format",
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    validated_data = serializer.validated_data
    hardware_data = validated_data['hardware']
    os_data = validated_data['sistema_operativo']
    software_data = validated_data.get('software_instalado', [])
    suspicious_software_data = validated_data.get('software_sospechoso', [])

    unique_identifier = hardware_data['identificador_unico']
    asset_created = False
    warnings_generated = 0
    changes_detected = []

    try:
        with transaction.atomic():
            # Check if asset with this BIOS UUID exists
            try:
                computer_detail = ComputerDetail.objects.select_related('asset').get(
                    unique_identifier=unique_identifier
                )
                asset = computer_detail.asset
                asset_created = False

                # Detect hardware changes for warnings
                if computer_detail.cpu_model != hardware_data['cpu']:
                    changes_detected.append(f"CPU changed from '{computer_detail.cpu_model}' to '{hardware_data['cpu']}'")

                if computer_detail.ram_gb != hardware_data['memoria_ram_gb']:
                    changes_detected.append(
                        f"RAM changed from {computer_detail.ram_gb}GB to {hardware_data['memoria_ram_gb']}GB"
                    )

                if computer_detail.os_name != os_data['nombre']:
                    changes_detected.append(
                        f"OS changed from '{computer_detail.os_name}' to '{os_data['nombre']}'"
                    )

            except ComputerDetail.DoesNotExist:
                # Auto-create new asset
                asset_created = True

                # Determine asset type from chassis type
                # Chassis types from Win32_SystemEnclosure:
                # Notebooks/Laptops: 8, 9, 10, 11, 14, 18, 21, 31, 32
                # Desktops: 3, 4, 5, 6, 7, 15, 35
                chassis_type = hardware_data.get('tipo_chassis')

                # Laptop/Notebook chassis types
                LAPTOP_CHASSIS_TYPES = [8, 9, 10, 11, 14, 18, 21, 31, 32]
                # Desktop chassis types
                DESKTOP_CHASSIS_TYPES = [3, 4, 5, 6, 7, 15, 35]

                if chassis_type in LAPTOP_CHASSIS_TYPES:
                    asset_type = Asset.AssetTypeChoices.NOTEBOOK
                    prefix = "UPLA-NO-"
                elif chassis_type in DESKTOP_CHASSIS_TYPES:
                    asset_type = Asset.AssetTypeChoices.DESKTOP
                    prefix = "UPLA-DE-"
                else:
                    # Default to DESKTOP if chassis type unknown or not provided
                    asset_type = Asset.AssetTypeChoices.DESKTOP
                    prefix = "UPLA-DE-"

                # Find the next number for this asset type
                # Count existing assets with this prefix to get next number
                existing_count = Asset.objects.filter(
                    inventory_code__startswith=prefix
                ).count()
                next_num = existing_count + 1
                inventory_code = f"{prefix}{next_num:04d}"

                # Extract brand from motherboard manufacturer
                motherboard = hardware_data['placa_base']
                brand = motherboard['fabricante']

                # Generate serial number from BIOS UUID (shortened for readability)
                # Take last 12 characters of UUID
                serial_number = f"AGENT-{unique_identifier[-12:]}"

                # Create new asset (unassigned, no department)
                asset = Asset.objects.create(
                    inventory_code=inventory_code,
                    serial_number=serial_number,
                    brand=brand,
                    model=motherboard['modelo'],
                    asset_type=asset_type,
                    status=Asset.StatusChoices.IN_STORAGE,  # Unassigned
                    # employee=None, department=None by default
                )

                computer_detail = ComputerDetail.objects.create(asset=asset)

            # Update ComputerDetail with latest data
            computer_detail.cpu_model = hardware_data['cpu']
            computer_detail.ram_gb = hardware_data['memoria_ram_gb']
            computer_detail.os_name = os_data['nombre']
            computer_detail.os_version = os_data['version']
            computer_detail.os_arch = os_data['arquitectura']
            computer_detail.unique_identifier = unique_identifier
            computer_detail.motherboard_manufacturer = hardware_data['placa_base']['fabricante']
            computer_detail.motherboard_model = hardware_data['placa_base']['modelo']
            computer_detail.last_updated_by_agent = timezone.now()
            computer_detail.save()

            # Update storage devices (delete old, create new)
            asset.storage_devices.all().delete()
            for storage in hardware_data['almacenamiento']:
                StorageDevice.objects.create(
                    asset=asset,
                    model=storage['modelo'],
                    serial_number=storage['numero_serie'],
                    capacity_gb=storage['capacidad_gb']
                )

            # Update graphics cards (delete old, create new)
            asset.graphics_cards.all().delete()
            for gpu_model in hardware_data['gpus']:
                GraphicsCard.objects.create(
                    asset=asset,
                    model_name=gpu_model
                )

            # Process software installations (if provided)
            if software_data:
                # Clear existing software installations for this asset
                asset.installed_software.all().delete()

                for software_item in software_data:
                    # Try to find or create software in catalog
                    software_name = software_item['nombre']
                    software_developer = software_item.get('desarrollador', 'Unknown')
                    software_version = software_item.get('version', '')

                    software_catalog, created = SoftwareCatalog.objects.get_or_create(
                        name=software_name,
                        developer=software_developer
                    )

                    # Create installed software entry
                    InstalledSoftware.objects.create(
                        asset=asset,
                        software=software_catalog,
                        version=software_version,
                        install_date=timezone.now().date()
                    )

            # Generate automatic warnings for suspicious/illegal software
            if suspicious_software_data:
                for suspicious_sw in suspicious_software_data:
                    software_name = suspicious_sw['nombre']
                    path = suspicious_sw['ruta_instalacion']
                    reason = suspicious_sw['razon_sospecha']
                    evidence = suspicious_sw.get('evidencia', {})

                    # Build detailed evidence
                    warning_evidence = {
                        'agent_report': True,
                        'software_name': software_name,
                        'installation_path': path,
                        'reason': reason,
                        'developer': suspicious_sw.get('desarrollador', 'Unknown'),
                        'version': suspicious_sw.get('version', 'Unknown'),
                        'additional_evidence': evidence
                    }

                    ComplianceWarning.objects.create(
                        asset=asset,
                        category='Software Ilegal/No Autorizado',
                        description=f'Software sospechoso detectado: {software_name} ({reason})',
                        evidence=warning_evidence,
                        status=ComplianceWarning.StatusChoices.NEW
                    )
                    warnings_generated += 1

            # Generate automatic warnings for hardware changes
            if changes_detected:
                for change in changes_detected:
                    ComplianceWarning.objects.create(
                        asset=asset,
                        category='Hardware Change',
                        description=f'Cambio detectado por agente: {change}',
                        evidence={'agent_report': True, 'change': change},
                        status=ComplianceWarning.StatusChoices.NEW
                    )
                    warnings_generated += 1

            # Prepare response
            response_data = {
                'success': True,
                'message': 'Reporte de hardware procesado exitosamente',
                'asset_created': asset_created,
                'asset_id': asset.id,
                'inventory_code': asset.inventory_code,
                'warnings_generated': warnings_generated,
                'changes_detected': changes_detected
            }

            response_serializer = AgentReportResponseSerializer(data=response_data)
            if response_serializer.is_valid():
                return Response(response_serializer.data, status=status.HTTP_200_OK)
            else:
                # Shouldn't happen, but return raw data as fallback
                return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        # Log error and return failure response
        return Response(
            {
                "success": False,
                "message": f"Error processing hardware report: {str(e)}",
                "error": str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
