import pytest
from django.db import IntegrityError
from assets.models import Asset
from users.models import Department
from ..models import Vulnerability, SoftwareCatalog, License, InstalledSoftware


@pytest.mark.django_db
def test_vulnerability_creation_and_str():
    """test vulnerability and the string"""
    vuln = Vulnerability.objects.create(
        cve_id="CVE-2024-12345",
        description="Una vulnerabilidad de prueba",
        severity="Alta",
    )
    assert vuln.cve_id == "CVE-2024-12345"
    assert str(vuln) == "CVE-2024-12345"


@pytest.mark.django_db
def test_vulnerability_cve_id_is_unique():
    """test cve id to be unique"""
    Vulnerability.objects.create(cve_id="CVE-2024-UNIQUE")
    with pytest.raises(IntegrityError):
        Vulnerability.objects.create(cve_id="CVE-2024-UNIQUE")


@pytest.mark.django_db
def test_software_catalog_creation_with_vulnerability():
    """test create a software and relation with vulnerability."""
    vuln = Vulnerability.objects.create(cve_id="CVE-2024-007")
    software = SoftwareCatalog.objects.create(name="SecureWare", developer="TestDev")
    software.vulnerabilities.add(vuln)
    assert software.name == "SecureWare"
    assert software.vulnerabilities.count() == 1
    assert str(software) == "SecureWare (TestDev)"


@pytest.mark.django_db
def test_software_catalog_unique_together_constraint():
    """test software unique"""
    SoftwareCatalog.objects.create(name="Office Suite", developer="MegaCorp")

    with pytest.raises(IntegrityError):
        SoftwareCatalog.objects.create(name="Office Suite", developer="MegaCorp")


@pytest.mark.django_db
def test_software_catalog_allows_different_combinations():
    """test software with different name combinations"""
    SoftwareCatalog.objects.create(name="Office Suite", developer="MegaCorp")
    SoftwareCatalog.objects.create(name="Office Suite", developer="MiniCorp")
    SoftwareCatalog.objects.create(name="Graphics Suite", developer="MegaCorp")
    assert SoftwareCatalog.objects.count() == 3


@pytest.mark.django_db
def test_license_creation():
    """test the licence and asignation wiyh a software"""
    software = SoftwareCatalog.objects.create(
        name="DataMiner", developer="Analytics Inc."
    )
    license = License.objects.create(
        software=software, license_key="ABCD-1234-EFGH-5678", quantity=10
    )

    assert license.software == software
    assert license.quantity == 10
    assert "DataMiner" in str(license)


@pytest.mark.django_db
def test_installed_software_creation_with_license():
    """the create software with licence included"""
    dept = Department.objects.create(name="Departamento de I&D")
    asset = Asset.objects.create(inventory_code="PC-01", department=dept)
    software = SoftwareCatalog.objects.create(name="CAD Pro", developer="EngSoft")
    lic = License.objects.create(software=software, license_key="LIC-01")

    installed = InstalledSoftware.objects.create(
        asset=asset, software=software, license=lic, version="2.0"
    )
    assert installed.asset == asset
    assert installed.software == software
    assert installed.license == lic
    assert str(installed) == "CAD Pro en PC-01"


@pytest.mark.django_db
def test_installed_software_creation_without_license():
    """test software creation without a licence (like freeware software)"""
    dept = Department.objects.create(name="Departamento de Comunicaciones")
    asset = Asset.objects.create(inventory_code="PC-02", department=dept)
    software = SoftwareCatalog.objects.create(name="OpenBrowser", developer="Community")

    installed = InstalledSoftware.objects.create(asset=asset, software=software)
    assert installed.license is None


@pytest.mark.django_db
def test_installed_software_unique_together_constraint():
    """test that a software cant be installed in many assets"""
    dept = Department.objects.create(name="Departamento de Operaciones")
    asset = Asset.objects.create(inventory_code="PC-03", department=dept)
    software = SoftwareCatalog.objects.create(
        name="UtilityTool", developer="Tools Inc."
    )

    InstalledSoftware.objects.create(asset=asset, software=software)
    with pytest.raises(IntegrityError):
        InstalledSoftware.objects.create(asset=asset, software=software)
