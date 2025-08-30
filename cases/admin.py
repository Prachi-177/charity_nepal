from django.contrib import admin
from django.db import models
from django.db.models import Count, Sum
from django.utils.html import format_html

from charity_backend.admin import admin_site

from .models import CaseUpdate, CharityCase


class CaseUpdateInline(admin.TabularInline):
    """Inline admin for case updates"""

    model = CaseUpdate
    extra = 0
    fields = ("title", "description", "created_by", "created_at")
    readonly_fields = ("created_at",)


class CharityCaseAdmin(admin.ModelAdmin):
    """Admin configuration for CharityCase model"""

    list_display = (
        "title",
        "category",
        "beneficiary_name",
        "verification_status_badge",
        "urgency_flag",
        "progress_display",
        "target_amount",
        "collected_amount",
        "created_at",
    )
    list_filter = (
        "verification_status",
        "category",
        "urgency_flag",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "title",
        "description",
        "beneficiary_name",
        "contact_phone",
        "contact_email",
        "created_by__email",
        "created_by__first_name",
        "created_by__last_name",
    )
    ordering = ("-created_at",)
    list_per_page = 25

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": ("title", "description", "category", "urgency_flag"),
            },
        ),
        (
            "Financial Details",
            {
                "fields": ("target_amount", "collected_amount"),
            },
        ),
        (
            "Beneficiary Information",
            {
                "fields": (
                    "beneficiary_name",
                    "beneficiary_age",
                    "contact_phone",
                    "contact_email",
                    "location",
                ),
            },
        ),
        (
            "Case Management",
            {
                "fields": (
                    "verification_status",
                    "created_by",
                    "approved_by",
                ),
            },
        ),
        (
            "Media & Documents",
            {
                "fields": ("featured_image", "documents"),
                "classes": ("collapse",),
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

    readonly_fields = ("created_at", "updated_at", "collected_amount")
    inlines = [CaseUpdateInline]

    actions = ["approve_cases", "reject_cases", "mark_completed"]

    def get_queryset(self, request):
        """Optimize queryset with related data"""
        queryset = super().get_queryset(request)
        queryset = queryset.select_related("created_by", "approved_by")
        queryset = queryset.annotate(
            donations_count=Count("donations", distinct=True),
            total_raised=Sum(
                "donations__amount", filter=models.Q(donations__status="completed")
            ),
        )
        return queryset

    def verification_status_badge(self, obj):
        """Display verification status with colored badge"""
        colors = {
            "pending": "#ffc107",  # Warning yellow
            "approved": "#28a745",  # Success green
            "rejected": "#dc3545",  # Danger red
            "completed": "#17a2b8",  # Info blue
            "cancelled": "#6c757d",  # Secondary gray
        }
        color = colors.get(obj.verification_status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_verification_status_display().upper(),
        )

    verification_status_badge.short_description = "Status"

    def progress_display(self, obj):
        """Display fundraising progress with visual bar"""
        if obj.target_amount > 0:
            percentage = min(float(obj.collected_amount / obj.target_amount * 100), 100)
            color = "#28a745" if percentage >= 100 else "#007bff"
            return format_html(
                '<div style="width: 100px; background-color: #e9ecef; border-radius: 10px; overflow: hidden;">'
                '<div style="width: {}%; background-color: {}; height: 20px; line-height: 20px; '
                'text-align: center; color: white; font-size: 11px; font-weight: bold;">'
                "{}%</div></div>",
                percentage,
                color,
                round(percentage, 1),
            )
        return "N/A"

    progress_display.short_description = "Progress"

    # Admin Actions
    def approve_cases(self, request, queryset):
        """Approve selected cases"""
        count = queryset.update(
            verification_status="approved", approved_by=request.user
        )
        self.message_user(request, f"✅ {count} cases approved.")

    approve_cases.short_description = "Approve selected cases"

    def reject_cases(self, request, queryset):
        """Reject selected cases"""
        count = queryset.update(
            verification_status="rejected", approved_by=request.user
        )
        self.message_user(request, f"❌ {count} cases rejected.")

    reject_cases.short_description = "Reject selected cases"

    def mark_completed(self, request, queryset):
        """Mark selected cases as completed"""
        count = queryset.update(verification_status="completed")
        self.message_user(request, f"🎉 {count} cases marked as completed.")

    mark_completed.short_description = "Mark as completed"


class CaseUpdateAdmin(admin.ModelAdmin):
    """Admin configuration for CaseUpdate model"""

    list_display = (
        "title_display",
        "case_link",
        "author_info",
        "created_at",
    )
    list_filter = (
        "created_at",
        "case__category",
        "case__verification_status",
    )
    search_fields = (
        "title",
        "description",
        "case__title",
        "created_by__email",
        "created_by__first_name",
        "created_by__last_name",
    )
    ordering = ("-created_at",)

    fieldsets = (
        (
            "Update Information",
            {
                "fields": ("case", "title", "description"),
            },
        ),
        (
            "Meta Information",
            {
                "fields": ("created_by", "created_at"),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = ("created_at",)

    def get_queryset(self, request):
        """Optimize queryset with related data"""
        return super().get_queryset(request).select_related("case", "created_by")

    def title_display(self, obj):
        """Display update title with icon"""
        return format_html(
            '<div style="display: flex; align-items: center;">'
            '<span style="margin-right: 8px;">📄</span>'
            '<span style="font-weight: bold;">{}</span>'
            "</div>",
            obj.title,
        )

    title_display.short_description = "Update"

    def case_link(self, obj):
        """Display case title as a link"""
        return format_html(
            "<div>"
            '<a href="/admin/cases/charitycase/{}/change/" style="color: #007bff; text-decoration: none;">{}</a>'
            '<br><small style="color: #6c757d;">{}</small>'
            "</div>",
            obj.case.id,
            obj.case.title[:40] + "..." if len(obj.case.title) > 40 else obj.case.title,
            obj.case.beneficiary_name,
        )

    case_link.short_description = "Case"

    def author_info(self, obj):
        """Display author information"""
        full_name = f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
        if not full_name:
            full_name = obj.created_by.username

        return format_html(
            '<div style="display: flex; align-items: center;">'
            '<div style="width: 24px; height: 24px; background-color: #007bff; color: white; '
            "border-radius: 50%; display: flex; align-items: center; justify-content: center; "
            'font-size: 12px; font-weight: bold; margin-right: 8px;">{}</div>'
            "<span>{}</span>"
            "</div>",
            full_name[0].upper(),
            full_name,
        )

    author_info.short_description = "Author"


# Register with custom admin site
admin_site.register(CharityCase, CharityCaseAdmin)
admin_site.register(CaseUpdate, CaseUpdateAdmin)
