from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta

from .models import AssetCheckin, ComplianceWarning, AuditLog, HardwareObsolescenceRules
from .serializers import (
    AssetCheckinSerializer,
    ComplianceWarningSerializer,
    AuditLogSerializer,
    HardwareObsolescenceRulesSerializer,
    ObsoleteAssetSerializer
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
    """

    queryset = AssetCheckin.objects.all().order_by("-checkin_date")
    serializer_class = AssetCheckinSerializer
    permission_classes = [IsAuthenticated]


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
