
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AssetCheckinViewSet

router = DefaultRouter()
router.register(r'asset-checkins', AssetCheckinViewSet)

urlpatterns = [
    path('', include(router.urls)),
]