import pytest
from rest_framework.test import APIClient
from assets.models import Asset
from users.models import Department, CustomUser
from ..models import SoftwareCatalog, InstalledSoftware, License


@pytest.fixture
def api_client():
    """fixture that return api client"""
    return APIClient()


@pytest.fixture
def technician_user():
    """fixture that creates a technician user"""
    return CustomUser.objects.create_user(
        username="tech_software", password="pw", role=CustomUser.RoleChoices.TECHNICIAN
    )


@pytest.fixture
def admin_user():
    """fixture that creates an admin user"""
    return CustomUser.objects.create_user(
        username="admin_software", password="pw", role=CustomUser.RoleChoices.ADMIN
    )


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
    license = License.objects.create(
        software=software, license_key="ABCD-1234-EFGH-5678"
    )
    return {"asset": asset, "software": software, "license": license}


@pytest.mark.django_db
def test_list_software_catalog(api_client, technician_user):
    """test to list catalog of software"""
    SoftwareCatalog.objects.create(name="Software 1", developer="Dev A")
    SoftwareCatalog.objects.create(name="Software 2", developer="Dev B")

    api_client.force_authenticate(user=technician_user)
    response = api_client.get("/api/software-catalog/")

    assert response.status_code == 200
    assert len(response.data['results']) == 2


@pytest.mark.django_db
def test_create_software_catalog(api_client, technician_user):
    """test new software"""
    api_client.force_authenticate(user=technician_user)
    data = {"name": "Nuevo Software", "developer": "Nuevo Desarrollador"}
    response = api_client.post("/api/software-catalog/", data=data)

    assert response.status_code == 201
    assert SoftwareCatalog.objects.count() == 1
    assert SoftwareCatalog.objects.get().name == "Nuevo Software"


@pytest.mark.django_db
def test_list_installed_software(api_client, technician_user, setup_asset_and_software):
    """test to list installed software"""
    asset = setup_asset_and_software["asset"]
    software = setup_asset_and_software["software"]
    InstalledSoftware.objects.create(asset=asset, software=software, version="1.0")

    api_client.force_authenticate(user=technician_user)
    response = api_client.get("/api/installed-software/")

    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]["asset"]["inventory_code"] == "API-TEST-001"


@pytest.mark.django_db
def test_create_installed_software(
    api_client, technician_user, setup_asset_and_software
):
    """test software installed in a asset"""
    asset = setup_asset_and_software["asset"]
    software = setup_asset_and_software["software"]

    api_client.force_authenticate(user=technician_user)
    data = {
        "asset_id": asset.id,
        "software_id": software.id,
        "version": "2.1 beta",
    }
    response = api_client.post("/api/installed-software/", data=data, format="json")

    assert response.status_code == 201
    assert InstalledSoftware.objects.count() == 1


@pytest.mark.django_db
def test_technician_sees_obfuscated_license_key(
    api_client, technician_user, setup_asset_and_software
):
    """test that a technician sees an obfuscated license key"""
    license_id = setup_asset_and_software["license"].id
    api_client.force_authenticate(user=technician_user)
    response = api_client.get(f"/api/licenses/{license_id}/")
    assert response.status_code == 200
    assert response.data["license_key_display"] == "****-****-****-5678"
    assert "license_key" not in response.data


@pytest.mark.django_db
def test_admin_sees_full_license_key(api_client, admin_user, setup_asset_and_software):
    """test that an admin sees the full license key"""
    license_id = setup_asset_and_software["license"].id
    api_client.force_authenticate(user=admin_user)
    response = api_client.get(f"/api/licenses/{license_id}/")
    assert response.status_code == 200
    assert response.data["license_key_display"] == "ABCD-1234-EFGH-5678"


@pytest.mark.django_db
def test_technician_cannot_create_license(
    api_client, technician_user, setup_asset_and_software
):
    """test that a technician cannot create a license"""
    software = setup_asset_and_software["software"]
    api_client.force_authenticate(user=technician_user)
    data = {"software_id": software.id, "license_key": "NEW-KEY"}
    response = api_client.post("/api/licenses/", data=data, format="json")
    assert response.status_code == 403
