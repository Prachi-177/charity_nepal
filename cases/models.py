from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

User = get_user_model()


class CharityCase(models.Model):
    """Model for charity cases"""

    CATEGORY_CHOICES = [
        ("cancer", "Cancer Treatment"),
        ("accident", "Accident Support"),
        ("acid_attack", "Acid Attack Recovery"),
        ("education", "Education Support"),
        ("disaster", "Disaster Relief"),
        ("medical", "General Medical"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending Verification"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    URGENCY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    target_amount = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(100)]
    )
    collected_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    verification_status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    urgency_flag = models.CharField(
        max_length=10, choices=URGENCY_CHOICES, default="medium"
    )
    location = models.CharField(max_length=100, blank=True, null=True)
    beneficiary_name = models.CharField(max_length=100)
    beneficiary_age = models.PositiveIntegerField(blank=True, null=True)
    contact_phone = models.CharField(max_length=15)
    contact_email = models.EmailField()

    # File uploads
    featured_image = models.ImageField(upload_to="cases/images/", blank=True, null=True)
    documents = models.FileField(upload_to="cases/documents/", blank=True, null=True)

    # Metadata
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_cases"
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_cases",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deadline = models.DateTimeField(blank=True, null=True)

    # SEO and search
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    tags = models.CharField(
        max_length=500, blank=True, help_text="Comma-separated tags"
    )

    class Meta:
        db_table = "charity_cases"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["category"]),
            models.Index(fields=["verification_status"]),
            models.Index(fields=["urgency_flag"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return self.title

    @property
    def completion_percentage(self):
        if self.target_amount > 0:
            return min((self.collected_amount / self.target_amount) * 100, 100)
        return 0

    @property
    def is_completed(self):
        return self.collected_amount >= self.target_amount

    @property
    def is_active(self):
        return self.verification_status == "approved" and not self.is_completed

    @property
    def days_remaining(self):
        if self.deadline:
            remaining = self.deadline - timezone.now()
            return remaining.days if remaining.days > 0 else 0
        return None

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify

            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while CharityCase.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class CaseUpdate(models.Model):
    """Model for case updates/progress reports"""

    case = models.ForeignKey(
        CharityCase, on_delete=models.CASCADE, related_name="updates"
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to="cases/updates/", blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "case_updates"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.case.title} - {self.title}"
