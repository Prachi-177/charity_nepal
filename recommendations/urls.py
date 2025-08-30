"""
URL configuration for recommendations app
"""

from django.urls import path

from . import views

app_name = "recommendations"

urlpatterns = [
    # Personalized recommendations
    path(
        "personal/",
        views.PersonalizedRecommendationsView.as_view(),
        name="personal-recommendations",
    ),
    # Trending cases
    path("trending/", views.TrendingCasesView.as_view(), name="trending-cases"),
    # User profile management
    path("profile/", views.UserProfileView.as_view(), name="user-profile"),
    # Recommendation history
    path(
        "history/",
        views.RecommendationHistoryView.as_view(),
        name="recommendation-history",
    ),
    # Track interactions
    path("track/", views.track_recommendation_interaction, name="track-interaction"),
]
