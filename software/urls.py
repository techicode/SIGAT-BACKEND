from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SoftwareCatalogViewSet, InstalledSoftwareViewSet

router = DefaultRouter()

router.register(r"software-catalog", SoftwareCatalogViewSet)
router.register(r"installed-software", InstalledSoftwareViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
