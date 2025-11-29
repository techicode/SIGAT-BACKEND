from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SoftwareCatalogViewSet,
    InstalledSoftwareViewSet,
    LicenseViewSet,
    SoftwareVulnerabilityViewSet,
    scan_vulnerabilities,
    vulnerable_assets_list
)

router = DefaultRouter()

router.register(r"software-catalog", SoftwareCatalogViewSet)
router.register(r"installed-software", InstalledSoftwareViewSet)
router.register(r"licenses", LicenseViewSet)
router.register(r"vulnerabilities", SoftwareVulnerabilityViewSet)

urlpatterns = [
    # Specific paths MUST come before router.urls to avoid conflicts
    path("vulnerabilities/scan/", scan_vulnerabilities, name="scan-vulnerabilities"),
    path("vulnerabilities/assets/", vulnerable_assets_list, name="vulnerable-assets-list"),
    path("", include(router.urls)),
]
