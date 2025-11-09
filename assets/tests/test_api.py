import pytest
from rest_framework.test import APIClient
from users.models import Department, Employee
from assets.models import Asset


@pytest.fixture
def setup_data():
    """
    test user and deparment
    """
    department = Department.objects.create(name="Departamento de Prueba")
    employee = Employee.objects.create(
        rut="12.345.678-9",
        first_name="Usuario",
        last_name="DePrueba",
        email="test@upla.cl",
        department=department,
    )
    return {"department": department, "employee": employee}


@pytest.mark.django_db
def test_list_assets(setup_data):
    """
    test list assets and check if the response is "short"
    """

    department = setup_data["department"]
    employee = setup_data["employee"]
    Asset.objects.create(
        inventory_code="TEST-001",
        serial_number="SN001",
        asset_type=Asset.AssetTypeChoices.NOTEBOOK,
        status=Asset.StatusChoices.ASSIGNED,
        department=department,
        employee=employee,
    )

    client = APIClient()
    response = client.get("/api/assets/")

    assert response.status_code == 200
    assert len(response.data) == 1

    asset_data = response.data[0]
    assert asset_data["inventory_code"] == "TEST-001"
    assert asset_data["employee"]["full_name"] == "Usuario DePrueba"
    assert "serial_number" not in asset_data


@pytest.mark.django_db
def test_retrieve_asset(setup_data):
    """
    test asset detailled
    """
    department = setup_data["department"]
    asset = Asset.objects.create(
        inventory_code="TEST-002",
        serial_number="SN002",
        asset_type=Asset.AssetTypeChoices.DESKTOP,
        department=department,
    )

    client = APIClient()
    response = client.get(f"/api/assets/{asset.inventory_code}/")

    assert response.status_code == 200

    assert response.data["inventory_code"] == "TEST-002"
    assert response.data["serial_number"] == "SN002"


@pytest.mark.django_db
def test_create_asset(setup_data):
    """
    test create asset via POST
    """
    department = setup_data["department"]
    employee = setup_data["employee"]

    client = APIClient()
    asset_data = {
        "inventory_code": "TEST-003",
        "serial_number": "SN003",
        "asset_type": "NOTEBOOK",
        "status": "BODEGA",
        "brand": "HP",
        "model": "EliteBook",
        "department_id": department.id,
        "employee_id": employee.id,
    }

    response = client.post("/api/assets/", data=asset_data)

    assert response.status_code == 201
    assert Asset.objects.count() == 1

    new_asset = Asset.objects.get()
    assert new_asset.inventory_code == "TEST-003"
    assert new_asset.employee.id == employee.id
