from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from unfold.admin import ModelAdmin
from unfold.decorators import display

from charity_backend.admin import admin_site
from .models import PaymentGateway, PaymentIntent, PaymentWebhook, RefundRequest


class PaymentGatewayAdmin(ModelAdmin):
    """Admin configuration for PaymentGateway model"""

    # Unfold specific settings
    compressed_fields = True
    warn_unsaved_form = True

    list_display = ("name_badge", "status_badge", "api_url", "created_at")
    list_filter = ("name", "is_active", "created_at")
    search_fields = ("name", "merchant_code", "api_url")
    ordering = ("name",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Gateway Information", {"fields": ("name", "is_active"), "classes": ("tab",)}),
        (
            "Configuration",
            {
                "fields": ("merchant_code", "secret_key", "public_key", "api_url"),
                "classes": ("tab",),
            },
        ),
        ("URLs", {"fields": ("success_url", "failure_url"), "classes": ("tab",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("tab",)}),
    )

    @display(description="Gateway", ordering="name")
    def name_badge(self, obj):
        """Display gateway name with icon"""
        gateway_icons = {
            "esewa": "💳",
            "khalti": "📱",
            "imepay": "🏦",
        }

        icon = gateway_icons.get(obj.name, "💰")

        return format_html(
            '<div class="flex items-center space-x-2">'
            '<span class="text-lg">{}</span>'
            '<span class="font-semibold">{}</span>'
            "</div>",
            icon,
            obj.get_name_display(),
        )

    @display(description="Status", boolean=True, ordering="is_active")
    def status_badge(self, obj):
        """Display active status"""
        if obj.is_active:
            return format_html(
                '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">'
                "✅ Active"
                "</span>"
            )
        return format_html(
            '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">'
            "❌ Inactive"
            "</span>"
        )


class PaymentIntentAdmin(ModelAdmin):
    """Admin configuration for PaymentIntent model"""

    # Unfold specific settings
    compressed_fields = True
    list_select_related = True
    warn_unsaved_form = True

    list_display = (
        "intent_id",
        "donation_info",
        "gateway_name",
        "amount_display",
        "status_badge",
        "expiry_status",
        "created_at",
    )
    list_filter = (
        "status",
        "gateway__name",
        ("created_at", admin.DateFieldListFilter),
        ("expires_at", admin.DateFieldListFilter),
    )
    search_fields = ("id", "gateway_payment_id", "donation__payment_reference")
    ordering = ("-created_at",)
    readonly_fields = (
        "id",
        "created_at",
        "processed_at",
        "is_expired",
        "is_successful",
    )

    fieldsets = (
        (
            "Payment Intent",
            {
                "fields": ("id", "donation", "gateway", "amount", "currency", "status"),
                "classes": ("tab",),
            },
        ),
        (
            "Gateway Information",
            {"fields": ("gateway_payment_id", "gateway_response"), "classes": ("tab",)},
        ),
        ("QR Code", {"fields": ("qr_code_data", "qr_code_image"), "classes": ("tab",)}),
        ("URLs", {"fields": ("return_url", "cancel_url"), "classes": ("tab",)}),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "expires_at",
                    "processed_at",
                    "is_expired",
                    "is_successful",
                ),
                "classes": ("tab",),
            },
        ),
        (
            "Metadata",
            {"fields": ("client_ip", "user_agent"), "classes": ("tab", "collapse")},
        ),
    )

    @display(description="Intent ID", ordering="id")
    def intent_id(self, obj):
        """Display payment intent ID"""
        return format_html(
            '<span class="font-mono text-sm">{}</span>', str(obj.id)[:8] + "..."
        )

    @display(description="Donation", ordering="donation__id")
    def donation_info(self, obj):
        """Display donation information"""
        return format_html(
            '<div class="flex flex-col">'
            '<a href="/admin/donations/donation/{}/change/" class="text-blue-600 hover:text-blue-800 font-medium">#{}</a>'
            '<span class="text-sm text-gray-500">{}</span>'
            "</div>",
            obj.donation.id,
            obj.donation.id,
            (
                obj.donation.case.title[:30] + "..."
                if len(obj.donation.case.title) > 30
                else obj.donation.case.title
            ),
        )

    @display(description="Gateway", ordering="gateway__name")
    def gateway_name(self, obj):
        """Display gateway name"""
        gateway_icons = {
            "esewa": "💳",
            "khalti": "📱",
            "imepay": "🏦",
        }

        icon = gateway_icons.get(obj.gateway.name, "💰")

        return format_html(
            '<div class="flex items-center space-x-1">'
            "<span>{}</span>"
            '<span class="text-sm font-medium">{}</span>'
            "</div>",
            icon,
            obj.gateway.get_name_display(),
        )

    @display(description="Amount", ordering="amount")
    def amount_display(self, obj):
        """Display amount with currency"""
        return format_html('<span class="font-semibold">NPR {:,.0f}</span>', obj.amount)

    @display(description="Status", ordering="status")
    def status_badge(self, obj):
        """Display status with colored badge"""
        status_config = {
            "created": {"color": "bg-blue-100 text-blue-800", "icon": "🆕"},
            "processing": {"color": "bg-yellow-100 text-yellow-800", "icon": "⏳"},
            "succeeded": {"color": "bg-green-100 text-green-800", "icon": "✅"},
            "failed": {"color": "bg-red-100 text-red-800", "icon": "❌"},
            "cancelled": {"color": "bg-gray-100 text-gray-800", "icon": "🚫"},
        }

        config = status_config.get(obj.status, status_config["created"])

        return format_html(
            '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {}">'
            '<span class="mr-1">{}</span>{}'
            "</span>",
            config["color"],
            config["icon"],
            obj.get_status_display(),
        )

    @display(description="Expiry", ordering="expires_at")
    def expiry_status(self, obj):
        """Display expiry status"""
        from django.utils import timezone

        if obj.is_expired:
            return format_html(
                '<span class="text-red-600 font-semibold">Expired</span>'
            )

        remaining = obj.expires_at - timezone.now()
        hours = remaining.total_seconds() / 3600

        if hours < 1:
            return format_html(
                '<span class="text-orange-600">{}min</span>',
                int(remaining.total_seconds() / 60),
            )
        elif hours < 24:
            return format_html('<span class="text-yellow-600">{:.1f}h</span>', hours)
        else:
            return format_html(
                '<span class="text-green-600">{} days</span>', remaining.days
            )


