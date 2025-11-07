from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SoftwareCatalogViewSet

router = DefaultRouter()

router.register(r"software-catalog", SoftwareCatalogViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
