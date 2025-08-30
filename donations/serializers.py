from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Donation

User = get_user_model()


class DonationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating donations"""

    class Meta:
        model = Donation
        fields = (
            "case",
            "amount",
            "payment_method",
            "is_anonymous",
            "donor_name",
            "donor_email",
            "donor_message",
        )
        extra_kwargs = {
            "amount": {"min_value": Decimal("1.00")},
            "payment_method": {"required": True},
        }

    def validate_case(self, value):
        """Validate that case is active and approved"""
        if not value.is_active:
            raise serializers.ValidationError("This case is not active for donations.")
        return value

    def validate_donor_email(self, value):
        """Validate donor email for anonymous donations"""
        # Check if this is an anonymous donation from the validated data
        is_anonymous = getattr(self, "_validated_data", {}).get("is_anonymous", False)
        if is_anonymous and not value:
            raise serializers.ValidationError(
                "Email is required for anonymous donations."
            )
        return value

    def create(self, validated_data):
        """Create donation with donor information"""
        request = self.context["request"]
        validated_data["donor"] = request.user

        # Generate unique payment reference
        import uuid

        validated_data["payment_reference"] = f"DN{uuid.uuid4().hex[:12].upper()}"

        # Store IP and User Agent for security
        validated_data["ip_address"] = self.get_client_ip(request)
        validated_data["user_agent"] = request.META.get("HTTP_USER_AGENT", "")

        return super().create(validated_data)

    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0]
        return request.META.get("REMOTE_ADDR")


class DonationPublicSerializer(serializers.ModelSerializer):
    """Serializer for public donation display (without sensitive info)"""

    donor_display_name = serializers.ReadOnlyField()
    case_title = serializers.CharField(source="case.title", read_only=True)

    class Meta:
        model = Donation
        fields = (
            "id",
            "amount",
            "donor_display_name",
            "donor_message",
            "case_title",
            "created_at",
            "is_anonymous",
        )


class DonationListSerializer(serializers.ModelSerializer):
    """Serializer for donation list view"""

    donor_display_name = serializers.ReadOnlyField()
    case_title = serializers.CharField(source="case.title", read_only=True)
    case_slug = serializers.CharField(source="case.slug", read_only=True)

    class Meta:
        model = Donation
        fields = (
            "id",
            "amount",
            "payment_method",
            "payment_reference",
            "status",
            "donor_display_name",
            "donor_message",
            "case_title",
            "case_slug",
            "created_at",
            "completed_at",
            "is_anonymous",
        )


class DonationDetailSerializer(serializers.ModelSerializer):
    """Serializer for donation detail view"""

    case_details = serializers.SerializerMethodField()
    donor_info = serializers.SerializerMethodField()

    class Meta:
        model = Donation
        fields = (
            "id",
            "amount",
            "payment_method",
            "payment_reference",
            "transaction_id",
            "status",
            "donor_message",
            "created_at",
            "completed_at",
            "is_anonymous",
            "case_details",
            "donor_info",
        )

    def get_case_details(self, obj):
        """Get case details"""
        return {
            "id": obj.case.id,
            "title": obj.case.title,
            "slug": obj.case.slug,
            "category": obj.case.category,
            "verification_status": obj.case.verification_status,
        }

    def get_donor_info(self, obj):
        """Get donor information (respecting privacy)"""
        request = self.context.get("request")
        if not request:
            return None

        # Only show full details to the donor themselves or admin
        if request.user == obj.donor or request.user.is_admin_user:
            return {
                "name": obj.donor_display_name,
                "email": obj.donor_email or obj.donor.email,
                "is_anonymous": obj.is_anonymous,
            }

        return {
            "name": obj.donor_display_name if not obj.is_anonymous else "Anonymous",
            "is_anonymous": obj.is_anonymous,
        }


class DonationHistorySerializer(serializers.ModelSerializer):
    """Serializer for donor's donation history"""

    case_title = serializers.CharField(source="case.title", read_only=True)
    case_slug = serializers.CharField(source="case.slug", read_only=True)
    case_category = serializers.CharField(source="case.category", read_only=True)
    case_status = serializers.CharField(
        source="case.verification_status", read_only=True
    )

    class Meta:
        model = Donation
        fields = (
            "id",
            "amount",
            "payment_method",
            "payment_reference",
            "status",
            "donor_message",
            "created_at",
            "completed_at",
            "case_title",
            "case_slug",
            "case_category",
            "case_status",
            "is_anonymous",
        )


class DonationStatsSerializer(serializers.Serializer):
    """Serializer for donation statistics"""

    total_donations = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    average_donation = serializers.DecimalField(max_digits=10, decimal_places=2)
    successful_donations = serializers.IntegerField()
    pending_donations = serializers.IntegerField()
    failed_donations = serializers.IntegerField()

    # Category breakdown
    category_stats = serializers.DictField()

    # Recent activity
    recent_donations = DonationListSerializer(many=True)

    # Monthly trends (for charts)
    monthly_trends = serializers.ListField()


class BulkDonationUpdateSerializer(serializers.Serializer):
    """Serializer for bulk donation status updates (admin only)"""

    donation_ids = serializers.ListField(
        child=serializers.IntegerField(), allow_empty=False
    )
    status = serializers.ChoiceField(choices=Donation.STATUS_CHOICES)

    def validate_donation_ids(self, value):
        """Validate that all donation IDs exist"""
        existing_ids = Donation.objects.filter(id__in=value).values_list(
            "id", flat=True
        )
        missing_ids = set(value) - set(existing_ids)
        if missing_ids:
            raise serializers.ValidationError(
                f"Donations with IDs {list(missing_ids)} do not exist."
            )
        return value
