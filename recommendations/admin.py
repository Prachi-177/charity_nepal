from django.contrib import admin
from django.utils.html import format_html

from charity_backend.admin import admin_site

from .models import UserProfile


@admin.register(UserProfile, site=admin_site)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin configuration for UserProfile model"""

    list_display = (
        "user_info",
        "demographics_info",
        "preferences_display",
        "donation_frequency_badge",
        "created_at",
    )
    list_filter = ("age_range", "income_range", "donation_frequency", "created_at")
    search_fields = ("user__email", "user__first_name", "user__last_name")
    ordering = ("-created_at",)

    fieldsets = (
        (
            "User Information",
            {
                "fields": ("user",),
            },
        ),
        (
            "Demographics",
            {
                "fields": ("age_range", "income_range"),
            },
        ),
        (
            "Preferences",
            {
                "fields": ("preferred_categories", "donation_frequency"),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = ("created_at", "updated_at")

    def user_info(self, obj):
        """Display user information"""
        full_name = f"{obj.user.first_name} {obj.user.last_name}".strip()
        if not full_name:
            full_name = obj.user.username
        return format_html(
            "<div>"
            "<strong>{}</strong><br>"
            '<small style="color: #6c757d;">{}</small>'
            "</div>",
            full_name,
            obj.user.email,
        )

    user_info.short_description = "User"

    def demographics_info(self, obj):
        """Display demographics information"""
        age = obj.get_age_range_display() if obj.age_range else "N/A"
        income = obj.get_income_range_display() if obj.income_range else "N/A"
        return format_html(
            "<div>"
            '<small style="color: #6c757d;">Age: {}</small><br>'
            '<small style="color: #6c757d;">Income: {}</small>'
            "</div>",
            age,
            income,
        )

    demographics_info.short_description = "Demographics"

    def preferences_display(self, obj):
        """Display user preferences"""
        categories = obj.preferred_categories or []
        if categories:
            return format_html(
                "<div>" '<small style="color: #007bff;">{}</small>' "</div>",
                ", ".join(categories[:3]) + ("..." if len(categories) > 3 else ""),
            )
        return format_html('<small style="color: #6c757d;">No preferences set</small>')

    preferences_display.short_description = "Preferences"

    def donation_frequency_badge(self, obj):
        """Display donation frequency with badge"""
        if not obj.donation_frequency:
            return format_html(
                '<span style="background-color: #6c757d; color: white; padding: 3px 8px; '
                'border-radius: 12px; font-size: 11px;">N/A</span>'
            )

        colors = {
            "one_time": "#6c757d",
            "monthly": "#28a745",
            "quarterly": "#17a2b8",
            "yearly": "#ffc107",
        }
        color = colors.get(obj.donation_frequency, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_donation_frequency_display().upper(),
        )

    donation_frequency_badge.short_description = "Frequency"
