from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Count
from django.utils.html import format_html

from charity_backend.admin import admin_site

from .models import User


class UserAdmin(BaseUserAdmin):
    """Admin configuration for custom User model"""

    list_display = (
        "email",
        "full_name_display",
        "role_badge",
        "verification_status",
        "is_active",
        "donations_count",
        "created_at",
    )
    list_filter = (
        "role",
        "is_verified",
        "is_active",
        "is_staff",
        "is_superuser",
        "created_at",
    )
    search_fields = ("email", "username", "first_name", "last_name", "phone")
    ordering = ("-created_at",)
    list_per_page = 25

    fieldsets = (
        (
            "Account Information",
            {
                "fields": ("email", "username", "password"),
            },
        ),
        (
            "Personal Information",
            {
                "fields": ("first_name", "last_name", "phone", "address"),
            },
        ),
        (
            "Permissions & Role",
            {
                "fields": (
                    "role",
                    "is_verified",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
        (
            "Groups & Permissions",
            {
                "fields": ("groups", "user_permissions"),
                "classes": ("collapse",),
            },
        ),
        (
            "Important Dates",
            {
                "fields": ("last_login", "date_joined", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    add_fieldsets = (
        (
            "Create New User",
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "username",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                    "role",
                ),
            },
        ),
    )

    readonly_fields = ("created_at", "updated_at", "last_login", "date_joined")

    actions = ["mark_verified", "mark_unverified", "make_donors", "make_admins"]

    def get_queryset(self, request):
        """Optimize queryset with related data"""
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(donations_count=Count("donations", distinct=True))
        return queryset

    def full_name_display(self, obj):
        """Display user's full name with username fallback"""
        full_name = f"{obj.first_name} {obj.last_name}".strip()
        if not full_name:
            full_name = obj.username
        return format_html(
            '<strong>{}</strong><br><small class="text-muted">{}</small>',
            full_name,
            obj.email,
        )

    full_name_display.short_description = "Name"

    def role_badge(self, obj):
        """Display role with colored badge"""
        colors = {
            "admin": "#dc3545",  # Red
            "donor": "#28a745",  # Green
        }
        color = colors.get(obj.role, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_role_display().upper(),
        )

    role_badge.short_description = "Role"

    def verification_status(self, obj):
        """Display verification status with icon"""
        if obj.is_verified:
            return format_html('<span style="color: #28a745;">✅ Verified</span>')
        return format_html('<span style="color: #dc3545;">❌ Not Verified</span>')

    verification_status.short_description = "Verification"

    def donations_count(self, obj):
        """Display donation count"""
        count = getattr(obj, "donations_count", 0)
        if count > 0:
            return format_html(
                '<span style="font-weight: bold; color: #007bff;">{}</span>', count
            )
        return "0"

    donations_count.short_description = "Donations"

    # Admin Actions
    def mark_verified(self, request, queryset):
        """Mark selected users as verified"""
        count = queryset.update(is_verified=True)
        self.message_user(request, f"✅ {count} users marked as verified.")

    mark_verified.short_description = "Mark selected users as verified"

    def mark_unverified(self, request, queryset):
        """Mark selected users as unverified"""
        count = queryset.update(is_verified=False)
        self.message_user(request, f"❌ {count} users marked as unverified.")

    mark_unverified.short_description = "Mark selected users as unverified"

    def make_donors(self, request, queryset):
        """Change role to donor"""
        count = queryset.update(role="donor", is_staff=False)
        self.message_user(request, f"👤 {count} users changed to donors.")

    make_donors.short_description = "Change role to donor"

    def make_admins(self, request, queryset):
        """Change role to admin"""
        count = queryset.update(role="admin", is_staff=True)
        self.message_user(request, f"👨‍💼 {count} users changed to admins.")

    make_admins.short_description = "Change role to admin"


# Register with custom admin site
admin_site.register(User, UserAdmin)
