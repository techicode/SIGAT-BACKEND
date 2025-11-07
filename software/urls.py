from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SoftwareCatalogViewSet, InstalledSoftwareViewSet, LicenseViewSet

router = DefaultRouter()

router.register(r"software-catalog", SoftwareCatalogViewSet)
router.register(r"installed-software", InstalledSoftwareViewSet)
router.register(r"licenses", LicenseViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
