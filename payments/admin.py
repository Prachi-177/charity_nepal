from django.contrib import admin
from django.db.models import Count, Sum
from django.utils.html import format_html

from charity_backend.admin import admin_site

from .models import PaymentGateway, PaymentIntent, PaymentWebhook, RefundRequest


@admin.register(PaymentGateway, site=admin_site)
class PaymentGatewayAdmin(admin.ModelAdmin):
    """Admin configuration for PaymentGateway model"""

    list_display = (
        "name_badge",
        "status_badge",
        "merchant_code",
        "api_url",
        "created_at",
    )
    list_filter = ("is_active", "name", "created_at")
    search_fields = ("name", "merchant_code")
    ordering = ("name",)

    fieldsets = (
        (
            "Gateway Information",
            {
                "fields": ("name", "is_active"),
            },
        ),
        (
            "API Configuration",
            {
                "fields": ("merchant_code", "secret_key", "public_key", "api_url"),
            },
        ),
        (
            "URLs",
            {
                "fields": ("success_url", "failure_url"),
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

    readonly_fields = ("created_at", "updated_at")

    def name_badge(self, obj):
        """Display gateway name with badge"""
        colors = {
            "esewa": "#60c951",
            "khalti": "#5c2d91",
            "imepay": "#007bff",
        }
        color = colors.get(obj.name, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_name_display().upper(),
        )

    name_badge.short_description = "Gateway"

    def status_badge(self, obj):
        """Display active status with badge"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 8px; '
                'border-radius: 12px; font-size: 11px; font-weight: bold;">✅ ACTIVE</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 3px 8px; '
                'border-radius: 12px; font-size: 11px; font-weight: bold;">❌ INACTIVE</span>'
            )

    status_badge.short_description = "Status"


@admin.register(PaymentIntent, site=admin_site)
class PaymentIntentAdmin(admin.ModelAdmin):
    """Admin configuration for PaymentIntent model"""

    list_display = (
        "intent_info",
        "donation_link",
        "gateway_badge",
        "amount_display",
        "status_badge",
        "expires_at",
        "created_at",
    )
    list_filter = ("status", "gateway", "created_at", "expires_at")
    search_fields = ("id", "gateway_payment_id", "donation__id")
    ordering = ("-created_at",)
    list_per_page = 25

    fieldsets = (
        (
            "Intent Information",
            {
                "fields": ("id", "donation", "gateway", "amount", "currency"),
            },
        ),
        (
            "Gateway Details",
            {
                "fields": ("gateway_payment_id", "gateway_response"),
            },
        ),
        (
            "QR Code",
            {
                "fields": ("qr_code_data", "qr_code_image"),
                "classes": ("collapse",),
            },
        ),
        (
            "URLs",
            {
                "fields": ("return_url", "cancel_url"),
            },
        ),
        (
            "Status & Timing",
            {
                "fields": ("status", "created_at", "expires_at", "processed_at"),
            },
        ),
        (
            "Metadata",
            {
                "fields": ("client_ip", "user_agent"),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = ("id", "created_at", "processed_at")

    def intent_info(self, obj):
        """Display intent ID and payment ID"""
        return format_html(
            "<div>"
            "<strong>{}</strong><br>"
            '<small style="color: #6c757d;">Gateway: {}</small>'
            "</div>",
            str(obj.id)[:8] + "...",
            obj.gateway_payment_id or "N/A",
        )

    intent_info.short_description = "Intent"

    def donation_link(self, obj):
        """Display donation as link"""
        return format_html(
            '<a href="/admin/donations/donation/{}/change/" style="color: #007bff;">#{}</a>',
            obj.donation.id,
            obj.donation.id,
        )

    donation_link.short_description = "Donation"

    def gateway_badge(self, obj):
        """Display gateway with badge"""
        colors = {
            "esewa": "#60c951",
            "khalti": "#5c2d91",
            "imepay": "#007bff",
        }
        color = colors.get(obj.gateway.name, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.gateway.get_name_display().upper(),
        )

    gateway_badge.short_description = "Gateway"

    def amount_display(self, obj):
        """Display amount with currency"""
        return format_html(
            '<span style="font-weight: bold; color: #007bff;">{} {}</span>',
            obj.currency,
            f"{obj.amount:,.0f}",
        )

    amount_display.short_description = "Amount"

    def status_badge(self, obj):
        """Display status with colored badge"""
        colors = {
            "created": "#6c757d",
            "processing": "#ffc107",
            "succeeded": "#28a745",
            "failed": "#dc3545",
            "cancelled": "#6c757d",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display().upper(),
        )

    status_badge.short_description = "Status"


@admin.register(PaymentWebhook, site=admin_site)
class PaymentWebhookAdmin(admin.ModelAdmin):
    """Admin configuration for PaymentWebhook model"""

    list_display = (
        "webhook_info",
        "gateway_badge",
        "event_type_badge",
        "processed_badge",
        "received_at",
    )
    list_filter = ("processed", "event_type", "gateway", "received_at")
    search_fields = ("webhook_id", "payment_intent__id")
    ordering = ("-received_at",)
    list_per_page = 25

    fieldsets = (
        (
            "Webhook Information",
            {
                "fields": ("webhook_id", "gateway", "event_type", "payment_intent"),
            },
        ),
        (
            "Processing",
            {
                "fields": ("processed", "processing_error", "processed_at"),
            },
        ),
        (
            "Data",
            {
                "fields": ("raw_data",),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("received_at",),
            },
        ),
    )

    readonly_fields = ("received_at", "processed_at")

    def webhook_info(self, obj):
        """Display webhook ID"""
        return format_html(
            "<div>"
            "<strong>{}</strong><br>"
            '<small style="color: #6c757d;">ID: {}</small>'
            "</div>",
            obj.webhook_id[:15] + "..." if len(obj.webhook_id) > 15 else obj.webhook_id,
            obj.id,
        )

    webhook_info.short_description = "Webhook"

    def gateway_badge(self, obj):
        """Display gateway with badge"""
        colors = {
            "esewa": "#60c951",
            "khalti": "#5c2d91",
            "imepay": "#007bff",
        }
        color = colors.get(obj.gateway.name, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.gateway.get_name_display().upper(),
        )

    gateway_badge.short_description = "Gateway"

    def event_type_badge(self, obj):
        """Display event type with badge"""
        colors = {
            "payment.completed": "#28a745",
            "payment.failed": "#dc3545",
            "payment.cancelled": "#6c757d",
            "refund.completed": "#ffc107",
        }
        color = colors.get(obj.event_type, "#007bff")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_event_type_display().upper(),
        )

    event_type_badge.short_description = "Event Type"

    def processed_badge(self, obj):
        """Display processed status"""
        if obj.processed:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 8px; '
                'border-radius: 12px; font-size: 11px; font-weight: bold;">✅ YES</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #ffc107; color: white; padding: 3px 8px; '
                'border-radius: 12px; font-size: 11px; font-weight: bold;">⏳ NO</span>'
            )

    processed_badge.short_description = "Processed"


@admin.register(RefundRequest, site=admin_site)
class RefundRequestAdmin(admin.ModelAdmin):
    """Admin configuration for RefundRequest model"""

    list_display = (
        "refund_info",
        "donation_link",
        "amount_display",
        "reason_badge",
        "status_badge",
        "requested_at",
    )
    list_filter = ("status", "reason", "requested_at")
    search_fields = ("donation__id", "requested_by__email", "gateway_refund_id")
    ordering = ("-requested_at",)
    list_per_page = 25

    actions = ["approve_refunds", "reject_refunds"]

    fieldsets = (
        (
            "Refund Information",
            {
                "fields": ("donation", "amount", "reason", "description"),
            },
        ),
        (
            "Processing",
            {
                "fields": ("status", "requested_by", "approved_by"),
            },
        ),
        (
            "Gateway Response",
            {
                "fields": ("gateway_refund_id", "gateway_response"),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("requested_at", "processed_at"),
            },
        ),
    )

    readonly_fields = ("requested_at", "processed_at")

    def refund_info(self, obj):
        """Display refund info"""
        return format_html(
            "<div>"
            "<strong>Refund #{}</strong><br>"
            '<small style="color: #6c757d;">Gateway: {}</small>'
            "</div>",
            obj.id,
            obj.gateway_refund_id or "Pending",
        )

    refund_info.short_description = "Refund"

    def donation_link(self, obj):
        """Display donation as link"""
        return format_html(
            '<a href="/admin/donations/donation/{}/change/" style="color: #007bff;">#{}</a>',
            obj.donation.id,
            obj.donation.id,
        )

    donation_link.short_description = "Donation"

    def amount_display(self, obj):
        """Display refund amount"""
        return format_html(
            '<span style="font-weight: bold; color: #dc3545;">NPR {}</span>',
            f"{obj.amount:,.0f}",
        )

    amount_display.short_description = "Amount"

    def reason_badge(self, obj):
        """Display reason with badge"""
        colors = {
            "duplicate_payment": "#ffc107",
            "case_cancelled": "#dc3545",
            "technical_error": "#17a2b8",
            "user_request": "#6c757d",
            "other": "#6c757d",
        }
        color = colors.get(obj.reason, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_reason_display().upper(),
        )

    reason_badge.short_description = "Reason"

    def status_badge(self, obj):
        """Display status with badge"""
        colors = {
            "requested": "#ffc107",
            "approved": "#28a745",
            "rejected": "#dc3545",
            "processing": "#17a2b8",
            "completed": "#28a745",
            "failed": "#dc3545",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display().upper(),
        )

    status_badge.short_description = "Status"

    def approve_refunds(self, request, queryset):
        """Approve selected refund requests"""
        updated = queryset.filter(status="requested").update(
            status="approved", approved_by=request.user
        )
        self.message_user(request, f"✅ {updated} refund requests approved.")

    approve_refunds.short_description = "✅ Approve refunds"

    def reject_refunds(self, request, queryset):
        """Reject selected refund requests"""
        updated = queryset.filter(status="requested").update(
            status="rejected", approved_by=request.user
        )
        self.message_user(request, f"❌ {updated} refund requests rejected.")

    reject_refunds.short_description = "❌ Reject refunds"
