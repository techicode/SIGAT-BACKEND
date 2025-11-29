"""
Utilities for comparing software versions and detecting vulnerabilities.
"""
from typing import List, Dict, Any, Tuple
import re


def parse_version(version_string: str) -> Tuple[int, ...]:
    """
    Parse a version string into a tuple of integers for comparison.

    Examples:
        "2.7.18" -> (2, 7, 18)
        "3.10.0" -> (3, 10, 0)
        "1.2" -> (1, 2, 0)
        "v2.5.1" -> (2, 5, 1)

    Returns:
        Tuple of integers representing the version, or (0,) if invalid
    """
    if not version_string:
        return (0,)

    # Remove common prefixes like 'v', 'version', etc.
    version_string = re.sub(r'^(v|version|ver)', '', version_string.lower().strip())

    # Extract numeric parts
    # Match patterns like "2.7.18", "3.10.0-beta", etc.
    match = re.match(r'^(\d+)(?:\.(\d+))?(?:\.(\d+))?', version_string)

    if not match:
        return (0,)

    # Convert matched groups to integers, default to 0 if not present
    parts = []
    for i in range(1, 4):  # major, minor, patch
        part = match.group(i)
        parts.append(int(part) if part else 0)

    return tuple(parts)


def compare_versions(version1: str, version2: str) -> int:
    """
    Compare two version strings.

    Returns:
        -1 if version1 < version2
         0 if version1 == version2
         1 if version1 > version2

    Examples:
        compare_versions("2.7.18", "3.0.0") -> -1
        compare_versions("3.10", "3.9.5") -> 1
        compare_versions("2.5.0", "2.5") -> 0
    """
    v1 = parse_version(version1)
    v2 = parse_version(version2)

    if v1 < v2:
        return -1
    elif v1 > v2:
        return 1
    else:
        return 0


def is_version_vulnerable(installed_version: str, safe_version_from: str) -> bool:
    """
    Check if an installed version is vulnerable based on the safe version threshold.

    Args:
        installed_version: Version currently installed (e.g., "2.4.0")
        safe_version_from: First safe version (e.g., "2.5.0")

    Returns:
        True if installed_version < safe_version_from (vulnerable)
        False otherwise (safe)

    Examples:
        is_version_vulnerable("2.4.0", "2.5.0") -> True (vulnerable)
        is_version_vulnerable("2.5.0", "2.5.0") -> False (safe, equal)
        is_version_vulnerable("2.6.0", "2.5.0") -> False (safe, newer)
    """
    if not installed_version or not safe_version_from:
        return False

    return compare_versions(installed_version, safe_version_from) < 0


def get_vulnerable_installations() -> List[Dict[str, Any]]:
    """
    Scan all installed software and find vulnerable installations.

    Returns:
        List of dicts with vulnerability information:
        {
            'asset': Asset object,
            'inventory_code': str,
            'software_name': str,
            'installed_version': str,
            'vulnerability': SoftwareVulnerability object,
            'safe_version': str,
            'severity': str,
            'cve_id': str,
        }
    """
    from .models import InstalledSoftware, SoftwareVulnerability

    vulnerable_installations = []

    # Get all installed software with versions
    installations = InstalledSoftware.objects.filter(
        version__isnull=False
    ).exclude(
        version__exact=''
    ).select_related('asset', 'software').prefetch_related(
        'software__software_vulnerabilities'
    )

    for installation in installations:
        # Check each vulnerability for this software
        for vuln in installation.software.software_vulnerabilities.all():
            if is_version_vulnerable(installation.version, vuln.safe_version_from):
                vulnerable_installations.append({
                    'asset': installation.asset,
                    'inventory_code': installation.asset.inventory_code,
                    'software_name': installation.software.name,
                    'installed_version': installation.version,
                    'vulnerability': vuln,
                    'safe_version': vuln.safe_version_from,
                    'severity': vuln.severity,
                    'cve_id': vuln.cve_id or 'N/A',
                    'title': vuln.title,
                    'description': vuln.description,
                })

    return vulnerable_installations


