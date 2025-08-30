from django.contrib import admin
from django.db.models import Avg, Count
from django.utils.html import format_html

from charity_backend.admin import admin_site

from .models import (
    AlgorithmPerformance,
    RecommendationHistory,
    UserProfile,
    UserRecommendation,
)


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


@admin.register(RecommendationHistory, site=admin_site)
class RecommendationHistoryAdmin(admin.ModelAdmin):
    """Admin configuration for RecommendationHistory model"""

    list_display = (
        "user_info",
        "case_link",
        "algorithm_badge",
        "score_display",
        "interaction_status",
        "created_at",
    )
    list_filter = ("algorithm_used", "clicked", "donated", "shared", "created_at")
    search_fields = ("user__email", "case__title")
    ordering = ("-created_at",)
    list_per_page = 25

    fieldsets = (
        (
            "Recommendation",
            {
                "fields": ("user", "case", "algorithm_used", "recommendation_score"),
            },
        ),
        (
            "Interactions",
            {
                "fields": (
                    "clicked",
                    "clicked_at",
                    "donated",
                    "donated_at",
                    "shared",
                    "shared_at",
                ),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at",),
            },
        ),
    )

    readonly_fields = ("created_at", "clicked_at", "donated_at", "shared_at")

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

    def case_link(self, obj):
        """Display case as link"""
        title = (
            obj.case.title[:30] + "..." if len(obj.case.title) > 30 else obj.case.title
        )
        return format_html(
            '<a href="/admin/cases/charitycase/{}/change/" style="color: #007bff;">{}</a>',
            obj.case.id,
            title,
        )

    def algorithm_badge(self, obj):
        """Display algorithm with badge"""
        colors = {
            "content": "#007bff",
            "collaborative": "#28a745",
            "clustering": "#ffc107",
            "decision_tree": "#dc3545",
            "hybrid": "#6c757d",
        }
        color = colors.get(obj.algorithm_used, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_algorithm_used_display().upper(),
        )

    def score_display(self, obj):
        """Display recommendation score with color coding"""
        if obj.recommendation_score >= 0.8:
            color = "#28a745"
        elif obj.recommendation_score >= 0.6:
            color = "#ffc107"
        else:
            color = "#dc3545"

        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.2f}</span>',
            color,
            obj.recommendation_score,
        )

    def interaction_status(self, obj):
        """Display interaction status"""
        status = []
        if obj.clicked:
            status.append("👆 Clicked")
        if obj.donated:
            status.append("💝 Donated")
        if obj.shared:
            status.append("📤 Shared")

        if not status:
            return format_html('<small style="color: #6c757d;">No interactions</small>')

        return format_html(
            '<small style="color: #28a745;">{}</small>', " | ".join(status)
        )


