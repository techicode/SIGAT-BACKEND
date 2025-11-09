import pytest
from rest_framework.test import APIClient
from assets.models import Asset
from users.models import Department, Employee, CustomUser
from ..models import ComplianceWarning


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def technician_user():
    """fixture that creates a technician user"""
    return CustomUser.objects.create_user(
        username="tech_audit", password="pw", role=CustomUser.RoleChoices.TECHNICIAN
    )


@pytest.fixture
def setup_auditing_data():
    """test setup for deparment and employee"""
    dept = Department.objects.create(name="Dept. para API Audit")
    employee = Employee.objects.create(
        rut="44.444.444-4", first_name="ApiUser", last_name="Audit"
    )
    asset = Asset.objects.create(
        inventory_code="API-AUDIT-001", department=dept, employee=employee
    )
    return {"asset": asset, "employee": employee}


@pytest.mark.django_db
def test_create_asset_checkin_unauthenticated_fails(api_client):
    """test that unauthenticated users cannot create checkins"""
    response = api_client.post("/api/asset-checkins/", data={})
    assert response.status_code == 401


@pytest.mark.django_db
def test_create_asset_checkin_as_technician(
    api_client, technician_user, setup_auditing_data
):
    """test asset checkin via POST"""
    asset = setup_auditing_data["asset"]
    employee = setup_auditing_data["employee"]

    api_client.force_authenticate(user=technician_user)
    data = {
        "asset_id": asset.id,
        "employee_id": employee.id,
        "physical_state": "Excelente",
        "notes": "Realizado durante la prueba de API.",
    }
    response = api_client.post("/api/asset-checkins/", data=data)

    assert response.status_code == 201
    assert response.data["physical_state"] == "Excelente"
    assert response.data["asset"]["inventory_code"] == "API-AUDIT-001"
    assert response.data["employee"]["full_name"] == "ApiUser Audit"


@pytest.mark.django_db
def test_create_compliance_warning_as_technician(
    api_client, technician_user, setup_auditing_data
):
    """test create compliance warning (via sigat agente)"""
    asset = setup_auditing_data["asset"]

    api_client.force_authenticate(user=technician_user)
    data = {
        "asset_id": asset.id,
        "category": "LICENSING_VIOLATION",
        "description": "Agente detectó software sin licencia.",
        "evidence": {"file": "C:/Games/game.exe"},
    }

    response = api_client.post("/api/compliance-warnings/", data=data, format="json")

    assert response.status_code == 201
    assert response.data["category"] == "LICENSING_VIOLATION"
    assert response.data["status"] == "NUEVA"
    assert response.data["resolved_by"] is None


@pytest.mark.django_db
def test_resolve_compliance_warning_assigns_user(
    api_client, technician_user, setup_auditing_data
):
    """test that updating a warning automatically assigns the resolver"""
    asset = setup_auditing_data["asset"]
    warning = ComplianceWarning.objects.create(
        asset=asset, category="TEST", description="test desc"
    )

    api_client.force_authenticate(user=technician_user)
    update_data = {
        "status": ComplianceWarning.StatusChoices.RESOLVED,
        "resolution_notes": "Problema resuelto por el técnico.",
    }
    response = api_client.patch(
        f"/api/compliance-warnings/{warning.id}/", data=update_data, format="json"
    )

    assert response.status_code == 200

    warning.refresh_from_db()
    assert warning.status == "RESUELTA"
    assert warning.resolved_by == technician_user
    assert warning.resolution_notes == "Problema resuelto por el técnico."
