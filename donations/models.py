from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()


class Donation(models.Model):
    """Model for donations made to charity cases"""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ("khalti", "Khalti"),
        ("bank_transfer", "Bank Transfer"),
        ("cash", "Cash"),
    ]

    donor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="donations")
    case = models.ForeignKey(
        "cases.CharityCase", on_delete=models.CASCADE, related_name="donations"
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("1.00"))]
    )
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_reference = models.CharField(max_length=100, unique=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Additional fields for anonymous donations
    is_anonymous = models.BooleanField(default=False)
    donor_name = models.CharField(max_length=100, blank=True, null=True)
    donor_email = models.EmailField(blank=True, null=True)
    donor_message = models.TextField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    # Metadata
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "donations"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["donor"]),
            models.Index(fields=["case"]),
            models.Index(fields=["status"]),
            models.Index(fields=["payment_method"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.donor.email if not self.is_anonymous else 'Anonymous'} - {self.amount} to {self.case.title}"

    @property
    def donor_display_name(self):
        if self.is_anonymous:
            return "Anonymous Donor"
        return (
            self.donor_name or f"{self.donor.first_name} {self.donor.last_name}".strip()
        )
