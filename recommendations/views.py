"""
Recommendation system views
"""

import json
import logging
from datetime import datetime, timedelta

import pandas as pd
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Avg, Count, F, Q, Sum
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from cases.models import CharityCase
from donations.models import Donation
from users.permissions import IsAdminUser

from .algorithms import HybridRecommendationSystem
from .models import RecommendationHistory, RecommendationModel, SearchQuery, UserProfile
from .serializers import (
    RecommendationHistorySerializer,
    RecommendationModelSerializer,
    SearchQuerySerializer,
    UserProfileSerializer,
)

User = get_user_model()
logger = logging.getLogger(__name__)


class PersonalizedRecommendationsView(APIView):
    """Get personalized case recommendations for authenticated users"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            num_recommendations = int(request.GET.get("count", 10))
            algorithm = request.GET.get("algorithm", "hybrid")

            # Get user profile or create if doesn't exist
            user_profile, created = UserProfile.objects.get_or_create(user=user)

            # Check cache first
            cache_key = f"recommendations_{user.id}_{algorithm}_{num_recommendations}"
            cached_recommendations = cache.get(cache_key)

            if cached_recommendations:
                return Response(cached_recommendations)

            # Initialize recommendation system
            hybrid_system = HybridRecommendationSystem()

            # Prepare user data
            user_data = {
                "id": user.id,
                "avg_donation_amount": user_profile.avg_donation_amount,
                "total_donations": user_profile.total_donations,
                "total_donated": float(user_profile.total_donated),
                "preferred_categories": user_profile.preferred_categories,
                "age_range": user_profile.age_range,
                "income_range": user_profile.income_range,
            }

            # Get active cases
            active_cases = CharityCase.objects.filter(
                verification_status="approved", end_date__gt=timezone.now()
            ).exclude(donations__donor=user, donations__status="completed")

            if not active_cases.exists():
                return Response(
                    {
                        "recommendations": [],
                        "message": "No new cases available for recommendation",
                    }
                )

            # Prepare cases data
            cases_df = pd.DataFrame(
                list(
                    active_cases.values(
                        "id",
                        "title",
                        "description",
                        "category",
                        "tags",
                        "target_amount",
                        "collected_amount",
                        "urgency_level",
                    )
                )
            )

            # Get donation history for training
            donations_df = pd.DataFrame(
                list(
                    Donation.objects.filter(
                        status="completed", donor_id=user.id
                    ).values("case_id", "amount", "created_at")
                )
            )

            # Get all user profiles for collaborative filtering
            all_profiles_df = pd.DataFrame(
                list(
                    UserProfile.objects.select_related("user").values(
                        "user_id",
                        "avg_donation_amount",
                        "total_donations",
                        "total_donated",
                        "preferred_categories",
                        "age_range",
                        "income_range",
                    )
                )
            )

            # Get recommendations using appropriate algorithm
            try:
                if algorithm == "content":
                    recommendations = hybrid_system.get_content_based_recommendations(
                        user_data, cases_df, donations_df, top_k=num_recommendations
                    )
                elif algorithm == "collaborative":
                    recommendations = hybrid_system.get_collaborative_recommendations(
                        user_data, cases_df, all_profiles_df, top_k=num_recommendations
                    )
                elif algorithm == "clustering":
                    recommendations = hybrid_system.get_clustering_recommendations(
                        user_data, cases_df, all_profiles_df, top_k=num_recommendations
                    )
                elif algorithm == "decision_tree":
                    recommendations = hybrid_system.get_decision_tree_recommendations(
                        user_data, cases_df, donations_df, top_k=num_recommendations
                    )
                else:  # hybrid (default)
                    recommendations = hybrid_system.get_hybrid_recommendations(
                        user_data,
                        cases_df,
                        all_profiles_df,
                        donations_df,
                        top_k=num_recommendations,
                    )
            except Exception as ml_error:
                logger.warning(
                    f"ML recommendation failed, using fallback: {str(ml_error)}"
                )
                # Fallback to simple category-based recommendations
                user_donations = Donation.objects.filter(donor=user, status="completed")
                preferred_categories = user_donations.values_list(
                    "case__category", flat=True
                ).distinct()

                if preferred_categories:
                    fallback_cases = active_cases.filter(
                        category__in=preferred_categories
                    )[:num_recommendations]
                else:
                    fallback_cases = active_cases.order_by("-created_at")[
                        :num_recommendations
                    ]

                recommendations = [(case.id, 0.5) for case in fallback_cases]

            # Format response
            recommended_cases = []
            for case_id, score in recommendations:
                try:
                    case = active_cases.get(id=case_id)
                    case_data = {
                        "id": case.id,
                        "title": case.title,
                        "description": (
                            case.description[:200] + "..."
                            if len(case.description) > 200
                            else case.description
                        ),
                        "category": case.category,
                        "target_amount": float(case.target_amount),
                        "collected_amount": float(case.collected_amount),
                        "completion_percentage": case.completion_percentage,
                        "urgency_level": case.urgency_level,
                        "image_url": case.image.url if case.image else None,
                        "recommendation_score": float(score),
                        "days_remaining": (
                            (case.end_date - timezone.now().date()).days
                            if case.end_date
                            else None
                        ),
                    }
                    recommended_cases.append(case_data)

                    # Log recommendation
                    RecommendationHistory.objects.create(
                        user=user,
                        case=case,
                        algorithm_used=algorithm,
                        recommendation_score=score,
                    )

                except CharityCase.DoesNotExist:
                    continue

            response_data = {
                "recommendations": recommended_cases,
                "algorithm_used": algorithm,
                "total_count": len(recommended_cases),
                "generated_at": timezone.now().isoformat(),
            }

            # Cache for 1 hour
            cache.set(cache_key, response_data, 3600)

            return Response(response_data)

        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return Response(
                {"error": "Failed to generate recommendations"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TrendingCasesView(APIView):
    """Get trending cases based on recent activity"""

    def get(self, request):
        try:
            num_cases = int(request.GET.get("count", 10))
            days = int(request.GET.get("days", 7))

            # Check cache
            cache_key = f"trending_cases_{num_cases}_{days}"
            cached_trending = cache.get(cache_key)

            if cached_trending:
                return Response(cached_trending)

            # Calculate trending score based on recent donations and views
            cutoff_date = timezone.now() - timedelta(days=days)

            trending_cases = (
                CharityCase.objects.filter(
                    verification_status="approved", end_date__gt=timezone.now()
                )
                .annotate(
                    recent_donations=Count(
                        "donations",
                        filter=Q(
                            donations__created_at__gte=cutoff_date,
                            donations__status="completed",
                        ),
                    ),
                    recent_donation_amount=Sum(
                        "donations__amount",
                        filter=Q(
                            donations__created_at__gte=cutoff_date,
                            donations__status="completed",
                        ),
                    ),
                    total_donors=Count("donations__donor", distinct=True),
                )
                .order_by(
                    "-recent_donations", "-recent_donation_amount", "-total_donors"
                )[:num_cases]
            )

            # Format response
            trending_data = []
            for case in trending_cases:
                case_data = {
                    "id": case.id,
                    "title": case.title,
                    "description": (
                        case.description[:200] + "..."
                        if len(case.description) > 200
                        else case.description
                    ),
                    "category": case.category,
                    "target_amount": float(case.target_amount),
                    "collected_amount": float(case.collected_amount),
                    "completion_percentage": case.completion_percentage,
                    "urgency_level": case.urgency_level,
                    "image_url": case.image.url if case.image else None,
                    "recent_donations": case.recent_donations,
                    "recent_donation_amount": float(case.recent_donation_amount or 0),
                    "total_donors": case.total_donors,
                    "trending_score": case.recent_donations * 10
                    + (case.recent_donation_amount or 0) / 1000,
                }
                trending_data.append(case_data)

            response_data = {
                "trending_cases": trending_data,
                "period_days": days,
                "total_count": len(trending_data),
                "generated_at": timezone.now().isoformat(),
            }

            # Cache for 30 minutes
            cache.set(cache_key, response_data, 1800)

            return Response(response_data)

        except Exception as e:
            logger.error(f"Error getting trending cases: {str(e)}")
            return Response(
                {"error": "Failed to get trending cases"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def track_recommendation_interaction(request):
    """Track when users interact with recommendations"""
    try:
        recommendation_id = request.data.get("recommendation_id")
        action = request.data.get("action")  # 'click', 'donate', 'share'

        if not recommendation_id or not action:
            return Response(
                {"error": "recommendation_id and action are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Find the recommendation history entry
        try:
            recommendation = RecommendationHistory.objects.get(
                id=recommendation_id, user=request.user
            )

            # Update based on action
            if action == "click":
                recommendation.clicked = True
                recommendation.clicked_at = timezone.now()
            elif action == "donate":
                recommendation.donated = True
                recommendation.donated_at = timezone.now()
            elif action == "share":
                recommendation.shared = True
                recommendation.shared_at = timezone.now()

            recommendation.save()

            return Response({"success": True, "message": "Interaction tracked"})

        except RecommendationHistory.DoesNotExist:
            return Response(
                {"error": "Recommendation not found"}, status=status.HTTP_404_NOT_FOUND
            )

    except Exception as e:
        logger.error(f"Error tracking recommendation interaction: {str(e)}")
        return Response(
            {"error": "Failed to track interaction"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Get and update user recommendation profile"""

    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


class RecommendationHistoryView(generics.ListAPIView):
    """Get user's recommendation history"""

    serializer_class = RecommendationHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            RecommendationHistory.objects.filter(user=self.request.user)
            .select_related("case")
            .order_by("-created_at")
        )
