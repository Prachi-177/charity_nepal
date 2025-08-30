from django.urls import path

from . import views

app_name = "donations"

urlpatterns = [
    # Donation management
    path("donate/<int:case_id>/", views.DonationCreateView.as_view(), name="create"),
    path("my-donations/", views.MyDonationsView.as_view(), name="my_donations"),
    path("<int:pk>/", views.DonationDetailView.as_view(), name="detail"),
    # Public donation info
    path("recent/", views.RecentDonationsView.as_view(), name="recent"),
    path("leaderboard/", views.DonationLeaderboardView.as_view(), name="leaderboard"),
    path("stats/", views.DonationStatsView.as_view(), name="stats"),
]
