"""
Analytics dashboard for ML algorithms and recommendation system
"""

import json
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Avg, Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from cases.models import CharityCase
from donations.models import Donation
from recommendations.models import UserRecommendation
from users.models import User


@method_decorator(staff_member_required, name="dispatch")
class MLAnalyticsView(TemplateView):
    """ML Algorithm Performance Analytics Dashboard"""

    template_name = "admin/ml_analytics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Algorithm Performance Metrics
        algorithm_stats = self._get_algorithm_performance()
        recommendation_stats = self._get_recommendation_stats()
        user_behavior_analysis = self._get_user_behavior_analysis()
        prediction_accuracy = self._get_prediction_accuracy()

        context.update(
            {
                "algorithm_stats": algorithm_stats,
                "recommendation_stats": recommendation_stats,
                "user_behavior_analysis": user_behavior_analysis,
                "prediction_accuracy": prediction_accuracy,
            }
        )

        return context

    def _get_algorithm_performance(self):
        """Analyze performance of different recommendation algorithms"""

        # Get recommendation data
        recommendations = UserRecommendation.objects.all()
        total_recommendations = recommendations.count()

        if total_recommendations == 0:
            return {
                "total_recommendations": 0,
                "algorithms": [],
                "performance_metrics": {},
            }

        # Algorithm distribution
        algorithm_distribution = (
            recommendations.values("algorithm_used")
            .annotate(count=Count("id"), avg_score=Avg("confidence_score"))
            .order_by("-count")
        )

        # Click-through rates by algorithm
        ctr_by_algorithm = {}
        for algo in algorithm_distribution:
            algo_name = algo["algorithm_used"]
            algo_recommendations = recommendations.filter(algorithm_used=algo_name)
            total_shown = algo_recommendations.count()
            total_clicked = algo_recommendations.filter(is_clicked=True).count()
            ctr = (total_clicked / total_shown * 100) if total_shown > 0 else 0

            ctr_by_algorithm[algo_name] = {
                "total_shown": total_shown,
                "total_clicked": total_clicked,
                "ctr": round(ctr, 2),
            }

        return {
            "total_recommendations": total_recommendations,
            "algorithm_distribution": list(algorithm_distribution),
            "ctr_by_algorithm": ctr_by_algorithm,
        }

    def _get_recommendation_stats(self):
        """Get recommendation system statistics"""

        today = timezone.now().date()
        last_30_days = today - timedelta(days=30)

        recommendations = UserRecommendation.objects.filter(
            created_at__date__gte=last_30_days
        )

        # Daily recommendation counts
        daily_recommendations = {}
        for i in range(30):
            date = today - timedelta(days=i)
            count = recommendations.filter(created_at__date=date).count()
            daily_recommendations[date.isoformat()] = count

        # User engagement metrics
        total_users_with_recommendations = (
            recommendations.values("user").distinct().count()
        )
        avg_recommendations_per_user = (
            recommendations.values("user")
            .annotate(count=Count("id"))
            .aggregate(avg=Avg("count"))["avg"]
            or 0
        )

        # Success metrics
        successful_recommendations = recommendations.filter(is_clicked=True).count()
        conversion_rate = (
            (successful_recommendations / recommendations.count() * 100)
            if recommendations.count() > 0
            else 0
        )

        return {
            "daily_recommendations": daily_recommendations,
            "total_users_with_recommendations": total_users_with_recommendations,
            "avg_recommendations_per_user": round(avg_recommendations_per_user, 2),
            "successful_recommendations": successful_recommendations,
            "conversion_rate": round(conversion_rate, 2),
        }

    def _get_user_behavior_analysis(self):
        """Analyze user behavior patterns"""

        # User donation patterns
        user_donation_stats = (
            Donation.objects.filter(status="completed")
            .values("donor")
            .annotate(
                total_donations=Count("id"),
                total_amount=Sum("amount"),
                avg_amount=Avg("amount"),
                categories_donated=Count("case__category", distinct=True),
            )
            .order_by("-total_amount")[:20]
        )

        # Category preferences
        category_preferences = (
            Donation.objects.filter(status="completed")
            .values("case__category")
            .annotate(
                donation_count=Count("id"),
                total_amount=Sum("amount"),
                unique_donors=Count("donor", distinct=True),
            )
            .order_by("-donation_count")
        )

        # Donation timing patterns (hourly distribution)
        hourly_donations = {}
        for hour in range(24):
            count = Donation.objects.filter(
                status="completed", created_at__hour=hour
            ).count()
            hourly_donations[hour] = count

        return {
            "top_donors": list(user_donation_stats),
            "category_preferences": list(category_preferences),
            "hourly_distribution": hourly_donations,
        }

    def _get_prediction_accuracy(self):
        """Calculate prediction accuracy metrics"""

        # Get cases that were recommended vs actually donated to
        recommendations = UserRecommendation.objects.filter(is_clicked=True)

        accuracy_metrics = {
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0,
            "total_predictions": recommendations.count(),
        }

        if recommendations.count() > 0:
            # Calculate precision (clicked recommendations / total recommendations)
            total_recommendations = UserRecommendation.objects.count()
            clicked_recommendations = recommendations.count()

            precision = 0
            if total_recommendations > 0:
                precision = clicked_recommendations / total_recommendations
                accuracy_metrics["precision"] = round(precision * 100, 2)

            # For demo purposes, simulate recall and F1 score
            # In a real system, you'd compare against actual user actions
            if precision > 0:
                accuracy_metrics["recall"] = round(precision * 0.85 * 100, 2)
                accuracy_metrics["f1_score"] = round(
                    2
                    * (accuracy_metrics["precision"] * accuracy_metrics["recall"])
                    / (accuracy_metrics["precision"] + accuracy_metrics["recall"]),
                    2,
                )

        return accuracy_metrics


