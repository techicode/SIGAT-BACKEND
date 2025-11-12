from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta

from .models import AssetCheckin, ComplianceWarning
from .serializers import AssetCheckinSerializer, ComplianceWarningSerializer
from assets.models import Asset
from users.models import Employee
from software.models import License


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
    - Filters: ?status=NUEVA
    - Ordering: ?ordering=-detection_date
    """

    queryset = ComplianceWarning.objects.select_related('asset', 'resolved_by').all().order_by("-detection_date")
    serializer_class = ComplianceWarningSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['asset__inventory_code', 'category', 'description']
    ordering_fields = ['detection_date', 'status']
    filterset_fields = {
        'status': ['exact'],
    }

    def perform_update(self, serializer):
        serializer.save(resolved_by=self.request.user)


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
