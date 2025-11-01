from django.urls import path

from . import views

app_name = "cases"

urlpatterns = [
    # Case listing and details
    path("cases/", views.CaseListView.as_view(), name="list"),
    path("cases/<int:pk>/", views.CaseDetailView.as_view(), name="detail"),
    # Case management
    path("cases/create/", views.CaseCreateView.as_view(), name="create"),
    path("cases/<int:pk>/edit/", views.CaseUpdateView.as_view(), name="update"),
    path("cases/<int:pk>/delete/", views.CaseDeleteView.as_view(), name="delete"),
    # Search and categories
    path("cases/search/", views.CaseSearchView.as_view(), name="search"),
    path("cases/categories/", views.CategoryListView.as_view(), name="categories"),
    # Featured and stats
    path("cases/featured/", views.FeaturedCasesView.as_view(), name="featured"),
    path("cases/stats/", views.CaseStatsView.as_view(), name="stats"),
    # User campaigns
    path("my-campaigns/", views.MyCampaignsView.as_view(), name="my_campaigns"),
    # About page
    path("about/", views.AboutView.as_view(), name="about"),
]
