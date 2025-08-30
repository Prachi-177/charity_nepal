from django.contrib import admin
from django.db.models import Count, Sum
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_POST

from cases.models import CharityCase
from donations.models import Donation
from users.models import User


class CharityNepalAdminSite(admin.AdminSite):
    """Custom admin site for CharityNepal"""

    site_header = "CharityNepal Administration"
    site_title = "CharityNepal Admin"
    index_title = "Welcome to CharityNepal Administration"

    def get_app_list(self, request):
        """Return a sorted list of all the installed apps that have been registered with the admin site."""
        app_list = super().get_app_list(request)

        # Add dashboard link as first item
        dashboard_app = {
            "name": "Dashboard",
            "app_label": "dashboard",
            "app_url": "/admin/dashboard/",
            "has_module_perms": True,
            "models": [
                {
                    "name": "Analytics Dashboard",
                    "object_name": "Dashboard",
                    "admin_url": "/admin/dashboard/",
                    "add_url": None,
                    "view_only": True,
                }
            ],
        }

        # Custom ordering of apps
        app_order = {
            "Dashboard": 0,
            "Users": 1,
            "Cases": 2,
            "Donations": 3,
            "Payments": 4,
            "Recommendations": 5,
        }

        # Add dashboard to beginning
        app_list.insert(0, dashboard_app)

        # Sort apps by custom order
        app_list.sort(key=lambda x: app_order.get(x.get("name", ""), 999))

        return app_list

    def index(self, request, extra_context=None):
        """Custom admin index with dashboard widgets"""
        extra_context = extra_context or {}

        # Quick stats for the index page
        stats = {
            "total_users": User.objects.count(),
            "total_cases": CharityCase.objects.count(),
            "approved_cases": CharityCase.objects.filter(
                verification_status="approved"
            ).count(),
            "pending_cases": CharityCase.objects.filter(
                verification_status="pending"
            ).count(),
            "total_raised": Donation.objects.filter(status="completed").aggregate(
                total=Sum("amount")
            )["total"]
            or 0,
            "recent_donations": Donation.objects.filter(status="completed").count(),
        }

        extra_context.update(
            {
                "dashboard_stats": stats,
                "dashboard_url": "/admin/dashboard/",
            }
        )

        return super().index(request, extra_context)

    def get_urls(self):
        """Add custom URLs to the admin site"""
        urls = super().get_urls()
        custom_urls = [
            path("toggle-sidebar/", self.toggle_sidebar_view, name="toggle_sidebar"),
            path("search/", self.search_view, name="search"),
        ]
        return custom_urls + urls

    @require_POST
    def toggle_sidebar_view(self, request):
        """Toggle sidebar view for Django Unfold compatibility"""
        return JsonResponse({"status": "success", "message": "Sidebar toggled"})

    def search_view(self, request):
        """Search view for Django Unfold compatibility"""
        query = request.GET.get("q", "")
        # Simple search implementation - you can enhance this
        results = []
        if query:
            # Search across models - simplified example
            from django.apps import apps

            for model in apps.get_models():
                if hasattr(model, "_meta") and model._meta.app_label in [
                    "users",
                    "cases",
                    "donations",
                ]:
                    # Add basic search logic here if needed
                    pass

        return JsonResponse({"results": results, "query": query, "status": "success"})


def dashboard_callback(request, context):
    """Custom dashboard callback for Unfold admin"""

    # Basic statistics
    total_users = User.objects.count()
    total_cases = CharityCase.objects.count()
    approved_cases = CharityCase.objects.filter(verification_status="approved").count()
    pending_cases = CharityCase.objects.filter(verification_status="pending").count()

    total_donations = Donation.objects.filter(status="completed").aggregate(
        count=Count("id"), total=Sum("amount")
    )

    # Recent activity
    recent_cases = CharityCase.objects.select_related("created_by").order_by(
        "-created_at"
    )[:5]
    recent_donations = (
        Donation.objects.select_related("donor", "case")
        .filter(status="completed")
        .order_by("-created_at")[:5]
    )

    # Top categories
    category_stats = (
        CharityCase.objects.filter(verification_status="approved")
        .values("category")
        .annotate(
            count=Count("id"),
            total_target=Sum("target_amount"),
            total_collected=Sum("collected_amount"),
        )
        .order_by("-count")[:5]
    )

    # Dashboard context
    dashboard_context = {
        "total_users": total_users,
        "total_cases": total_cases,
        "approved_cases": approved_cases,
        "pending_cases": pending_cases,
        "total_donations_count": total_donations["count"] or 0,
        "total_donations_amount": total_donations["total"] or 0,
        "recent_cases": recent_cases,
        "recent_donations": recent_donations,
        "category_stats": category_stats,
    }

    context.update(dashboard_context)
    return context


# Create custom admin site instance
admin_site = CharityNepalAdminSite(name="charity_admin")
