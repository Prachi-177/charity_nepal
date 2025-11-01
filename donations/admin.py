from django.contrib import admin
from django.db.models import Count, Sum
from django.utils.html import format_html

from charity_backend.admin import admin_site

from .models import Donation


class DonationAdmin(admin.ModelAdmin):
    """Admin configuration for Donation model"""

    list_display = (
        "donation_info",
        "case_link",
        "donor_info",
        "amount_display",
        "payment_method_badge",
        "status_badge",
        "created_at",
    )
    list_filter = (
        "status",
        "payment_method",
        "is_anonymous",
        "created_at",
        "completed_at",
        "case__category",
    )
    search_fields = (
        "donor__email",
        "donor__first_name",
        "donor__last_name",
        "donor_name",
        "donor_email",
        "case__title",
        "payment_reference",
        "transaction_id",
    )
    ordering = ("-created_at",)
    list_per_page = 25

    fieldsets = (
        (
            "Donation Information",
            {
                "fields": ("case", "amount", "donor_message"),
            },
        ),
        (
            "Donor Information",
            {
                "fields": ("donor", "is_anonymous", "donor_name", "donor_email"),
            },
        ),
        (
            "Payment Details",
            {
                "fields": (
                    "payment_method",
                    "payment_reference",
                    "transaction_id",
                    "status",
                ),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "completed_at"),
                "classes": ("collapse",),
            },
        ),
        (
            "Technical Details",
            {
                "fields": ("ip_address",),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = ("created_at", "completed_at")

    actions = ["mark_completed", "mark_failed", "mark_refunded"]

    def get_queryset(self, request):
        """Optimize queryset with related data"""
        return super().get_queryset(request).select_related("donor", "case")

    def donation_info(self, obj):
        """Display donation ID and reference"""
        return format_html(
            "<div>"
            "<strong>#{}</strong><br>"
            '<small style="color: #6c757d;">Ref: {}</small>'
            "</div>",
            obj.id,
            (
                obj.payment_reference[:20] + "..."
                if len(obj.payment_reference) > 20
                else obj.payment_reference
            ),
        )

    donation_info.short_description = "Donation"

    def case_link(self, obj):
        """Display case as a link"""
        return format_html(
            '<a href="/admin/cases/charitycase/{}/change/" style="color: #007bff; text-decoration: none;">{}</a>',
            obj.case.id,
            obj.case.title[:30] + "..." if len(obj.case.title) > 30 else obj.case.title,
        )

    case_link.short_description = "Case"

    def donor_info(self, obj):
        """Display donor information"""
        if obj.is_anonymous:
            donor_name = obj.donor_name or "Anonymous"
            return format_html(
                '<div style="color: #6c757d;">'
                '<span style="font-style: italic;">🕶️ {}</span>'
                "</div>",
                donor_name,
            )
        else:
            full_name = f"{obj.donor.first_name} {obj.donor.last_name}".strip()
            if not full_name:
                full_name = obj.donor.username
            return format_html(
                "<div>"
                "<strong>{}</strong><br>"
                '<small style="color: #6c757d;">{}</small>'
                "</div>",
                full_name,
                obj.donor.email,
            )

    donor_info.short_description = "Donor"

    def amount_display(self, obj):
        """Display amount with currency formatting"""
        return format_html(
            '<span style="font-weight: bold; color: #28a745;">NPR {}</span>',
            f"{obj.amount:,.0f}",
        )

    amount_display.short_description = "Amount"

    def payment_method_badge(self, obj):
        """Display payment method with badge"""
        colors = {
            " ": "#60c951",
            "khalti": "#5c2d91",
            "bank_transfer": "#007bff",
            "cash": "#28a745",
        }
        color = colors.get(obj.payment_method, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_payment_method_display().upper(),
        )

    payment_method_badge.short_description = "Payment Method"

    def status_badge(self, obj):
        """Display status with colored badge"""
        colors = {
            "pending": "#ffc107",
            "completed": "#28a745",
            "failed": "#dc3545",
            "refunded": "#6c757d",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display().upper(),
        )

    status_badge.short_description = "Status"

    # Admin Actions
    def mark_completed(self, request, queryset):
        """Mark selected donations as completed"""
        from django.utils import timezone

        updated = queryset.update(status="completed", completed_at=timezone.now())
        self.message_user(request, f"✅ {updated} donations marked as completed.")

    mark_completed.short_description = "✅ Mark as completed"

    def mark_failed(self, request, queryset):
        """Mark selected donations as failed"""
        updated = queryset.update(status="failed")
        self.message_user(request, f"❌ {updated} donations marked as failed.")

    mark_failed.short_description = "❌ Mark as failed"

    def mark_refunded(self, request, queryset):
        """Mark selected donations as refunded"""
        updated = queryset.update(status="refunded")
        self.message_user(request, f"↩️ {updated} donations marked as refunded.")

    mark_refunded.short_description = "↩️ Mark as refunded"


# Register with custom admin site
admin_site.register(Donation, DonationAdmin)
