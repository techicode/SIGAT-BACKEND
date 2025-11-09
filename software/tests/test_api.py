import pytest
from rest_framework.test import APIClient
from assets.models import Asset
from users.models import Department
from ..models import SoftwareCatalog, InstalledSoftware


@pytest.fixture
def api_client():
    """fixture that return api client"""
    return APIClient()


@pytest.fixture
def setup_asset_and_software():
    """
    create a deparment, an asset and a software for tests
    """
    dept = Department.objects.create(name="Departamento para API Test")
    asset = Asset.objects.create(inventory_code="API-TEST-001", department=dept)
    software = SoftwareCatalog.objects.create(
        name="Software de Prueba API", developer="Dev API"
    )
    return {"asset": asset, "software": software}


@pytest.mark.django_db
def test_list_software_catalog(api_client):
    """test to list catalog of software"""
    SoftwareCatalog.objects.create(name="Software 1", developer="Dev A")
    SoftwareCatalog.objects.create(name="Software 2", developer="Dev B")

    response = api_client.get("/api/software-catalog/")

    assert response.status_code == 200
    assert len(response.data) == 2


@pytest.mark.django_db
def test_create_software_catalog(api_client):
    """test new software"""
    data = {"name": "Nuevo Software", "developer": "Nuevo Desarrollador"}
    response = api_client.post("/api/software-catalog/", data=data)

    assert response.status_code == 201
    assert SoftwareCatalog.objects.count() == 1
    assert SoftwareCatalog.objects.get().name == "Nuevo Software"


@pytest.mark.django_db
def test_list_installed_software(api_client, setup_asset_and_software):
    """test to list installed software"""

    asset = setup_asset_and_software["asset"]
    software = setup_asset_and_software["software"]
    InstalledSoftware.objects.create(asset=asset, software=software, version="1.0")

    response = api_client.get("/api/installed-software/")

    assert response.status_code == 200
    assert len(response.data) == 1

    installed_data = response.data[0]
    assert installed_data["asset"]["inventory_code"] == "API-TEST-001"
    assert installed_data["software"]["name"] == "Software de Prueba API"
    assert installed_data["version"] == "1.0"


@pytest.mark.django_db
def test_create_installed_software(api_client, setup_asset_and_software):
    """test software installed in a asset"""
    asset = setup_asset_and_software["asset"]
    software = setup_asset_and_software["software"]

    data = {
        "asset_id": asset.inventory_code,
        "software_id": software.id,
        "version": "2.1 beta",
    }
    response = api_client.post("/api/installed-software/", data=data)

    assert response.status_code == 201
    assert InstalledSoftware.objects.count() == 1

    new_install = InstalledSoftware.objects.get()
    assert new_install.asset == asset
    assert new_install.software == software
    assert new_install.version == "2.1 beta"