@admin.register(UserRecommendation, site=admin_site)
class UserRecommendationAdmin(admin.ModelAdmin):
    """Admin configuration for UserRecommendation model"""

    list_display = (
        "recommendation_info",
        "user_link",
        "case_link",
        "algorithm_badge",
        "confidence_display",
        "interaction_badges",
        "created_at",
    )
    list_filter = (
        "algorithm_used",
        "is_viewed",
        "is_clicked",
        "is_donated",
        "created_at",
    )
    search_fields = ("user__email", "recommended_case__title")
    ordering = ("-created_at",)
    list_per_page = 25

    fieldsets = (
        (
            "Recommendation",
            {
                "fields": (
                    "user",
                    "recommended_case",
                    "algorithm_used",
                    "confidence_score",
                ),
            },
        ),
        (
            "Interactions",
            {
                "fields": ("is_viewed", "is_clicked", "is_donated"),
            },
        ),
        (
            "Context",
            {
                "fields": ("recommendation_context",),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "viewed_at", "clicked_at", "donated_at"),
            },
        ),
    )

    readonly_fields = ("created_at", "viewed_at", "clicked_at", "donated_at")

    def recommendation_info(self, obj):
        """Display recommendation info"""
        return format_html(
            "<div>"
            "<strong>Rec #{}</strong><br>"
            '<small style="color: #6c757d;">Score: {:.2f}</small>'
            "</div>",
            obj.id,
            obj.confidence_score,
        )

    def user_link(self, obj):
        """Display user as link"""
        full_name = f"{obj.user.first_name} {obj.user.last_name}".strip()
        if not full_name:
            full_name = obj.user.username
        return format_html(
            '<a href="/admin/users/user/{}/change/" style="color: #007bff;">{}</a>',
            obj.user.id,
            full_name,
        )

    def case_link(self, obj):
        """Display case as link"""
        title = (
            obj.recommended_case.title[:30] + "..."
            if len(obj.recommended_case.title) > 30
            else obj.recommended_case.title
        )
        return format_html(
            '<a href="/admin/cases/charitycase/{}/change/" style="color: #007bff;">{}</a>',
            obj.recommended_case.id,
            title,
        )

    def algorithm_badge(self, obj):
        """Display algorithm with badge"""
        colors = {
            "content_based": "#007bff",
            "collaborative": "#28a745",
            "hybrid": "#6c757d",
            "category_based": "#ffc107",
            "popularity": "#17a2b8",
        }
        color = colors.get(obj.algorithm_used, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_algorithm_used_display().upper(),
        )

    def confidence_display(self, obj):
        """Display confidence score with color coding"""
        if obj.confidence_score >= 0.8:
            color = "#28a745"
        elif obj.confidence_score >= 0.6:
            color = "#ffc107"
        else:
            color = "#dc3545"

        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.2f}</span>',
            color,
            obj.confidence_score,
        )

    def interaction_badges(self, obj):
        """Display interaction badges"""
        badges = []
        if obj.is_viewed:
            badges.append(
                '<span style="background-color: #007bff; color: white; padding: 2px 6px; border-radius: 8px; font-size: 10px;">👁️ VIEWED</span>'
            )
        if obj.is_clicked:
            badges.append(
                '<span style="background-color: #ffc107; color: white; padding: 2px 6px; border-radius: 8px; font-size: 10px;">👆 CLICKED</span>'
            )
        if obj.is_donated:
            badges.append(
                '<span style="background-color: #28a745; color: white; padding: 2px 6px; border-radius: 8px; font-size: 10px;">💝 DONATED</span>'
            )

        if not badges:
            return format_html('<small style="color: #6c757d;">No interactions</small>')

        return format_html(" ".join(badges))


@admin.register(AlgorithmPerformance, site=admin_site)
class AlgorithmPerformanceAdmin(admin.ModelAdmin):
    """Admin configuration for AlgorithmPerformance model"""

    list_display = (
        "algorithm_name",
        "date",
        "recommendations_count",
        "ctr_display",
        "conversion_display",
        "avg_confidence_display",
    )
    list_filter = ("algorithm_name", "date", "created_at")
    search_fields = ("algorithm_name",)
    ordering = ("-date", "algorithm_name")
    list_per_page = 25

    fieldsets = (
        (
            "Algorithm & Date",
            {
                "fields": ("algorithm_name", "date"),
            },
        ),
        (
            "Metrics",
            {
                "fields": (
                    "total_recommendations",
                    "clicked_recommendations",
                    "donated_recommendations",
                ),
            },
        ),
        (
            "Calculated Rates",
            {
                "fields": (
                    "click_through_rate",
                    "conversion_rate",
                    "avg_confidence_score",
                ),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at",),
            },
        ),
    )

    readonly_fields = ("created_at",)

    def recommendations_count(self, obj):
        """Display total recommendations"""
        return format_html(
            '<strong style="color: #007bff;">{}</strong>', obj.total_recommendations
        )

    def ctr_display(self, obj):
        """Display click-through rate"""
        if obj.click_through_rate >= 0.1:
            color = "#28a745"
        elif obj.click_through_rate >= 0.05:
            color = "#ffc107"
        else:
            color = "#dc3545"

        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.2%}</span>',
            color,
            obj.click_through_rate,
        )

    def conversion_display(self, obj):
        """Display conversion rate"""
        if obj.conversion_rate >= 0.05:
            color = "#28a745"
        elif obj.conversion_rate >= 0.02:
            color = "#ffc107"
        else:
            color = "#dc3545"

        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.2%}</span>',
            color,
            obj.conversion_rate,
        )

    def avg_confidence_display(self, obj):
        """Display average confidence score"""
        if obj.avg_confidence_score >= 0.8:
            color = "#28a745"
        elif obj.avg_confidence_score >= 0.6:
            color = "#ffc107"
        else:
            color = "#dc3545"

        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.2f}</span>',
            color,
            obj.avg_confidence_score,
        )
