from django.contrib import admin
from django.db.models import Count, Sum
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display

from .models import CaseUpdate, CharityCase


class CaseUpdateInline(TabularInline):
    """Inline admin for case updates"""

    model = CaseUpdate
    extra = 0
    fields = ("title", "description", "created_by", "created_at")
    readonly_fields = ("created_at",)


@admin.register(CharityCase)
class CharityCaseAdmin(ModelAdmin):
    """Admin configuration for CharityCase model with Unfold theme"""

    # Unfold specific settings
    compressed_fields = True
    list_select_related = True
    warn_unsaved_form = True

    list_display = (
        "title_with_image",
        "beneficiary_info",
        "category_badge",
        "financial_progress",
        "status_badge",
        "urgency_badge",
        "donations_count",
        "created_at",
    )
    list_filter = (
        "category",
        "verification_status",
        "urgency_flag",
        ("created_at", admin.DateFieldListFilter),
        ("deadline", admin.DateFieldListFilter),
        "created_by",
    )
    search_fields = ("title", "description", "beneficiary_name", "tags", "location")
    ordering = ("-created_at",)
    readonly_fields = (
        "slug",
        "created_at",
        "updated_at",
        "completion_percentage_display",
        "days_remaining_display",
    )
    list_per_page = 20
    inlines = [CaseUpdateInline]

    fieldsets = (
        (
            "Case Information",
            {
                "fields": (
                    "title",
                    "slug",
                    "description",
                    "category",
                    "tags",
                ),
                "classes": ("tab",),
            },
        ),
        (
            "Beneficiary Details",
            {
                "fields": (
                    "beneficiary_name",
                    "beneficiary_age",
                    "location",
                ),
                "classes": ("tab",),
            },
        ),
        (
            "Financial Information",
            {
                "fields": (
                    "target_amount",
                    "collected_amount",
                    "completion_percentage_display",
                    "deadline",
                    "days_remaining_display",
                ),
                "classes": ("tab",),
            },
        ),
        (
            "Contact Information",
            {
                "fields": (
                    "contact_phone",
                    "contact_email",
                ),
                "classes": ("tab",),
            },
        ),
        (
            "Status & Approval",
            {
                "fields": (
                    "verification_status",
                    "urgency_flag",
                    "approved_by",
                ),
                "classes": ("tab",),
            },
        ),
        (
            "Media & Documents",
            {
                "fields": (
                    "featured_image",
                    "documents",
                ),
                "classes": ("tab",),
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "created_by",
                    "created_at",
                    "updated_at",
                ),
                "classes": ("tab", "collapse"),
            },
        ),
    )

    actions = ["approve_cases", "reject_cases", "mark_as_urgent", "mark_as_critical"]

    @display(description="Case Title", ordering="title")
    def title_with_image(self, obj):
        """Display title with featured image thumbnail"""
        title = obj.title[:50] + "..." if len(obj.title) > 50 else obj.title

        if obj.featured_image:
            return format_html(
                '<div class="flex items-center space-x-3">'
                '<img src="{}" alt="{}" class="w-12 h-12 object-cover rounded-lg">'
                '<div class="flex flex-col">'
                '<span class="font-medium text-gray-900">{}</span>'
                '<span class="text-sm text-gray-500">{}</span>'
                "</div>"
                "</div>",
                obj.featured_image.url,
                obj.title,
                title,
                obj.beneficiary_name,
            )
        else:
            return format_html(
                '<div class="flex items-center space-x-3">'
                '<div class="w-12 h-12 bg-gray-200 rounded-lg flex items-center justify-center">'
                '<svg class="w-6 h-6 text-gray-400" fill="currentColor" viewBox="0 0 20 20">'
                '<path fill-rule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clip-rule="evenodd"></path>'
                "</svg>"
                "</div>"
                '<div class="flex flex-col">'
                '<span class="font-medium text-gray-900">{}</span>'
                '<span class="text-sm text-gray-500">{}</span>'
                "</div>"
                "</div>",
                title,
                obj.beneficiary_name,
            )

    @display(description="Beneficiary", ordering="beneficiary_name")
    def beneficiary_info(self, obj):
        """Display beneficiary information"""
        age_text = f", {obj.beneficiary_age}y" if obj.beneficiary_age else ""
        location_text = f"📍 {obj.location}" if obj.location else ""

        return format_html(
            '<div class="flex flex-col">'
            '<span class="font-medium">{}{}</span>'
            '<span class="text-sm text-gray-500">{}</span>'
            "</div>",
            obj.beneficiary_name,
            age_text,
            location_text,
        )

    @display(description="Category", ordering="category")
    def category_badge(self, obj):
        """Display category with colored badge"""
        category_colors = {
            "cancer": "bg-red-100 text-red-800",
            "accident": "bg-orange-100 text-orange-800",
            "education": "bg-blue-100 text-blue-800",
            "medical": "bg-green-100 text-green-800",
            "disaster": "bg-purple-100 text-purple-800",
            "acid_attack": "bg-pink-100 text-pink-800",
            "other": "bg-gray-100 text-gray-800",
        }
        color_class = category_colors.get(obj.category, "bg-gray-100 text-gray-800")

        return format_html(
            '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {}">'
            "{}"
            "</span>",
            color_class,
            obj.get_category_display(),
        )

    @display(description="Progress", ordering="collected_amount")
    def financial_progress(self, obj):
        """Display financial progress with progress bar"""
        percentage = obj.completion_percentage

        # Progress bar color based on completion
        bar_color = (
            "bg-green-500"
            if percentage >= 100
            else "bg-blue-500" if percentage >= 50 else "bg-yellow-500"
        )

        return format_html(
            '<div class="flex flex-col w-32">'
            '<div class="flex justify-between text-xs text-gray-600 mb-1">'
            "<span>{:.0f}%</span>"
            "<span>NPR {:,.0f}</span>"
            "</div>"
            '<div class="w-full bg-gray-200 rounded-full h-2">'
            '<div class="h-2 rounded-full {}" style="width: {}%"></div>'
            "</div>"
            '<div class="text-xs text-gray-500 mt-1">NPR {:,.0f}</div>'
            "</div>",
            percentage,
            obj.collected_amount,
            bar_color,
            min(percentage, 100),
            obj.target_amount,
        )

    @display(description="Status", ordering="verification_status")
    def status_badge(self, obj):
        """Display verification status with colored badge"""
        status_colors = {
            "pending": "bg-yellow-100 text-yellow-800",
            "approved": "bg-green-100 text-green-800",
            "rejected": "bg-red-100 text-red-800",
            "completed": "bg-blue-100 text-blue-800",
            "cancelled": "bg-gray-100 text-gray-800",
        }
        color_class = status_colors.get(
            obj.verification_status, "bg-gray-100 text-gray-800"
        )

        return format_html(
            '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {}">'
            "{}"
            "</span>",
            color_class,
            obj.get_verification_status_display(),
        )

    @display(description="Urgency", ordering="urgency_flag")
    def urgency_badge(self, obj):
        """Display urgency with colored badge"""
        urgency_colors = {
            "low": "bg-gray-100 text-gray-800",
            "medium": "bg-yellow-100 text-yellow-800",
            "high": "bg-orange-100 text-orange-800",
            "critical": "bg-red-100 text-red-800",
        }
        color_class = urgency_colors.get(obj.urgency_flag, "bg-gray-100 text-gray-800")

        return format_html(
            '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {}">'
            "{}"
            "</span>",
            color_class,
            obj.get_urgency_flag_display(),
        )

    @display(description="Donations")
    def donations_count(self, obj):
        """Display donations count"""
        count = getattr(obj, "donations_count", obj.donations.count())
        return format_html(
            '<span class="inline-flex items-center px-2 py-1 rounded-md text-sm bg-blue-50 text-blue-700">'
            "{} donations"
            "</span>",
            count,
        )

    @display(description="Completion %")
    def completion_percentage_display(self, obj):
        """Display completion percentage with progress indicator"""
        percentage = obj.completion_percentage
        color = (
            "text-green-600"
            if percentage >= 100
            else "text-blue-600" if percentage >= 50 else "text-yellow-600"
        )
        return format_html(
            '<span class="font-semibold {}">{:.1f}%</span>', color, percentage
        )

    @display(description="Days Remaining")
    def days_remaining_display(self, obj):
        """Display days remaining until deadline"""
        days = obj.days_remaining
        if days is None:
            return "No deadline"
        elif days <= 0:
            return format_html(
                '<span class="text-red-600 font-semibold">Expired</span>'
            )
        elif days <= 7:
            return format_html(
                '<span class="text-orange-600 font-semibold">{} days</span>', days
            )
        else:
            return format_html('<span class="text-green-600">{} days</span>', days)

    def get_queryset(self, request):
        """Optimize queryset with annotations"""
        qs = super().get_queryset(request)
        qs = qs.select_related("created_by", "approved_by").prefetch_related(
            "donations"
        )
        qs = qs.annotate(donations_count=Count("donations"))
        return qs

    # Admin actions
    @admin.action(description="✅ Approve selected cases")
    def approve_cases(self, request, queryset):
        updated = queryset.update(
            verification_status="approved", approved_by=request.user
        )
        self.message_user(request, f"✅ {updated} cases were approved.")

    @admin.action(description="❌ Reject selected cases")
    def reject_cases(self, request, queryset):
        updated = queryset.update(
            verification_status="rejected", approved_by=request.user
        )
        self.message_user(request, f"❌ {updated} cases were rejected.")

    @admin.action(description="🔥 Mark as high priority")
    def mark_as_urgent(self, request, queryset):
        updated = queryset.update(urgency_flag="high")
        self.message_user(request, f"🔥 {updated} cases marked as high priority.")

    @admin.action(description="🚨 Mark as critical")
    def mark_as_critical(self, request, queryset):
        updated = queryset.update(urgency_flag="critical")
        self.message_user(request, f"🚨 {updated} cases marked as critical.")


