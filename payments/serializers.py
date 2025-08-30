"""
Serializers for payments app
"""

from rest_framework import serializers

from .models import PaymentIntent


class PaymentIntentSerializer(serializers.ModelSerializer):
    """Serializer for PaymentIntent model"""

    donation_title = serializers.CharField(source="donation.case.title", read_only=True)
    donor_name = serializers.CharField(
        source="donation.donor.get_full_name", read_only=True
    )

    class Meta:
        model = PaymentIntent
        fields = [
            "id",
            "donation",
            "donation_title",
            "donor_name",
            "payment_method",
            "amount",
            "currency",
            "status",
            "gateway_response",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "gateway_response"]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value


class TransactionSerializer(serializers.Serializer):
    """Serializer for transaction data"""

    id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField(max_length=3)
    status = serializers.CharField(max_length=20)
    payment_method = serializers.CharField(max_length=20)
    created_at = serializers.DateTimeField()
    donation_id = serializers.IntegerField()
    case_title = serializers.CharField()
