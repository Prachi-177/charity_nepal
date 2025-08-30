import json
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class UserProfile(models.Model):
    """Extended user profile for recommendation system"""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    # Demographics
    age_range = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        choices=[
            ("18-25", "18-25"),
            ("26-35", "26-35"),
            ("36-45", "36-45"),
            ("46-55", "46-55"),
            ("55+", "55+"),
        ],
    )
    income_range = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=[
            ("low", "Low (< 50K)"),
            ("medium", "Medium (50K-200K)"),
            ("high", "High (200K+)"),
        ],
    )

    # Preferences
    preferred_categories = models.JSONField(default=list, blank=True)
    donation_frequency = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=[
            ("one_time", "One Time"),
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("yearly", "Yearly"),
        ],
    )

    # ML Features
    avg_donation_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    total_donations = models.PositiveIntegerField(default=0)
    total_donated = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    donation_pattern_vector = models.JSONField(default=list, blank=True)
    cluster_id = models.IntegerField(blank=True, null=True)

    # Activity tracking
    last_login = models.DateTimeField(blank=True, null=True)
    last_donation = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_profiles"

    def __str__(self):
        return f"Profile for {self.user.email}"

    def update_donation_stats(self):
        """Update donation statistics"""
        from django.db.models import Avg, Count, Sum

        from donations.models import Donation

        stats = self.user.donations.filter(status="completed").aggregate(
            total=Sum("amount"), count=Count("id"), avg=Avg("amount")
        )

        self.total_donated = stats["total"] or 0
        self.total_donations = stats["count"] or 0
        self.avg_donation_amount = stats["avg"] or 0
        self.save()


class RecommendationHistory(models.Model):
    """Track recommendation history and user interactions"""

    ALGORITHM_CHOICES = [
        ("content", "Content-Based"),
        ("collaborative", "Collaborative Filtering"),
        ("clustering", "Clustering-Based"),
        ("decision_tree", "Decision Tree"),
        ("hybrid", "Hybrid Algorithm"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="recommendation_history"
    )
    case = models.ForeignKey("cases.CharityCase", on_delete=models.CASCADE)
    algorithm_used = models.CharField(max_length=20, choices=ALGORITHM_CHOICES)
    recommendation_score = models.FloatField()

    # Interaction tracking
    clicked = models.BooleanField(default=False)
    clicked_at = models.DateTimeField(blank=True, null=True)
    donated = models.BooleanField(default=False)
    donated_at = models.DateTimeField(blank=True, null=True)
    shared = models.BooleanField(default=False)
    shared_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "recommendation_history"
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["algorithm_used"]),
        ]

    def __str__(self):
        return f"{self.user.email} -> {self.case.title} ({self.algorithm_used})"


class RecommendationModel(models.Model):
    """Model to store trained ML models"""

    MODEL_TYPES = [
        ("content_based", "Content-Based Filtering"),
        ("collaborative", "Collaborative Filtering"),
        ("kmeans", "K-Means Clustering"),
        ("decision_tree", "Decision Tree"),
        ("naive_bayes", "Naive Bayes"),
    ]

    name = models.CharField(max_length=50)
    model_type = models.CharField(max_length=20, choices=MODEL_TYPES)
    version = models.CharField(max_length=10, default="1.0")

    # Model storage (serialized model)
    model_data = models.BinaryField()
    parameters = models.JSONField(default=dict)
    features = models.JSONField(default=list)

    # Performance metrics
    accuracy = models.FloatField(blank=True, null=True)
    precision = models.FloatField(blank=True, null=True)
    recall = models.FloatField(blank=True, null=True)
    f1_score = models.FloatField(blank=True, null=True)

    # Status
    is_active = models.BooleanField(default=False)
    training_date = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "recommendation_models"
        unique_together = ["name", "version"]

    def __str__(self):
        return f"{self.name} v{self.version} ({self.model_type})"


