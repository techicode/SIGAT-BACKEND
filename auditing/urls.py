from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AssetCheckinViewSet,
    ComplianceWarningViewSet,
    AuditLogViewSet,
    dashboard_stats,
    hardware_obsolescence_rules,
    obsolete_assets_list,
    checkin_by_token,
    submit_checkin,
    agent_hardware_report,
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
    # Public check-in endpoints (no authentication required)
    path("checkin/<str:token>/", checkin_by_token, name="checkin-by-token"),
    path("checkin/<str:token>/submit/", submit_checkin, name="submit-checkin"),
    # Agent hardware report endpoint (no authentication required for MVP)
    path("agent/hardware-report/", agent_hardware_report, name="agent-hardware-report"),
]