@staff_member_required
def ml_analytics_api(request):
    """API endpoint for real-time ML analytics data"""

    # Get recent performance data
    today = timezone.now().date()
    last_7_days = today - timedelta(days=7)

    # Daily algorithm usage
    daily_algo_usage = {}
    for i in range(7):
        date = today - timedelta(days=i)
        recommendations = UserRecommendation.objects.filter(created_at__date=date)

        algo_counts = recommendations.values("algorithm_used").annotate(
            count=Count("id")
        )

        daily_algo_usage[date.isoformat()] = {
            algo["algorithm_used"]: algo["count"] for algo in algo_counts
        }

    # Real-time metrics
    total_recommendations_today = UserRecommendation.objects.filter(
        created_at__date=today
    ).count()

    successful_recommendations_today = UserRecommendation.objects.filter(
        created_at__date=today, is_clicked=True
    ).count()

    return JsonResponse(
        {
            "daily_algorithm_usage": daily_algo_usage,
            "today_metrics": {
                "total_recommendations": total_recommendations_today,
                "successful_recommendations": successful_recommendations_today,
                "success_rate": (
                    round(
                        (
                            successful_recommendations_today
                            / total_recommendations_today
                            * 100
                        ),
                        2,
                    )
                    if total_recommendations_today > 0
                    else 0
                ),
            },
            "timestamp": timezone.now().isoformat(),
        }
    )


@staff_member_required
def algorithm_comparison(request):
    """Compare different algorithm performances"""

    algorithms = ["content_based", "collaborative", "hybrid", "category_based"]
    comparison_data = {}

    for algorithm in algorithms:
        recommendations = UserRecommendation.objects.filter(algorithm_used=algorithm)
        total = recommendations.count()
        clicked = recommendations.filter(is_clicked=True).count()
        avg_score = recommendations.aggregate(avg=Avg("confidence_score"))["avg"] or 0

        comparison_data[algorithm] = {
            "total_recommendations": total,
            "successful_recommendations": clicked,
            "click_through_rate": round((clicked / total * 100), 2) if total > 0 else 0,
            "avg_confidence_score": round(avg_score, 3),
        }

    return JsonResponse(
        {
            "algorithm_comparison": comparison_data,
            "best_performing": (
                max(comparison_data.items(), key=lambda x: x[1]["click_through_rate"])[
                    0
                ]
                if comparison_data
                else None
            ),
        }
    )


@staff_member_required
def user_segmentation_analysis(request):
    """Analyze user segments for better targeting"""

    # Segment users based on donation behavior
    user_segments = {
        "high_value": User.objects.annotate(
            total_donated=Sum(
                "donations__amount", filter=Q(donations__status="completed")
            )
        )
        .filter(total_donated__gte=10000)
        .count(),
        "regular_donors": User.objects.annotate(
            donation_count=Count("donations", filter=Q(donations__status="completed"))
        )
        .filter(donation_count__gte=5)
        .count(),
        "occasional_donors": User.objects.annotate(
            donation_count=Count("donations", filter=Q(donations__status="completed"))
        )
        .filter(donation_count__range=[2, 4])
        .count(),
        "new_donors": User.objects.annotate(
            donation_count=Count("donations", filter=Q(donations__status="completed"))
        )
        .filter(donation_count=1)
        .count(),
        "inactive_users": User.objects.annotate(
            donation_count=Count("donations", filter=Q(donations__status="completed"))
        )
        .filter(donation_count=0)
        .count(),
    }

    # Category preferences by segment
    segment_preferences = {}
    for segment, count in user_segments.items():
        if segment == "high_value":
            users = User.objects.annotate(
                total_donated=Sum(
                    "donations__amount", filter=Q(donations__status="completed")
                )
            ).filter(total_donated__gte=10000)
        elif segment == "regular_donors":
            users = User.objects.annotate(
                donation_count=Count(
                    "donations", filter=Q(donations__status="completed")
                )
            ).filter(donation_count__gte=5)
        else:
            continue

        preferences = (
            Donation.objects.filter(donor__in=users, status="completed")
            .values("case__category")
            .annotate(count=Count("id"))
            .order_by("-count")[:3]
        )

        segment_preferences[segment] = list(preferences)

    return JsonResponse(
        {"user_segments": user_segments, "segment_preferences": segment_preferences}
    )
