
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AssetCheckinViewSet, ComplianceWarningViewSet

router = DefaultRouter()
router.register(r'asset-checkins', AssetCheckinViewSet)
router.register(r'compliance-warnings', ComplianceWarningViewSet)

urlpatterns = [
    path('', include(router.urls)),
]