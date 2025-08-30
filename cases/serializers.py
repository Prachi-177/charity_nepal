from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import CaseUpdate, CharityCase

User = get_user_model()


class CharityCaseListSerializer(serializers.ModelSerializer):
    """Serializer for charity case list view"""

    completion_percentage = serializers.ReadOnlyField()
    days_remaining = serializers.ReadOnlyField()
    is_completed = serializers.ReadOnlyField()
    created_by_name = serializers.SerializerMethodField()
    donation_count = serializers.SerializerMethodField()

    class Meta:
        model = CharityCase
        fields = (
            "id",
            "title",
            "slug",
            "description",
            "category",
            "target_amount",
            "collected_amount",
            "completion_percentage",
            "verification_status",
            "urgency_flag",
            "location",
            "beneficiary_name",
            "featured_image",
            "created_at",
            "deadline",
            "days_remaining",
            "is_completed",
            "created_by_name",
            "donation_count",
        )

    def get_created_by_name(self, obj):
        """Get creator's display name"""
        if obj.created_by:
            return (
                f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
                or obj.created_by.username
            )
        return "Unknown"

    def get_donation_count(self, obj):
        """Get number of donations for this case"""
        return obj.donations.filter(status="completed").count()


class CharityCaseDetailSerializer(serializers.ModelSerializer):
    """Serializer for charity case detail view"""

    completion_percentage = serializers.ReadOnlyField()
    days_remaining = serializers.ReadOnlyField()
    is_completed = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    created_by_name = serializers.SerializerMethodField()
    donation_count = serializers.SerializerMethodField()
    recent_donations = serializers.SerializerMethodField()
    updates = serializers.SerializerMethodField()

    class Meta:
        model = CharityCase
        fields = (
            "id",
            "title",
            "slug",
            "description",
            "category",
            "target_amount",
            "collected_amount",
            "completion_percentage",
            "verification_status",
            "urgency_flag",
            "location",
            "beneficiary_name",
            "beneficiary_age",
            "contact_phone",
            "contact_email",
            "featured_image",
            "documents",
            "tags",
            "created_at",
            "updated_at",
            "deadline",
            "days_remaining",
            "is_completed",
            "is_active",
            "created_by_name",
            "donation_count",
            "recent_donations",
            "updates",
        )

    def get_created_by_name(self, obj):
        """Get creator's display name"""
        if obj.created_by:
            return (
                f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
                or obj.created_by.username
            )
        return "Unknown"

    def get_donation_count(self, obj):
        """Get number of donations for this case"""
        return obj.donations.filter(status="completed").count()

    def get_recent_donations(self, obj):
        """Get recent donations for this case"""
        from donations.serializers import DonationPublicSerializer

        recent_donations = obj.donations.filter(status="completed").order_by(
            "-created_at"
        )[:5]
        return DonationPublicSerializer(recent_donations, many=True).data

    def get_updates(self, obj):
        """Get case updates"""
        updates = obj.updates.all().order_by("-created_at")[:10]
        return CaseUpdateSerializer(updates, many=True).data


class CharityCaseCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating charity cases"""

    class Meta:
        model = CharityCase
        fields = (
            "title",
            "description",
            "category",
            "target_amount",
            "urgency_flag",
            "location",
            "beneficiary_name",
            "beneficiary_age",
            "contact_phone",
            "contact_email",
            "featured_image",
            "documents",
            "tags",
            "deadline",
        )
        extra_kwargs = {
            "target_amount": {"min_value": 100},
            "contact_phone": {"required": True},
            "contact_email": {"required": True},
        }

    def create(self, validated_data):
        """Create charity case"""
        validated_data["created_by"] = self.context["request"].user
        validated_data["verification_status"] = "pending"
        return super().create(validated_data)


class CharityCaseUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating charity cases"""

    class Meta:
        model = CharityCase
        fields = (
            "title",
            "description",
            "target_amount",
            "urgency_flag",
            "location",
            "beneficiary_name",
            "beneficiary_age",
            "contact_phone",
            "contact_email",
            "featured_image",
            "documents",
            "tags",
            "deadline",
        )
        extra_kwargs = {
            "target_amount": {"min_value": 100},
        }

    def validate_target_amount(self, value):
        """Validate target amount - can't be less than collected amount"""
        if self.instance and value < self.instance.collected_amount:
            raise serializers.ValidationError(
                "Target amount cannot be less than already collected amount."
            )
        return value


class CharityCaseStatusSerializer(serializers.ModelSerializer):
    """Serializer for updating case status (admin only)"""

    class Meta:
        model = CharityCase
        fields = ("verification_status", "urgency_flag")

    def update(self, instance, validated_data):
        """Update case status"""
        if "verification_status" in validated_data:
            instance.approved_by = self.context["request"].user
        return super().update(instance, validated_data)


class CaseUpdateSerializer(serializers.ModelSerializer):
    """Serializer for case updates"""

    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = CaseUpdate
        fields = (
            "id",
            "title",
            "description",
            "image",
            "created_by_name",
            "created_at",
        )
        read_only_fields = ("id", "created_by_name", "created_at")

    def get_created_by_name(self, obj):
        """Get creator's display name"""
        if obj.created_by:
            return (
                f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
                or obj.created_by.username
            )
        return "Unknown"


class CaseUpdateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating case updates"""

    class Meta:
        model = CaseUpdate
        fields = ("case", "title", "description", "image")

    def create(self, validated_data):
        """Create case update"""
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class CharityCaseSearchSerializer(serializers.Serializer):
    """Serializer for case search parameters"""

    q = serializers.CharField(required=False, allow_blank=True)
    category = serializers.ChoiceField(
        choices=CharityCase.CATEGORY_CHOICES, required=False, allow_blank=True
    )
    location = serializers.CharField(required=False, allow_blank=True)
    min_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, min_value=0
    )
    max_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, min_value=0
    )
    urgency = serializers.ChoiceField(
        choices=CharityCase.URGENCY_CHOICES, required=False, allow_blank=True
    )
    status = serializers.ChoiceField(
        choices=[("active", "Active"), ("completed", "Completed")],
        required=False,
        allow_blank=True,
    )
    ordering = serializers.ChoiceField(
        choices=[
            ("created_at", "Newest First"),
            ("-created_at", "Oldest First"),
            ("target_amount", "Amount Low to High"),
            ("-target_amount", "Amount High to Low"),
            ("urgency_flag", "Urgency"),
            ("-completion_percentage", "Near Completion"),
        ],
        required=False,
        default="-created_at",
    )
