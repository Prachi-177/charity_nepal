import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class PaymentGateway(models.Model):
    """Model to store payment gateway configurations"""

    GATEWAY_CHOICES = [
        ("esewa", "eSewa"),
        ("khalti", "Khalti"),
        ("imepay", "IMEPay"),
    ]

    name = models.CharField(max_length=20, choices=GATEWAY_CHOICES, unique=True)
    is_active = models.BooleanField(default=True)
    merchant_code = models.CharField(max_length=100)
    secret_key = models.CharField(max_length=255)
    public_key = models.CharField(max_length=255, blank=True, null=True)
    api_url = models.URLField()
    success_url = models.URLField(blank=True, null=True)
    failure_url = models.URLField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payment_gateways"

    def __str__(self):
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"


class PaymentIntent(models.Model):
    """Model to track payment intents before actual payment"""

    STATUS_CHOICES = [
        ("created", "Created"),
        ("processing", "Processing"),
        ("succeeded", "Succeeded"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    donation = models.OneToOneField(
        "donations.Donation", on_delete=models.CASCADE, related_name="payment_intent"
    )
    gateway = models.ForeignKey(PaymentGateway, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="NPR")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="created")

    # Gateway specific fields
    gateway_payment_id = models.CharField(max_length=100, blank=True, null=True)
    gateway_response = models.JSONField(default=dict, blank=True)

    # QR Code for payment
    qr_code_data = models.TextField(blank=True, null=True)
    qr_code_image = models.ImageField(upload_to="qr_codes/", blank=True, null=True)

    # URLs
    return_url = models.URLField()
    cancel_url = models.URLField()

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    processed_at = models.DateTimeField(blank=True, null=True)

    # Metadata
    client_ip = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "payment_intents"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment Intent {self.id} - {self.amount} {self.currency}"

    @property
    def is_expired(self):
        from django.utils import timezone

        return timezone.now() > self.expires_at

    @property
    def is_successful(self):
        return self.status == "succeeded"


class PaymentWebhook(models.Model):
    """Model to log payment webhook events"""

    EVENT_TYPES = [
        ("payment.completed", "Payment Completed"),
        ("payment.failed", "Payment Failed"),
        ("payment.cancelled", "Payment Cancelled"),
        ("refund.completed", "Refund Completed"),
    ]

    gateway = models.ForeignKey(PaymentGateway, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    webhook_id = models.CharField(max_length=100, unique=True)
    payment_intent = models.ForeignKey(
        PaymentIntent, on_delete=models.CASCADE, blank=True, null=True
    )

    # Raw webhook data
    raw_data = models.JSONField()
    processed = models.BooleanField(default=False)
    processing_error = models.TextField(blank=True, null=True)

    # Timestamps
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "payment_webhooks"
        ordering = ["-received_at"]

    def __str__(self):
        return f"Webhook {self.webhook_id} - {self.event_type}"


class RefundRequest(models.Model):
    """Model for refund requests"""

    STATUS_CHOICES = [
        ("requested", "Requested"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    REASON_CHOICES = [
        ("duplicate_payment", "Duplicate Payment"),
        ("case_cancelled", "Case Cancelled"),
        ("technical_error", "Technical Error"),
        ("user_request", "User Request"),
        ("other", "Other"),
    ]

    donation = models.ForeignKey(
        "donations.Donation", on_delete=models.CASCADE, related_name="refunds"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="requested"
    )

    # Processing info
    requested_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="refund_requests"
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_refunds",
    )

    # Gateway response
    gateway_refund_id = models.CharField(max_length=100, blank=True, null=True)
    gateway_response = models.JSONField(default=dict, blank=True)

    # Timestamps
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "refund_requests"
        ordering = ["-requested_at"]

    def __str__(self):
        return f"Refund Request for {self.donation.id} - {self.amount} NPR"
