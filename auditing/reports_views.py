"""
Views for generating reports and analytics data.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Q, Avg
from assets.models import Asset
from users.models import Employee, Department
from software.models import InstalledSoftware, License, SoftwareCatalog
from auditing.models import ComplianceWarning
from datetime import datetime, timedelta


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def employees_with_assets_report(request):
    """
    Generate report of employees with their assigned assets.

    Filters:
    - department: Filter by department ID
    - has_assets: true/false - only employees with/without assets
    """
    department_id = request.query_params.get('department')
    has_assets = request.query_params.get('has_assets')

    employees = Employee.objects.select_related('department').prefetch_related('assets')

    if department_id:
        employees = employees.filter(department_id=department_id)

    if has_assets == 'true':
        employees = employees.filter(assets__isnull=False).distinct()
    elif has_assets == 'false':
        employees = employees.filter(assets__isnull=True)

    data = []
    for emp in employees:
        assets_list = []
        for asset in emp.assets.all():
            assets_list.append({
                'inventory_code': asset.inventory_code,
                'asset_type': asset.get_asset_type_display(),
                'brand': asset.brand,
                'model': asset.model,
                'status': asset.get_status_display(),
            })

        data.append({
            'rut': emp.rut,
            'name': f"{emp.first_name} {emp.last_name}",
            'email': emp.email,
            'position': emp.position,
            'department': emp.department.name if emp.department else 'Sin departamento',
            'assets_count': len(assets_list),
            'assets': assets_list,
        })

    return Response({
        'count': len(data),
        'results': data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def assets_by_specs_report(request):
    """
    Generate report of assets filtered by hardware specifications.

    Filters:
    - ram_max: Maximum RAM in GB (e.g., 8 for assets with less than 8GB)
    - ram_min: Minimum RAM in GB
    - asset_type: Filter by asset type
    - status: Filter by status
    - department: Filter by department ID
    - has_employee: true/false - only assets assigned/unassigned
    """
    ram_max = request.query_params.get('ram_max')
    ram_min = request.query_params.get('ram_min')
    asset_type = request.query_params.get('asset_type')
    asset_status = request.query_params.get('status')
    department_id = request.query_params.get('department')
    has_employee = request.query_params.get('has_employee')

    assets = Asset.objects.select_related(
        'employee', 'department', 'computerdetail'
    ).prefetch_related('storage_devices', 'graphics_cards')

    # Apply filters
    if asset_type:
        assets = assets.filter(asset_type=asset_type)

    if asset_status:
        assets = assets.filter(status=asset_status)

    if department_id:
        assets = assets.filter(department_id=department_id)

    if has_employee == 'true':
        assets = assets.filter(employee__isnull=False)
    elif has_employee == 'false':
        assets = assets.filter(employee__isnull=True)

    # RAM filters (requires computerdetail)
    if ram_max:
        assets = assets.filter(
            computerdetail__isnull=False,
            computerdetail__ram_gb__lte=float(ram_max)
        )

    if ram_min:
        assets = assets.filter(
            computerdetail__isnull=False,
            computerdetail__ram_gb__gte=float(ram_min)
        )

    data = []
    for asset in assets:
        computer_detail = getattr(asset, 'computerdetail', None)

        data.append({
            'inventory_code': asset.inventory_code,
            'serial_number': asset.serial_number,
            'asset_type': asset.get_asset_type_display(),
            'brand': asset.brand,
            'model': asset.model,
            'status': asset.get_status_display(),
            'acquisition_date': asset.acquisition_date,
            'employee': f"{asset.employee.first_name} {asset.employee.last_name}" if asset.employee else 'Sin asignar',
            'employee_email': asset.employee.email if asset.employee else '',
            'department': asset.department.name if asset.department else 'Sin departamento',
            'ram_gb': computer_detail.ram_gb if computer_detail else None,
            'cpu_model': computer_detail.cpu_model if computer_detail else '',
            'os_name': computer_detail.os_name if computer_detail else '',
            'os_version': computer_detail.os_version if computer_detail else '',
        })

    return Response({
        'count': len(data),
        'results': data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def software_installations_report(request):
    """
    Generate report of software installations.

    Filters:
    - software_id: Filter by specific software
    - has_license: true/false - installations with/without license
    - department: Filter by department of the asset
    """
    software_id = request.query_params.get('software_id')
    has_license = request.query_params.get('has_license')
    department_id = request.query_params.get('department')

    installations = InstalledSoftware.objects.select_related(
        'software', 'asset', 'asset__employee', 'asset__department', 'license'
    )

    if software_id:
        installations = installations.filter(software_id=software_id)

    if has_license == 'true':
        installations = installations.filter(license__isnull=False)
    elif has_license == 'false':
        installations = installations.filter(license__isnull=True)

    if department_id:
        installations = installations.filter(asset__department_id=department_id)

    data = []
    for inst in installations:
        data.append({
            'software_name': inst.software.name,
            'software_developer': inst.software.developer,
            'version': inst.version or 'N/A',
            'install_date': inst.install_date,
            'asset_code': inst.asset.inventory_code,
            'asset_type': inst.asset.get_asset_type_display(),
            'employee': f"{inst.asset.employee.first_name} {inst.asset.employee.last_name}" if inst.asset.employee else 'Sin asignar',
            'department': inst.asset.department.name if inst.asset.department else 'Sin departamento',
            'has_license': inst.license is not None,
            'license_key': inst.license.license_key[-4:] if inst.license and inst.license.license_key else '',
        })

    return Response({
        'count': len(data),
        'results': data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def licenses_usage_report(request):
    """
    Generate report of license usage.

    Filters:
    - software_id: Filter by specific software
    - status: 'available', 'full', 'exceeded' - filter by usage status
    """
    software_id = request.query_params.get('software_id')
    usage_status = request.query_params.get('status')

    licenses = License.objects.select_related('software').prefetch_related('installations')

    if software_id:
        licenses = licenses.filter(software_id=software_id)

    data = []
    for lic in licenses:
        in_use = lic.installations.count()
        available = lic.quantity - in_use
        usage_percentage = (in_use / lic.quantity * 100) if lic.quantity > 0 else 0

        # Determine status
        if in_use > lic.quantity:
            status_label = 'exceeded'
        elif in_use == lic.quantity:
            status_label = 'full'
        else:
            status_label = 'available'

        # Apply status filter
        if usage_status and status_label != usage_status:
            continue

        data.append({
            'software_name': lic.software.name,
            'software_developer': lic.software.developer,
            'license_key_display': f"****-****-****-{lic.license_key[-4:]}" if lic.license_key and len(lic.license_key) > 4 else 'Sin clave',
            'quantity': lic.quantity,
            'in_use': in_use,
            'available': available,
            'usage_percentage': round(usage_percentage, 1),
            'purchase_date': lic.purchase_date,
            'expiration_date': lic.expiration_date,
            'status': status_label,
        })

    return Response({
        'count': len(data),
        'results': data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def warnings_report(request):
    """
    Generate report of compliance warnings.

    Filters:
    - status: Filter by warning status
    - category: Filter by category
    - date_from: Filter warnings from this date (YYYY-MM-DD)
    - date_to: Filter warnings until this date (YYYY-MM-DD)
    - department: Filter by department of the asset
    """
    warning_status = request.query_params.get('status')
    category = request.query_params.get('category')
    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')
    department_id = request.query_params.get('department')

    warnings = ComplianceWarning.objects.select_related(
        'asset', 'asset__employee', 'asset__department', 'resolved_by'
    )

    if warning_status:
        warnings = warnings.filter(status=warning_status)

    if category:
        warnings = warnings.filter(category=category)

    if date_from:
        warnings = warnings.filter(detection_date__gte=date_from)

    if date_to:
        warnings = warnings.filter(detection_date__lte=date_to)

    if department_id:
        warnings = warnings.filter(asset__department_id=department_id)

    data = []
    for warning in warnings:
        data.append({
            'id': warning.id,
            'asset_code': warning.asset.inventory_code,
            'asset_type': warning.asset.get_asset_type_display(),
            'employee': f"{warning.asset.employee.first_name} {warning.asset.employee.last_name}" if warning.asset.employee else 'Sin asignar',
            'department': warning.asset.department.name if warning.asset.department else 'Sin departamento',
            'category': warning.category,
            'description': warning.description,
            'detection_date': warning.detection_date,
            'status': warning.get_status_display(),
            'resolved_by': warning.resolved_by.username if warning.resolved_by else '',
            'resolution_notes': warning.resolution_notes,
        })

    return Response({
        'count': len(data),
        'results': data
    })
