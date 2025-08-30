from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView, TemplateView

from cases.models import CharityCase

from .forms import DonationForm
from .models import Donation


class DonationCreateView(CreateView):
    """Create a new donation"""

    model = Donation
    form_class = DonationForm
    template_name = "donations/create.html"

    def get_case(self):
        return get_object_or_404(
            CharityCase, pk=self.kwargs["case_id"], verification_status="approved"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["case"] = self.get_case()
        context["title"] = f'Donate to {context["case"].title}'
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.case = self.get_case()
        if self.request.user.is_authenticated:
            form.instance.donor = self.request.user

        response = super().form_valid(form)
        messages.success(self.request, "Thank you for your generous donation!")
        return response

    def get_success_url(self):
        # Redirect to case detail page with success message
        return reverse("cases:detail", kwargs={"pk": self.object.case.pk})


class MyDonationsView(LoginRequiredMixin, ListView):
    """List current user's donations"""

    model = Donation
    template_name = "donations/my_donations.html"
    context_object_name = "donations"
    paginate_by = 20

    def get_queryset(self):
        return (
            Donation.objects.filter(donor=self.request.user)
            .select_related("case")
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "My Donations"

        # Calculate summary statistics
        total_donated = self.get_queryset().aggregate(total=Sum("amount"))["total"] or 0
        context["total_donated"] = total_donated
        context["total_donations"] = self.get_queryset().count()

        return context


class DonationDetailView(DetailView):
    """Display donation details"""

    model = Donation
    template_name = "donations/detail.html"
    context_object_name = "donation"

    def get_queryset(self):
        # Users can only see their own donations, admins can see all
        if self.request.user.is_authenticated:
            if self.request.user.is_staff:
                return Donation.objects.all()
            return Donation.objects.filter(donor=self.request.user)
        return Donation.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Donation #{self.get_object().pk}"
        return context


class RecentDonationsView(ListView):
    """Display recent public donations"""

    model = Donation
    template_name = "donations/recent.html"
    context_object_name = "donations"
    paginate_by = 20

    def get_queryset(self):
        return (
            Donation.objects.filter(status="completed", is_anonymous=False)
            .select_related("donor", "case")
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Recent Donations"
        return context


class DonationLeaderboardView(ListView):
    """Display donation leaderboard"""

    model = Donation
    template_name = "donations/leaderboard.html"
    context_object_name = "top_donors"

    def get_queryset(self):
        # Get top donors by total donation amount
        return (
            Donation.objects.filter(
                status="completed", is_anonymous=False, donor__isnull=False
            )
            .values("donor__first_name", "donor__last_name", "donor__pk")
            .annotate(total_donated=Sum("amount"), donation_count=Count("pk"))
            .order_by("-total_donated")[:50]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Top Donors"

        # Get top campaigns by donations received
        top_cases = (
            CharityCase.objects.annotate(
                total_donations=Sum("donations__amount"),
                donor_count=Count("donations", distinct=True),
            )
            .filter(verification_status="approved")
            .order_by("-total_donations")[:10]
        )

        context["top_cases"] = top_cases
        return context


class DonationStatsView(TemplateView):
    """Display donation statistics"""

    template_name = "donations/stats.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Donation Statistics"

        # Calculate various statistics
        total_donations = Donation.objects.filter(status="completed").aggregate(
            total_amount=Sum("amount"), total_count=Count("pk")
        )

        context["total_amount"] = total_donations["total_amount"] or 0
        context["total_count"] = total_donations["total_count"] or 0

        if context["total_count"] > 0:
            context["average_donation"] = (
                context["total_amount"] / context["total_count"]
            )
        else:
            context["average_donation"] = 0

        # Monthly statistics (last 12 months)
        from datetime import datetime, timedelta

        from django.db.models import TruncMonth

        twelve_months_ago = datetime.now() - timedelta(days=365)
        monthly_stats = (
            Donation.objects.filter(
                status="completed", created_at__gte=twelve_months_ago
            )
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(total=Sum("amount"), count=Count("pk"))
            .order_by("month")
        )

        context["monthly_stats"] = monthly_stats

        return context