@admin.register(CaseUpdate)
class CaseUpdateAdmin(ModelAdmin):
    """Admin configuration for CaseUpdate model with Unfold theme"""

    # Unfold specific settings
    compressed_fields = True
    warn_unsaved_form = True

    list_display = ("update_title", "case_link", "author_info", "created_at")
    list_filter = (
        ("created_at", admin.DateFieldListFilter),
        "case__category",
        "case__verification_status",
        "created_by",
    )
    search_fields = ("title", "description", "case__title", "case__beneficiary_name")
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)
    list_per_page = 25

    fieldsets = (
        (
            "Update Information",
            {"fields": ("case", "title", "description"), "classes": ("tab",)},
        ),
        ("Media", {"fields": ("image",), "classes": ("tab",)}),
        ("Metadata", {"fields": ("created_by", "created_at"), "classes": ("tab",)}),
    )

    @display(description="Update", ordering="title")
    def update_title(self, obj):
        """Display update title with icon"""
        return format_html(
            '<div class="flex items-center space-x-2">'
            '<svg class="w-4 h-4 text-blue-500" fill="currentColor" viewBox="0 0 20 20">'
            '<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>'
            "</svg>"
            '<span class="font-medium">{}</span>'
            "</div>",
            obj.title,
        )

    @display(description="Case", ordering="case__title")
    def case_link(self, obj):
        """Display case title as a link"""
        return format_html(
            '<div class="flex flex-col">'
            '<a href="/admin/cases/charitycase/{}/change/" class="text-blue-600 hover:text-blue-800 font-medium">{}</a>'
            '<span class="text-sm text-gray-500">{}</span>'
            "</div>",
            obj.case.id,
            obj.case.title[:40] + "..." if len(obj.case.title) > 40 else obj.case.title,
            obj.case.beneficiary_name,
        )

    @display(description="Author", ordering="created_by__first_name")
    def author_info(self, obj):
        """Display author information"""
        full_name = f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
        if not full_name:
            full_name = obj.created_by.username

        return format_html(
            '<div class="flex items-center space-x-2">'
            '<div class="w-6 h-6 bg-green-100 text-green-800 rounded-full flex items-center justify-center text-xs font-semibold">'
            "{}"
            "</div>"
            '<span class="text-sm font-medium">{}</span>'
            "</div>",
            full_name[0].upper(),
            full_name,
        )
