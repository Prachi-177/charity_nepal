from django.contrib import admin
from django.db.models import Count, Sum
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from unfold.admin import ModelAdmin
from unfold.decorators import display

from .models import Donation


@admin.register(Donation)
class DonationAdmin(ModelAdmin):
    """Admin configuration for Donation model with Unfold theme"""

    # Unfold specific settings
    compressed_fields = True
    list_select_related = True
    warn_unsaved_form = True

    list_display = (
        "donation_info",
        "donor_info",
        "case_link",
        "amount_display",
        "payment_info",
        "status_badge",
        "created_at",
    )
    list_filter = (
        "status",
        "payment_method",
        "is_anonymous",
        ("created_at", admin.DateFieldListFilter),
        ("completed_at", admin.DateFieldListFilter),
        "case__category",
    )
    search_fields = (
        "payment_reference",
        "transaction_id",
        "donor__email",
        "donor__first_name",
        "donor__last_name",
        "donor_name",
        "donor_email",
        "case__title",
        "case__beneficiary_name",
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "completed_at", "payment_reference")
    list_per_page = 25

    fieldsets = (
        (
            "Donation Information",
            {
                "fields": (
                    "donor",
                    "case",
                    "amount",
                    "donor_message",
                ),
                "classes": ("tab",),
            },
        ),
        (
            "Anonymous Donation Details",
            {
                "fields": (
                    "is_anonymous",
                    "donor_name",
                    "donor_email",
                ),
                "classes": ("tab",),
            },
        ),
        (
            "Payment Information",
            {
                "fields": (
                    "payment_method",
                    "payment_reference",
                    "transaction_id",
                    "status",
                ),
                "classes": ("tab",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "completed_at",
                ),
                "classes": ("tab",),
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "ip_address",
                    "user_agent",
                ),
                "classes": ("tab", "collapse"),
            },
        ),
    )

    actions = ["mark_completed", "mark_failed", "mark_refunded"]

    @display(description="Donation", ordering="id")
    def donation_info(self, obj):
        """Display donation ID and reference"""
        return format_html(
            '<div class="flex flex-col">'
            '<span class="font-mono text-sm font-semibold">#{}</span>'
            '<span class="text-xs text-gray-500">{}</span>'
            "</div>",
            obj.id,
            obj.payment_reference,
        )

    @display(description="Donor", ordering="donor__first_name")
    def donor_info(self, obj):
        """Display donor information with avatar"""
        if obj.is_anonymous:
            name = obj.donor_name or "Anonymous Donor"
            email = obj.donor_email or ""
            initials = "AN"
            avatar_bg = "bg-gray-100 text-gray-600"
        else:
            name = (
                f"{obj.donor.first_name} {obj.donor.last_name}".strip()
                or obj.donor.username
            )
            email = obj.donor.email
            initials = "".join([word[0].upper() for word in name.split()[:2]])
            avatar_bg = "bg-green-100 text-green-800"

        return format_html(
            '<div class="flex items-center space-x-3">'
            '<div class="w-8 h-8 {} rounded-full flex items-center justify-center text-sm font-semibold">'
            "{}"
            "</div>"
            '<div class="flex flex-col">'
            '<span class="font-medium">{}</span>'
            '<span class="text-sm text-gray-500">{}</span>'
            "</div>"
            "</div>",
            avatar_bg,
            initials,
            name,
            email[:30] + "..." if len(email) > 30 else email,
        )

    @display(description="Case", ordering="case__title")
    def case_link(self, obj):
        """Display case title as clickable link"""
        title = (
            obj.case.title[:30] + "..." if len(obj.case.title) > 30 else obj.case.title
        )
        return format_html(
            '<div class="flex flex-col">'
            '<a href="/admin/cases/charitycase/{}/change/" class="text-blue-600 hover:text-blue-800 font-medium">{}</a>'
            '<span class="text-sm text-gray-500">{}</span>'
            "</div>",
            obj.case.id,
            title,
            obj.case.beneficiary_name,
        )

    @display(description="Amount", ordering="amount")
    def amount_display(self, obj):
        """Display donation amount with currency"""
        # Color based on amount
        if obj.amount >= 10000:
            color = "text-green-600 font-bold"
        elif obj.amount >= 1000:
            color = "text-blue-600 font-semibold"
        else:
            color = "text-gray-800"

        return format_html(
            '<div class="flex flex-col">'
            '<span class="{}">NPR {}</span>'
            "</div>",
            color,
            f"{obj.amount:,.0f}",
        )

    @display(description="Payment", ordering="payment_method")
    def payment_info(self, obj):
        """Display payment method with icon"""
        method_icons = {
            "esewa": "💳",
            "khalti": "📱",
            "bank_transfer": "🏦",
            "cash": "💵",
        }

        icon = method_icons.get(obj.payment_method, "💳")
        method_name = obj.get_payment_method_display()

        txn_display = (
            obj.transaction_id[:10] + "..."
            if obj.transaction_id and len(obj.transaction_id) > 10
            else obj.transaction_id or ""
        )

        return format_html(
            '<div class="flex flex-col">'
            '<span class="flex items-center space-x-1">'
            "<span>{}</span>"
            '<span class="text-sm font-medium">{}</span>'
            "</span>"
            "{}"
            "</div>",
            icon,
            method_name,
            (
                f'<span class="text-xs text-gray-500 font-mono">{txn_display}</span>'
                if txn_display
                else ""
            ),
        )

    @display(description="Status", ordering="status")
    def status_badge(self, obj):
        """Display status with colored badge and completion time"""
        status_config = {
            "pending": {"color": "bg-yellow-100 text-yellow-800", "icon": "⏳"},
            "completed": {"color": "bg-green-100 text-green-800", "icon": "✅"},
            "failed": {"color": "bg-red-100 text-red-800", "icon": "❌"},
            "refunded": {"color": "bg-purple-100 text-purple-800", "icon": "↩️"},
        }

        config = status_config.get(obj.status, status_config["pending"])
        status_text = obj.get_status_display()

        completed_info = ""
        if obj.status == "completed" and obj.completed_at:
            completed_info = f'<div class="text-xs text-gray-500 mt-1">{obj.completed_at.strftime("%b %d, %Y")}</div>'

        return format_html(
            "<div>"
            '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {}">'
            '<span class="mr-1">{}</span>{}'
            "</span>"
            "{}"
            "</div>",
            config["color"],
            config["icon"],
            status_text,
            mark_safe(completed_info),
        )

    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        qs = qs.select_related("donor", "case")
        return qs

    # Admin actions
    @admin.action(description="✅ Mark as completed")
    def mark_completed(self, request, queryset):
        from django.utils import timezone

        updated = queryset.update(status="completed", completed_at=timezone.now())
        self.message_user(request, f"✅ {updated} donations marked as completed.")

    @admin.action(description="❌ Mark as failed")
    def mark_failed(self, request, queryset):
        updated = queryset.update(status="failed")
        self.message_user(request, f"❌ {updated} donations marked as failed.")

    @admin.action(description="↩️ Mark as refunded")
    def mark_refunded(self, request, queryset):
        updated = queryset.update(status="refunded")
        self.message_user(request, f"↩️ {updated} donations marked as refunded.")