def generate_vulnerability_warnings():
    """
    Generate ComplianceWarning entries for all vulnerable software installations.
    This should be run periodically or when vulnerability data is updated.

    Also cleans up obsolete warnings:
    - Warnings for vulnerabilities that no longer exist (marked as FALSE_POSITIVE)
    - Warnings for software that has been updated to safe versions (marked as RESOLVED)

    Returns:
        dict: {
            'warnings_created': int - Number of new warnings created
            'warnings_cleaned': int - Number of obsolete warnings cleaned up
        }
    """
    from auditing.models import ComplianceWarning
    from .models import SoftwareVulnerability, InstalledSoftware

    # Step 1: Clean up obsolete warnings
    obsolete_warnings = ComplianceWarning.objects.filter(
        category='SOFTWARE_VULNERABLE',
        status__in=[
            ComplianceWarning.StatusChoices.NEW,
            ComplianceWarning.StatusChoices.IN_REVIEW
        ]
    )

    warnings_cleaned = 0
    for warning in obsolete_warnings:
        evidence = warning.evidence or {}
        vulnerability_id = evidence.get('vulnerability_id')

        # Check if vulnerability still exists
        if vulnerability_id:
            if not SoftwareVulnerability.objects.filter(id=vulnerability_id).exists():
                # Vulnerability was deleted, mark warning as false positive
                warning.status = ComplianceWarning.StatusChoices.FALSE_POSITIVE
                warning.resolution_notes = "Vulnerabilidad eliminada del sistema"
                warning.save()
                warnings_cleaned += 1
                continue

        # Check if software version has been updated to safe version
        software_name = evidence.get('software_name')
        installed_version = evidence.get('installed_version')
        safe_version = evidence.get('safe_version')

        if software_name and installed_version and safe_version:
            # Find current installation on this asset
            current_installation = InstalledSoftware.objects.filter(
                asset=warning.asset,
                software__name=software_name
            ).first()

            if current_installation:
                # Check if version was updated to safe version
                if not is_version_vulnerable(current_installation.version, safe_version):
                    # Software was updated, mark as resolved
                    warning.status = ComplianceWarning.StatusChoices.RESOLVED
                    warning.resolution_notes = f"Software actualizado a versión {current_installation.version}"
                    warning.save()
                    warnings_cleaned += 1

    # Step 2: Generate new warnings for current vulnerabilities
    vulnerable = get_vulnerable_installations()
    warnings_created = 0

    for vuln_data in vulnerable:
        asset = vuln_data['asset']
        vuln = vuln_data['vulnerability']

        # Check if warning already exists for this specific vulnerability
        existing = ComplianceWarning.objects.filter(
            asset=asset,
            category='SOFTWARE_VULNERABLE',
            evidence__vulnerability_id=vuln.id
        ).filter(
            status__in=[
                ComplianceWarning.StatusChoices.NEW,
                ComplianceWarning.StatusChoices.IN_REVIEW
            ]
        ).exists()

        if existing:
            continue  # Skip if already warned

        # Create warning
        description = (
            f"Se detectó software vulnerable: {vuln_data['software_name']} "
            f"versión {vuln_data['installed_version']}. "
            f"Actualizar a versión {vuln_data['safe_version']} o superior."
        )

        if vuln.cve_id:
            description += f" (CVE: {vuln.cve_id})"

        evidence = {
            'vulnerability_id': vuln.id,  # Track the vulnerability ID
            'software_name': vuln_data['software_name'],
            'installed_version': vuln_data['installed_version'],
            'safe_version': vuln_data['safe_version'],
            'severity': vuln_data['severity'],
            'cve_id': vuln_data['cve_id'],
            'vulnerability_title': vuln.title,
        }

        ComplianceWarning.objects.create(
            asset=asset,
            category='SOFTWARE_VULNERABLE',
            description=description,
            evidence=evidence,
            status=ComplianceWarning.StatusChoices.NEW
        )

        warnings_created += 1

    return {
        'warnings_created': warnings_created,
        'warnings_cleaned': warnings_cleaned
    }
