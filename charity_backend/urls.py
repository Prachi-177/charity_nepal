"""
URL configuration for charity_backend project.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

from cases.views import HomeView
from recommendations.ml_analytics import (
    MLAnalyticsView,
    algorithm_comparison,
    ml_analytics_api,
    user_segmentation_analysis,
)

from .admin import admin_site
from .dashboard_views import DashboardView, case_analytics, dashboard_api

# Admin site customization
admin.site.site_header = "Charity Management System"
admin.site.site_title = "Charity Admin"
admin.site.index_title = "Welcome to Charity Management System"

urlpatterns = [
    path("admin/dashboard/", DashboardView.as_view(), name="admin_dashboard"),
    path("admin/dashboard/api/", dashboard_api, name="admin_dashboard_api"),
    path(
        "admin/dashboard/case/<int:case_id>/",
        case_analytics,
        name="admin_case_analytics",
    ),
    path("admin/ml-analytics/", MLAnalyticsView.as_view(), name="admin_ml_analytics"),
    path("admin/ml-analytics/api/", ml_analytics_api, name="admin_ml_analytics_api"),
    path(
        "admin/ml-analytics/algorithm-comparison/",
        algorithm_comparison,
        name="admin_algorithm_comparison",
    ),
    path(
        "admin/ml-analytics/user-segmentation/",
        user_segmentation_analysis,
        name="admin_user_segmentation",
    ),
    path("admin/", admin_site.urls),
    path("", include("users.urls")),
    path("", include("cases.urls")),
    path("donations/", include("donations.urls")),
    path("payments/", include("payments.urls")),
    path("recommendations/", include("recommendations.urls")),
    # Home page with ML-powered dynamic content
    path("", HomeView.as_view(), name="home"),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # Add django-browser-reload for development
    urlpatterns.append(path("__reload__/", include("django_browser_reload.urls")))
