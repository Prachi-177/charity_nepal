from django.urls import path

from . import views

app_name = "donations"

urlpatterns = [
    # Donation management
    path("donate/<int:case_id>/", views.DonationCreateView.as_view(), name="create"),
    path("my-donations/", views.MyDonationsView.as_view(), name="my_donations"),
    path("<int:pk>/", views.DonationDetailView.as_view(), name="detail"),
    # Payment callbacks
    path(
        "khalti/success/<int:donation_id>/", views.khalti_success, name="khalti_success"
    ),
    path(
        "khalti/failed/<int:donation_id>/", views.payment_failed, name="khalti_failed"
    ),
    path("khalti/webhook/", views.khalti_webhook, name="khalti_webhook"),
    # Public donation info
    path("recent/", views.RecentDonationsView.as_view(), name="recent"),
    path("leaderboard/", views.DonationLeaderboardView.as_view(), name="leaderboard"),
    path("stats/", views.DonationStatsView.as_view(), name="stats"),
]
