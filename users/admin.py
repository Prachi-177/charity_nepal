from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from unfold.admin import ModelAdmin
from unfold.decorators import display

from charity_backend.admin import admin_site

from .models import User


class UserAdmin(BaseUserAdmin, ModelAdmin):
    """Admin configuration for custom User model with Unfold theme"""

    # Unfold specific settings
    compressed_fields = True
    list_select_related = True
    warn_unsaved_form = True

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
        ("created_at", admin.DateFieldListFilter),
    )
    search_fields = ("email", "username", "first_name", "last_name", "phone")
    ordering = ("-created_at",)
    list_per_page = 25

    fieldsets = (
        (
            "Account Information",
            {"fields": ("email", "username", "password"), "classes": ("tab",)},
        ),
        (
            "Personal Information",
            {
                "fields": ("first_name", "last_name", "phone", "address"),
                "classes": ("tab",),
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "role",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "is_verified",
                ),
                "classes": ("tab",),
            },
        ),
        (
            "Groups & Permissions",
            {"fields": ("groups", "user_permissions"), "classes": ("tab", "collapse")},
        ),
        (
            "Timestamps",
            {
                "fields": ("last_login", "date_joined", "created_at", "updated_at"),
                "classes": ("tab", "collapse"),
            },
        ),
    )

    readonly_fields = ("created_at", "updated_at", "last_login", "date_joined")

    # Add fields for creating new users
    add_fieldsets = (
        (
            "Account Information",
            {
                "fields": ("email", "username", "password1", "password2"),
                "classes": ("tab",),
            },
        ),
        (
            "Personal Information",
            {
                "fields": ("first_name", "last_name", "phone", "address"),
                "classes": ("tab",),
            },
        ),
        (
            "Permissions",
            {
                "fields": ("role", "is_staff", "is_superuser", "is_verified"),
                "classes": ("tab",),
            },
        ),
    )

    actions = ["verify_users", "unverify_users", "make_donors", "make_admins"]

    @display(description="Full Name", ordering="first_name")
    def full_name_display(self, obj):
        """Display full name with avatar placeholder"""
        full_name = f"{obj.first_name} {obj.last_name}".strip()
        if not full_name:
            full_name = obj.username

        # Create initials for avatar
        initials = "".join([name[0].upper() for name in full_name.split()[:2]])

        return format_html(
            '<div class="flex items-center space-x-3">'
            '<div class="w-8 h-8 bg-green-100 text-green-800 rounded-full flex items-center justify-center text-sm font-semibold">'
            "{}"
            "</div>"
            '<span class="font-medium">{}</span>'
            "</div>",
            initials,
            full_name,
        )

    @display(description="Role", ordering="role")
    def role_badge(self, obj):
        """Display role with colored badge"""
        colors = {
            "donor": "bg-blue-100 text-blue-800",
            "admin": "bg-purple-100 text-purple-800",
        }
        color_class = colors.get(obj.role, "bg-gray-100 text-gray-800")

        return format_html(
            '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {}">'
            "{}"
            "</span>",
            color_class,
            obj.get_role_display(),
        )

    @display(description="Verification", boolean=True, ordering="is_verified")
    def verification_status(self, obj):
        """Display verification status with icon"""
        if obj.is_verified:
            return format_html(
                '<span class="inline-flex items-center text-green-600">'
                '<svg class="w-5 h-5 mr-1" fill="currentColor" viewBox="0 0 20 20">'
                '<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>'
                "</svg>"
                "Verified"
                "</span>"
            )
        return format_html(
            '<span class="inline-flex items-center text-red-600">'
            '<svg class="w-5 h-5 mr-1" fill="currentColor" viewBox="0 0 20 20">'
            '<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>'
            "</svg>"
            "Unverified"
            "</span>"
        )

    @display(description="Donations", ordering="donations__count")
    def donations_count(self, obj):
        """Display donation count"""
        count = getattr(obj, "donations_count", obj.donations.count())
        return format_html(
            '<span class="inline-flex items-center px-2 py-1 rounded-md text-sm bg-green-50 text-green-700">'
            "{} donations"
            "</span>",
            count,
        )

    def get_queryset(self, request):
        """Optimize queryset with annotations"""
        qs = super().get_queryset(request)
        qs = qs.select_related().prefetch_related("donations")
        return qs

    # Admin actions
    def verify_users(self, request, queryset):
        """Mark selected users as verified"""
        count = queryset.update(is_verified=True)
        self.message_user(request, f"{count} users marked as verified.")

    verify_users.short_description = "Mark selected users as verified"

    def unverify_users(self, request, queryset):
        """Mark selected users as unverified"""
        count = queryset.update(is_verified=False)
        self.message_user(request, f"{count} users marked as unverified.")

    unverify_users.short_description = "Mark selected users as unverified"

    def make_donors(self, request, queryset):
        """Change role to donor"""
        count = queryset.update(role="donor")
        self.message_user(request, f"{count} users changed to donors.")

    make_donors.short_description = "Change role to donor"

    def make_admins(self, request, queryset):
        """Change role to admin"""
        count = queryset.update(role="admin", is_staff=True)
        self.message_user(request, f"{count} users changed to admins.")

    make_admins.short_description = "Change role to admin"


# Register with custom admin site
admin_site.register(User, UserAdmin)
