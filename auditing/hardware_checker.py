"""
Utilities for checking hardware obsolescence.
"""
from typing import List, Dict, Any
from assets.models import Asset
from .models import HardwareObsolescenceRules


def parse_windows_version(version_string: str) -> tuple:
    """
    Parse Windows version string to tuple for comparison.
    Example: "10.0.22621" -> (10, 0, 22621)
    """
    if not version_string:
        return (0, 0, 0)

    try:
        parts = version_string.split('.')
        return tuple(int(p) for p in parts)
    except (ValueError, AttributeError):
        return (0, 0, 0)


def check_asset_obsolescence(asset: Asset, rules: HardwareObsolescenceRules) -> Dict[str, Any]:
    """
    Check if an asset meets obsolescence criteria.

    Returns:
        dict with keys:
            - is_obsolete: bool
            - reasons: list of strings describing why it's obsolete
            - details: dict with specific values that failed checks
    """
    if not rules.enabled:
        return {
            'is_obsolete': False,
            'reasons': [],
            'details': {}
        }

    # Only check computers (NOTEBOOK and DESKTOP)
    if asset.asset_type not in ['NOTEBOOK', 'DESKTOP']:
        return {
            'is_obsolete': False,
            'reasons': [],
            'details': {}
        }

    reasons = []
    details = {}

    # Check if computer detail exists
    if not hasattr(asset, 'computerdetail'):
        return {
            'is_obsolete': False,
            'reasons': ['Sin datos de hardware'],
            'details': {}
        }

    computer = asset.computerdetail

    # Check Windows version
    if computer.os_name and 'Windows' in computer.os_name:
        current_version = parse_windows_version(computer.os_version)
        min_version = parse_windows_version(rules.windows_min_version)

        if current_version < min_version:
            reasons.append(f'Sistema operativo obsoleto: {computer.os_name} {computer.os_version}')
            details['os_version'] = computer.os_version
            details['os_min_required'] = rules.windows_min_version

    # Check RAM
    if computer.ram_gb is not None:
        if computer.ram_gb < rules.ram_min_gb:
            reasons.append(f'RAM insuficiente: {computer.ram_gb} GB (mínimo: {rules.ram_min_gb} GB)')
            details['ram_gb'] = computer.ram_gb
            details['ram_min_required'] = rules.ram_min_gb

    # Check disk space (any disk below threshold)
    storage_devices = asset.storage_devices.all()
    for disk in storage_devices:
        if disk.capacity_gb and disk.free_space_gb is not None:
            free_percent = (disk.free_space_gb / disk.capacity_gb) * 100
            if free_percent < rules.disk_min_free_percent:
                reasons.append(
                    f'Disco con poco espacio: {disk.model or "Disco"} - '
                    f'{free_percent:.1f}% libre (mínimo: {rules.disk_min_free_percent}%)'
                )
                if 'low_disk_drives' not in details:
                    details['low_disk_drives'] = []
                details['low_disk_drives'].append({
                    'model': disk.model,
                    'free_percent': round(free_percent, 2),
                    'min_required': rules.disk_min_free_percent
                })

    return {
        'is_obsolete': len(reasons) > 0,
        'reasons': reasons,
        'details': details
    }


def get_obsolete_assets() -> List[Dict[str, Any]]:
    """
    Get all assets that are considered obsolete based on current rules.

    Returns:
        List of dicts with asset info and obsolescence reasons.
    """
    rules = HardwareObsolescenceRules.get_rules()

    if not rules.enabled:
        return []

    # Get all computers (NOTEBOOK and DESKTOP)
    assets = Asset.objects.filter(
        asset_type__in=['NOTEBOOK', 'DESKTOP']
    ).select_related('computerdetail', 'department', 'employee').prefetch_related('storage_devices')

    obsolete_list = []

    for asset in assets:
        check_result = check_asset_obsolescence(asset, rules)

        if check_result['is_obsolete']:
            # Build employee full name manually
            employee_name = None
            if asset.employee:
                employee_name = f"{asset.employee.first_name} {asset.employee.last_name}"

            obsolete_list.append({
                'asset': asset,
                'inventory_code': asset.inventory_code,
                'asset_type': asset.asset_type,
                'brand': asset.brand,
                'model': asset.model,
                'department': asset.department.name if asset.department else None,
                'employee': employee_name,
                'reasons': check_result['reasons'],
                'details': check_result['details'],
            })

    return obsolete_list
