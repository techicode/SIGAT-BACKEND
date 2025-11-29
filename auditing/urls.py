from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AssetCheckinViewSet,
    ComplianceWarningViewSet,
    AuditLogViewSet,
    dashboard_stats,
    hardware_obsolescence_rules,
    obsolete_assets_list
)

router = DefaultRouter()
router.register(r"asset-checkins", AssetCheckinViewSet)
router.register(r"compliance-warnings", ComplianceWarningViewSet)
router.register(r"audit-logs", AuditLogViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("dashboard/stats/", dashboard_stats, name="dashboard-stats"),
    path("hardware-obsolescence/rules/", hardware_obsolescence_rules, name="hardware-obsolescence-rules"),
    path("hardware-obsolescence/assets/", obsolete_assets_list, name="obsolete-assets-list"),
]