class CaseFeatures(models.Model):
    """Pre-computed features for charity cases used in ML models"""

    case = models.OneToOneField(
        "cases.CharityCase", on_delete=models.CASCADE, related_name="features"
    )

    # Text features (TF-IDF vectors)
    title_vector = models.JSONField(default=list)
    description_vector = models.JSONField(default=list)

    # Numerical features
    urgency_score = models.FloatField(default=0.0)
    completion_ratio = models.FloatField(default=0.0)
    donor_count = models.PositiveIntegerField(default=0)
    avg_donation = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    days_active = models.PositiveIntegerField(default=0)

    # Category features (one-hot encoding)
    category_features = models.JSONField(default=dict)

    # Location features
    location_vector = models.JSONField(default=list)

    # Social features
    share_count = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)

    # Update tracking
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "case_features"

    def __str__(self):
        return f"Features for {self.case.title}"


class RecommendationFeedback(models.Model):
    """Model to collect user feedback on recommendations"""

    FEEDBACK_TYPES = [
        ("like", "Like"),
        ("dislike", "Dislike"),
        ("not_interested", "Not Interested"),
        ("irrelevant", "Irrelevant"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    case = models.ForeignKey("cases.CharityCase", on_delete=models.CASCADE)
    recommendation_history = models.ForeignKey(
        "RecommendationHistory", on_delete=models.CASCADE
    )

    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPES)
    comment = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "recommendation_feedback"
        unique_together = ["user", "case", "recommendation_history"]

    def __str__(self):
        return f"{self.user.email} - {self.feedback_type} - {self.case.title}"


class SearchQuery(models.Model):
    """Model to track search queries for analytics and improvement"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    query = models.CharField(max_length=500)
    category_filter = models.CharField(max_length=20, blank=True, null=True)
    location_filter = models.CharField(max_length=100, blank=True, null=True)

    # Results and user interaction
    results_count = models.PositiveIntegerField(default=0)
    clicked_case = models.ForeignKey(
        "cases.CharityCase", on_delete=models.SET_NULL, blank=True, null=True
    )

    # Search metadata
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "search_queries"
        indexes = [
            models.Index(fields=["query"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Search: {self.query} ({self.results_count} results)"


class UserRecommendation(models.Model):
    """Track recommendations shown to users and their interactions"""

    ALGORITHM_CHOICES = [
        ("content_based", "Content-Based Filtering"),
        ("collaborative", "Collaborative Filtering"),
        ("hybrid", "Hybrid Approach"),
        ("category_based", "Category-Based"),
        ("popularity", "Popularity-Based"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="recommendations_received"
    )
    recommended_case = models.ForeignKey(
        "cases.CharityCase", on_delete=models.CASCADE, related_name="recommendations"
    )
    algorithm_used = models.CharField(max_length=20, choices=ALGORITHM_CHOICES)
    confidence_score = models.FloatField(
        default=0.0, help_text="Algorithm confidence score (0-1)"
    )

    # Interaction tracking
    is_viewed = models.BooleanField(default=False)
    is_clicked = models.BooleanField(default=False)
    is_donated = models.BooleanField(default=False)

    # Context information
    recommendation_context = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional context like user location, time, etc.",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    viewed_at = models.DateTimeField(blank=True, null=True)
    clicked_at = models.DateTimeField(blank=True, null=True)
    donated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "user_recommendations"
        unique_together = ["user", "recommended_case", "algorithm_used"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["algorithm_used"]),
            models.Index(fields=["is_clicked"]),
            models.Index(fields=["is_donated"]),
        ]

    def __str__(self):
        return f"{self.user} -> {self.recommended_case.title} ({self.algorithm_used})"


class AlgorithmPerformance(models.Model):
    """Track algorithm performance metrics over time"""

    algorithm_name = models.CharField(max_length=20)
    date = models.DateField()

    # Performance metrics
    total_recommendations = models.IntegerField(default=0)
    clicked_recommendations = models.IntegerField(default=0)
    donated_recommendations = models.IntegerField(default=0)

    # Calculated metrics
    click_through_rate = models.FloatField(default=0.0)
    conversion_rate = models.FloatField(default=0.0)
    avg_confidence_score = models.FloatField(default=0.0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "algorithm_performance"
        unique_together = ["algorithm_name", "date"]
        indexes = [
            models.Index(fields=["algorithm_name", "date"]),
            models.Index(fields=["date"]),
        ]

    def __str__(self):
        return (
            f"{self.algorithm_name} - {self.date} (CTR: {self.click_through_rate:.2%})"
        )
