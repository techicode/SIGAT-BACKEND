import pytest
from assets.models import Asset
from users.models import Department, Employee, CustomUser
from ..models import AssetCheckin, ComplianceWarning


@pytest.mark.django_db
def test_asset_checkin_creation():
    """test an asset check in"""

    dept = Department.objects.create(name="Dept. Auditoría")
    employee = Employee.objects.create(
        rut="33.333.333-3", first_name="Auditor", last_name="Test"
    )
    asset = Asset.objects.create(inventory_code="AUDIT-001", department=dept)

    checkin = AssetCheckin.objects.create(
        asset=asset,
        employee=employee,
        physical_state="Bueno",
        notes="El equipo funciona correctamente.",
    )

    assert checkin.asset == asset
    assert checkin.employee == employee
    assert checkin.physical_state == "Bueno"
    assert "AUDIT-001" in str(checkin)
    assert "Auditor Test" in str(checkin)


@pytest.mark.django_db
def test_compliance_warning_creation_and_resolution():
    """test the creation of a warning and his resolution"""

    dept = Department.objects.create(name="Dept. Cumplimiento")
    asset = Asset.objects.create(inventory_code="COMP-001", department=dept)
    resolver_user = CustomUser.objects.create_user(username="resolver1", password="pw")

    warning = ComplianceWarning.objects.create(
        asset=asset,
        category="SOFTWARE_NO_LICENCIADO",
        description="WinRAR instalado sin licencia.",
    )

    assert warning.asset == asset
    assert warning.status == ComplianceWarning.StatusChoices.NEW
    assert warning.resolved_by is None
    assert "COMP-001" in str(warning)

    warning.status = ComplianceWarning.StatusChoices.RESOLVED
    warning.resolved_by = resolver_user
    warning.resolution_notes = "Software desinstalado."
    warning.save()

    updated_warning = ComplianceWarning.objects.get(id=warning.id)
    assert updated_warning.status == "RESUELTA"
    assert updated_warning.resolved_by == resolver_user
    assert updated_warning.resolution_notes == "Software desinstalado."