class PaymentWebhookAdmin(ModelAdmin):
    """Admin configuration for PaymentWebhook model"""

    # Unfold specific settings
    compressed_fields = True
    list_select_related = True
    warn_unsaved_form = True

    list_display = (
        "webhook_id",
        "gateway_name",
        "event_badge",
        "processing_status",
        "received_at",
    )
    list_filter = ("event_type", "gateway__name", "processed", "received_at")
    search_fields = ("webhook_id", "event_type", "payment_intent__id")
    ordering = ("-received_at",)
    readonly_fields = ("received_at", "processed_at")

    fieldsets = (
        (
            "Webhook Information",
            {
                "fields": ("gateway", "event_type", "webhook_id", "payment_intent"),
                "classes": ("tab",),
            },
        ),
        (
            "Processing",
            {"fields": ("processed", "processing_error"), "classes": ("tab",)},
        ),
        ("Data", {"fields": ("raw_data",), "classes": ("tab",)}),
        (
            "Timestamps",
            {"fields": ("received_at", "processed_at"), "classes": ("tab",)},
        ),
    )

    @display(description="Gateway", ordering="gateway__name")
    def gateway_name(self, obj):
        """Display gateway name"""
        gateway_icons = {
            "esewa": "💳",
            "khalti": "📱",
            "imepay": "🏦",
        }

        icon = gateway_icons.get(obj.gateway.name, "💰")

        return format_html(
            '<div class="flex items-center space-x-1">'
            "<span>{}</span>"
            '<span class="text-sm font-medium">{}</span>'
            "</div>",
            icon,
            obj.gateway.get_name_display(),
        )

    @display(description="Event", ordering="event_type")
    def event_badge(self, obj):
        """Display event type with badge"""
        event_config = {
            "payment.completed": {"color": "bg-green-100 text-green-800", "icon": "✅"},
            "payment.failed": {"color": "bg-red-100 text-red-800", "icon": "❌"},
            "payment.cancelled": {"color": "bg-gray-100 text-gray-800", "icon": "🚫"},
            "refund.completed": {"color": "bg-purple-100 text-purple-800", "icon": "↩️"},
        }

        config = event_config.get(
            obj.event_type, {"color": "bg-blue-100 text-blue-800", "icon": "📡"}
        )

        return format_html(
            '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {}">'
            '<span class="mr-1">{}</span>{}'
            "</span>",
            config["color"],
            config["icon"],
            obj.get_event_type_display(),
        )

    @display(description="Processing", boolean=True, ordering="processed")
    def processing_status(self, obj):
        """Display processing status"""
        if obj.processed:
            return format_html(
                '<span class="inline-flex items-center text-green-600">'
                "✅ Processed"
                "</span>"
            )
        return format_html(
            '<span class="inline-flex items-center text-yellow-600">'
            "⏳ Pending"
            "</span>"
        )


