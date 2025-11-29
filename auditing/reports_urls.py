"""
URL configuration for reports and analytics endpoints.
"""
from django.urls import path
from . import reports_views, analytics_views

urlpatterns = [
    # Tabular Reports
    path('employees-assets/', reports_views.employees_with_assets_report, name='report-employees-assets'),
    path('assets-specs/', reports_views.assets_by_specs_report, name='report-assets-specs'),
    path('software-installations/', reports_views.software_installations_report, name='report-software-installations'),
    path('licenses-usage/', reports_views.licenses_usage_report, name='report-licenses-usage'),
    path('warnings/', reports_views.warnings_report, name='report-warnings'),

    # Analytics / Chart Data
    path('analytics/assets-distribution/', analytics_views.assets_distribution, name='analytics-assets'),
    path('analytics/employees-distribution/', analytics_views.employees_distribution, name='analytics-employees'),
    path('analytics/warnings/', analytics_views.warnings_analytics, name='analytics-warnings'),
    path('analytics/software/', analytics_views.software_analytics, name='analytics-software'),
    path('analytics/summary/', analytics_views.summary_metrics, name='analytics-summary'),
]
