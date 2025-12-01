"""
Views for analytics and chart data.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Q, Avg, Sum
from django.db.models.functions import TruncDate
from assets.models import Asset
from users.models import Employee, Department
from software.models import InstalledSoftware, License, SoftwareCatalog
from auditing.models import ComplianceWarning
from datetime import datetime, timedelta


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def assets_distribution(request):
    """
    Get distribution of assets by various dimensions.
    Returns data suitable for pie/donut charts.
    """
    # By type
    by_type = list(Asset.objects.values('asset_type').annotate(
        count=Count('id')
    ).order_by('-count'))

    for item in by_type:
        item['label'] = dict(Asset.AssetTypeChoices.choices).get(item['asset_type'], item['asset_type'])

    # By status
    by_status = list(Asset.objects.values('status').annotate(
        count=Count('id')
    ).order_by('-count'))

    for item in by_status:
        item['label'] = dict(Asset.StatusChoices.choices).get(item['status'], item['status'])

    # By department (Top 10)
    by_department = list(Asset.objects.filter(
        department__isnull=False
    ).values(
        'department__name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:10])  # Top 10 departments

    for item in by_department:
        item['label'] = item['department__name']

    # RAM distribution (for computers)
    ram_ranges = [
        {'label': '< 4GB', 'min': 0, 'max': 4},
        {'label': '4-8GB', 'min': 4, 'max': 8},
        {'label': '8-16GB', 'min': 8, 'max': 16},
        {'label': '16-32GB', 'min': 16, 'max': 32},
        {'label': '> 32GB', 'min': 32, 'max': 999},
    ]

    ram_distribution = []
    for range_item in ram_ranges:
        count = Asset.objects.filter(
            computerdetail__isnull=False,
            computerdetail__ram_gb__gte=range_item['min'],
            computerdetail__ram_gb__lt=range_item['max']
        ).count()
        ram_distribution.append({
            'label': range_item['label'],
            'count': count
        })

    return Response({
        'by_type': by_type,
        'by_status': by_status,
        'by_department': by_department,
        'ram_distribution': ram_distribution
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def employees_distribution(request):
    """
    Get distribution of employees.
    """
    # By department (Top 10)
    by_department = list(Employee.objects.filter(
        department__isnull=False
    ).values(
        'department__name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:10])  # Limit to Top 10

    for item in by_department:
        item['label'] = item['department__name']

    # Assets per employee distribution
    assets_per_employee = list(Employee.objects.annotate(
        assets_count=Count('assets')
    ).values('assets_count').annotate(
        employees=Count('id')
    ).order_by('assets_count'))

    for item in assets_per_employee:
        item['label'] = f"{item['assets_count']} assets"
        item['count'] = item['employees']

    return Response({
        'by_department': by_department,
        'assets_per_employee': assets_per_employee
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def warnings_analytics(request):
    """
    Get analytics data for compliance warnings.
    """
    # By status
    by_status = list(ComplianceWarning.objects.values('status').annotate(
        count=Count('id')
    ).order_by('-count'))

    for item in by_status:
        item['label'] = dict(ComplianceWarning.StatusChoices.choices).get(item['status'], item['status'])

    # By category
    by_category = list(ComplianceWarning.objects.values('category').annotate(
        count=Count('id')
    ).order_by('-count'))

    for item in by_category:
        item['label'] = item['category']

    # Trend over last 30 days
    thirty_days_ago = datetime.now() - timedelta(days=30)
    trend_data = list(ComplianceWarning.objects.filter(
        detection_date__gte=thirty_days_ago
    ).annotate(
        date=TruncDate('detection_date')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date'))

    # Fill in missing dates with 0
    date_range = []
    current_date = thirty_days_ago.date()
    end_date = datetime.now().date()

    while current_date <= end_date:
        existing = next((item for item in trend_data if item['date'] == current_date), None)
        date_range.append({
            'date': current_date.isoformat(),
            'count': existing['count'] if existing else 0
        })
        current_date += timedelta(days=1)

    return Response({
        'by_status': by_status,
        'by_category': by_category,
        'trend': date_range
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def software_analytics(request):
    """
    Get analytics data for software.
    """
    # Top 10 most installed software
    top_installed = list(SoftwareCatalog.objects.annotate(
        installations_count=Count('installations')
    ).filter(
        installations_count__gt=0
    ).values(
        'name', 'developer', 'installations_count'
    ).order_by('-installations_count')[:10])

    for item in top_installed:
        item['label'] = f"{item['name']} ({item['developer']})"
        item['count'] = item['installations_count']

    # License usage overview - grouped by software
    # Get all licenses grouped by software
    from collections import defaultdict

    licenses = License.objects.select_related('software').prefetch_related('installations').all()
    software_licenses = defaultdict(lambda: {'total': 0, 'in_use': 0, 'name': '', 'developer': ''})

    for lic in licenses:
        software_key = lic.software.id
        in_use = lic.installations.count()

        # Aggregate by software
        software_licenses[software_key]['name'] = lic.software.name
        software_licenses[software_key]['developer'] = lic.software.developer
        software_licenses[software_key]['total'] += lic.quantity
        software_licenses[software_key]['in_use'] += in_use

    # Convert to list and calculate available
    license_data = []
    for data in software_licenses.values():
        license_data.append({
            'name': f"{data['name']} ({data['developer']})",
            'total': data['total'],
            'in_use': data['in_use'],
            'available': max(0, data['total'] - data['in_use'])
        })

    # Sort by total quantity and take top 10
    license_data = sorted(license_data, key=lambda x: x['total'], reverse=True)[:10]

    # Software without licenses (installations count)
    software_without_license = InstalledSoftware.objects.filter(
        license__isnull=True
    ).values(
        'software__name', 'software__developer'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:10]

    for item in software_without_license:
        item['label'] = f"{item['software__name']} ({item['software__developer']})"

    return Response({
        'top_installed': top_installed,
        'license_usage': license_data,
        'without_license': list(software_without_license)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def summary_metrics(request):
    """
    Get summary metrics for dashboard overview.
    """
    # Total counts
    total_assets = Asset.objects.count()
    total_employees = Employee.objects.count()
    total_departments = Department.objects.count()

    # Assets by status
    assets_assigned = Asset.objects.filter(status=Asset.StatusChoices.ASSIGNED).count()
    assets_in_storage = Asset.objects.filter(status=Asset.StatusChoices.IN_STORAGE).count()
    assets_in_repair = Asset.objects.filter(status=Asset.StatusChoices.IN_REPAIR).count()

    # Warnings
    active_warnings = ComplianceWarning.objects.filter(
        status__in=[ComplianceWarning.StatusChoices.NEW, ComplianceWarning.StatusChoices.IN_REVIEW]
    ).count()

    # Software
    total_software = SoftwareCatalog.objects.count()
    total_licenses = License.objects.count()
    total_installations = InstalledSoftware.objects.count()

    # Compute average RAM
    avg_ram = Asset.objects.filter(
        computerdetail__isnull=False,
        computerdetail__ram_gb__isnull=False
    ).aggregate(Avg('computerdetail__ram_gb'))['computerdetail__ram_gb__avg']

    return Response({
        'assets': {
            'total': total_assets,
            'assigned': assets_assigned,
            'in_storage': assets_in_storage,
            'in_repair': assets_in_repair,
        },
        'employees': {
            'total': total_employees,
        },
        'departments': {
            'total': total_departments,
        },
        'warnings': {
            'active': active_warnings,
        },
        'software': {
            'total': total_software,
            'licenses': total_licenses,
            'installations': total_installations,
        },
        'hardware': {
            'avg_ram_gb': round(avg_ram, 2) if avg_ram else 0,
        }
    })