class RefundRequestAdmin(ModelAdmin):
    """Admin configuration for RefundRequest model"""

    # Unfold specific settings
    compressed_fields = True
    list_select_related = True
    warn_unsaved_form = True

    list_display = (
        "refund_id",
        "donation_info",
        "amount_display",
        "reason_badge",
        "status_badge",
        "requester_info",
        "requested_at",
    )
    list_filter = (
        "status",
        "reason",
        ("requested_at", admin.DateFieldListFilter),
        "requested_by",
        "approved_by",
    )
    search_fields = ("donation__payment_reference", "description", "gateway_refund_id")
    ordering = ("-requested_at",)
    readonly_fields = ("requested_at", "processed_at")

    fieldsets = (
        (
            "Refund Information",
            {
                "fields": ("donation", "amount", "reason", "description", "status"),
                "classes": ("tab",),
            },
        ),
        (
            "Processing",
            {
                "fields": (
                    "requested_by",
                    "approved_by",
                    "gateway_refund_id",
                    "gateway_response",
                ),
                "classes": ("tab",),
            },
        ),
        (
            "Timestamps",
            {"fields": ("requested_at", "processed_at"), "classes": ("tab",)},
        ),
    )

    actions = ["approve_refunds", "reject_refunds", "mark_completed"]

    @display(description="Refund ID", ordering="id")
    def refund_id(self, obj):
        """Display refund ID"""
        return format_html('<span class="font-mono text-sm">#{}</span>', obj.id)

    @display(description="Donation", ordering="donation__id")
    def donation_info(self, obj):
        """Display donation information"""
        return format_html(
            '<div class="flex flex-col">'
            '<a href="/admin/donations/donation/{}/change/" class="text-blue-600 hover:text-blue-800 font-medium">Donation #{}</a>'
            '<span class="text-sm text-gray-500">{}</span>'
            "</div>",
            obj.donation.id,
            obj.donation.id,
            obj.donation.payment_reference,
        )

    @display(description="Amount", ordering="amount")
    def amount_display(self, obj):
        """Display refund amount"""
        return format_html(
            '<span class="font-semibold text-red-600">NPR {:,.0f}</span>', obj.amount
        )

    @display(description="Reason", ordering="reason")
    def reason_badge(self, obj):
        """Display refund reason"""
        reason_colors = {
            "duplicate_payment": "bg-yellow-100 text-yellow-800",
            "case_cancelled": "bg-red-100 text-red-800",
            "technical_error": "bg-orange-100 text-orange-800",
            "user_request": "bg-blue-100 text-blue-800",
            "other": "bg-gray-100 text-gray-800",
        }

        color = reason_colors.get(obj.reason, "bg-gray-100 text-gray-800")

        return format_html(
            '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {}">'
            "{}"
            "</span>",
            color,
            obj.get_reason_display(),
        )

    @display(description="Status", ordering="status")
    def status_badge(self, obj):
        """Display status with colored badge"""
        status_config = {
            "requested": {"color": "bg-yellow-100 text-yellow-800", "icon": "📋"},
            "approved": {"color": "bg-green-100 text-green-800", "icon": "✅"},
            "rejected": {"color": "bg-red-100 text-red-800", "icon": "❌"},
            "processing": {"color": "bg-blue-100 text-blue-800", "icon": "⏳"},
            "completed": {"color": "bg-purple-100 text-purple-800", "icon": "✨"},
            "failed": {"color": "bg-red-100 text-red-800", "icon": "💥"},
        }

        config = status_config.get(obj.status, status_config["requested"])

        return format_html(
            '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {}">'
            '<span class="mr-1">{}</span>{}'
            "</span>",
            config["color"],
            config["icon"],
            obj.get_status_display(),
        )

    @display(description="Requested By", ordering="requested_by__first_name")
    def requester_info(self, obj):
        """Display requester information"""
        name = (
            f"{obj.requested_by.first_name} {obj.requested_by.last_name}".strip()
            or obj.requested_by.username
        )
        return format_html(
            '<div class="flex items-center space-x-2">'
            '<div class="w-6 h-6 bg-blue-100 text-blue-800 rounded-full flex items-center justify-center text-xs font-semibold">'
            "{}"
            "</div>"
            '<span class="text-sm font-medium">{}</span>'
            "</div>",
            name[0].upper(),
            name,
        )

    # Admin actions
    @admin.action(description="✅ Approve selected refunds")
    def approve_refunds(self, request, queryset):
        updated = queryset.update(status="approved", approved_by=request.user)
        self.message_user(request, f"✅ {updated} refund requests approved.")

    @admin.action(description="❌ Reject selected refunds")
    def reject_refunds(self, request, queryset):
        updated = queryset.update(status="rejected", approved_by=request.user)
        self.message_user(request, f"❌ {updated} refund requests rejected.")

    @admin.action(description="✨ Mark as completed")
    def mark_completed(self, request, queryset):
        from django.utils import timezone

        updated = queryset.update(status="completed", processed_at=timezone.now())
        self.message_user(request, f"✨ {updated} refunds marked as completed.")


# Register with custom admin site
admin_site.register(PaymentGateway, PaymentGatewayAdmin)
admin_site.register(PaymentIntent, PaymentIntentAdmin)
admin_site.register(PaymentWebhook, PaymentWebhookAdmin)
admin_site.register(RefundRequest, RefundRequestAdmin)
