from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AssetCheckinViewSet, ComplianceWarningViewSet, dashboard_stats

router = DefaultRouter()
router.register(r"asset-checkins", AssetCheckinViewSet)
router.register(r"compliance-warnings", ComplianceWarningViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("dashboard/stats/", dashboard_stats, name="dashboard-stats"),
]
