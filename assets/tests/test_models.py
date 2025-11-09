import pytest
from django.db import IntegrityError
from users.models import Department, Employee
from assets.models import Asset, ComputerDetail, StorageDevice, GraphicsCard


@pytest.fixture
def setup_dependencies():
    """create a deparment and employee"""
    dept = Department.objects.create(name="Departamento de Activos")
    employee = Employee.objects.create(
        rut="55.555.555-5", first_name="Asset", last_name="Holder"
    )
    return {"department": dept, "employee": employee}


@pytest.mark.django_db
def test_asset_creation(setup_dependencies):
    """create an asset and relations with deparment and employee"""
    dept = setup_dependencies["department"]
    employee = setup_dependencies["employee"]

    asset = Asset.objects.create(
        inventory_code="ASSET-001",
        serial_number="SN-ASSET-001",
        asset_type=Asset.AssetTypeChoices.NOTEBOOK,
        department=dept,
        employee=employee,
        brand="Dell",
    )

    assert asset.inventory_code == "ASSET-001"
    assert asset.department.name == "Departamento de Activos"
    assert asset.employee.first_name == "Asset"
    assert "ASSET-001" in str(asset)
    assert "Notebook" in str(asset)


@pytest.mark.django_db
def test_asset_inventory_code_is_unique(setup_dependencies):
    """test unique invetory code"""
    dept = setup_dependencies["department"]
    Asset.objects.create(
        inventory_code="UNIQUE-01", serial_number="SN-UNIQUE-01", department=dept
    )

    with pytest.raises(IntegrityError):
        Asset.objects.create(
            inventory_code="UNIQUE-01", serial_number="SN-OTHER-01", department=dept
        )


@pytest.mark.django_db
def test_asset_serial_number_is_unique(setup_dependencies):
    """test unique serial code"""
    dept = setup_dependencies["department"]
    Asset.objects.create(
        inventory_code="UNIQUE-02", serial_number="SN-UNIQUE-02", department=dept
    )

    with pytest.raises(IntegrityError):
        Asset.objects.create(
            inventory_code="OTHER-02", serial_number="SN-UNIQUE-02", department=dept
        )


@pytest.mark.django_db
def test_computer_detail_creation(setup_dependencies):
    """test relation of asset and details"""
    dept = setup_dependencies["department"]
    asset = Asset.objects.create(inventory_code="PC-DETAIL-01", department=dept)

    detail = ComputerDetail.objects.create(
        asset=asset, os_name="Windows 11", cpu_model="Intel Core i5", ram_gb=16
    )

    assert asset.computerdetail == detail
    assert detail.os_name == "Windows 11"
    assert "PC-DETAIL-01" in str(detail)


@pytest.mark.django_db
def test_multiple_storage_devices_for_asset(setup_dependencies):
    """test asset with multiple storage devices"""
    dept = setup_dependencies["department"]
    asset = Asset.objects.create(inventory_code="STORAGE-PC-01", department=dept)

    StorageDevice.objects.create(asset=asset, model="SSD NVMe 1TB")
    StorageDevice.objects.create(asset=asset, model="HDD SATA 2TB")

    assert asset.storage_devices.count() == 2

    models = list(asset.storage_devices.values_list("model", flat=True))
    assert "SSD NVMe 1TB" in models
    assert "HDD SATA 2TB" in models


@pytest.mark.django_db
def test_graphics_card_creation(setup_dependencies):
    """test gpu creation asigned to a asset"""
    dept = setup_dependencies["department"]
    asset = Asset.objects.create(inventory_code="GPU-PC-01", department=dept)

    GraphicsCard.objects.create(asset=asset, model_name="NVIDIA RTX 3060")

    assert asset.graphics_cards.count() == 1
    assert asset.graphics_cards.first().model_name == "NVIDIA RTX 3060"
