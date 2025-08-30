"""
Serializers for recommendations app
"""

from rest_framework import serializers

from cases.models import CharityCase

from .models import (
    CaseFeatures,
    RecommendationFeedback,
    RecommendationHistory,
    RecommendationModel,
    SearchQuery,
    UserProfile,
)


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model"""

    user_email = serializers.CharField(source="user.email", read_only=True)
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "user_email",
            "user_name",
            "age_range",
            "income_range",
            "preferred_categories",
            "donation_frequency",
            "avg_donation_amount",
            "total_donations",
            "total_donated",
            "cluster_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user_email",
            "user_name",
            "avg_donation_amount",
            "total_donations",
            "total_donated",
            "cluster_id",
            "created_at",
            "updated_at",
        ]

    def validate_preferred_categories(self, value):
        """Validate preferred categories"""
        valid_categories = [
            "health",
            "education",
            "disaster_relief",
            "poverty",
            "environment",
            "animal_welfare",
        ]
        if value:
            for category in value:
                if category not in valid_categories:
                    raise serializers.ValidationError(f"Invalid category: {category}")
        return value


class RecommendationHistorySerializer(serializers.ModelSerializer):
    """Serializer for RecommendationHistory model"""

    case_title = serializers.CharField(source="case.title", read_only=True)
    case_category = serializers.CharField(source="case.category", read_only=True)
    case_target_amount = serializers.DecimalField(
        source="case.target_amount", max_digits=10, decimal_places=2, read_only=True
    )
    case_collected_amount = serializers.DecimalField(
        source="case.collected_amount", max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = RecommendationHistory
        fields = [
            "id",
            "case",
            "case_title",
            "case_category",
            "case_target_amount",
            "case_collected_amount",
            "algorithm_used",
            "recommendation_score",
            "clicked",
            "clicked_at",
            "donated",
            "donated_at",
            "shared",
            "shared_at",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class SearchQuerySerializer(serializers.ModelSerializer):
    """Serializer for SearchQuery model"""

    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = SearchQuery
        fields = [
            "id",
            "user_email",
            "query",
            "category_filter",
            "location_filter",
            "results_count",
            "clicked_case",
            "created_at",
        ]
        read_only_fields = ["id", "user_email", "created_at"]


class RecommendationModelSerializer(serializers.ModelSerializer):
    """Serializer for RecommendationModel model"""

    class Meta:
        model = RecommendationModel
        fields = [
            "id",
            "name",
            "model_type",
            "version",
            "parameters",
            "features",
            "accuracy",
            "precision",
            "recall",
            "f1_score",
            "is_active",
            "training_date",
            "last_used",
        ]
        read_only_fields = ["id", "training_date"]


class CaseFeaturesSerializer(serializers.ModelSerializer):
    """Serializer for CaseFeatures model"""

    case_title = serializers.CharField(source="case.title", read_only=True)

    class Meta:
        model = CaseFeatures
        fields = [
            "id",
            "case",
            "case_title",
            "urgency_score",
            "completion_ratio",
            "donor_count",
            "avg_donation",
            "days_active",
            "share_count",
            "view_count",
            "last_updated",
        ]
        read_only_fields = ["id", "case_title", "last_updated"]


class RecommendationFeedbackSerializer(serializers.ModelSerializer):
    """Serializer for RecommendationFeedback model"""

    user_email = serializers.CharField(source="user.email", read_only=True)
    case_title = serializers.CharField(source="case.title", read_only=True)

    class Meta:
        model = RecommendationFeedback
        fields = [
            "id",
            "user_email",
            "case",
            "case_title",
            "recommendation_history",
            "feedback_type",
            "comment",
            "created_at",
        ]
        read_only_fields = ["id", "user_email", "case_title", "created_at"]
