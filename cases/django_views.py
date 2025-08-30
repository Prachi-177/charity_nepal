from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from .forms import CharityCaseForm
from .models import CharityCase


class CaseListView(ListView):
    """List all approved charity cases"""

    model = CharityCase
    template_name = "cases/list.html"
    context_object_name = "cases"
    paginate_by = 12

    def get_queryset(self):
        queryset = CharityCase.objects.filter(
            verification_status="approved"
        ).select_related("created_by")

        # Filter by category
        category = self.request.GET.get("category")
        if category and category != "all":
            queryset = queryset.filter(category=category)

        # Filter by urgency
        urgency = self.request.GET.get("urgency")
        if urgency:
            queryset = queryset.filter(urgency_flag=urgency)

        # Search functionality
        search_query = self.request.GET.get("search")
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query)
                | Q(description__icontains=search_query)
                | Q(beneficiary_name__icontains=search_query)
            )

        # Ordering
        ordering = self.request.GET.get("ordering", "-created_at")
        queryset = queryset.order_by(ordering)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "All Campaigns"
        context["categories"] = CharityCase.CATEGORY_CHOICES
        context["current_category"] = self.request.GET.get("category", "all")
        context["search_query"] = self.request.GET.get("search", "")
        return context


class CaseDetailView(DetailView):
    """Display detailed view of a charity case"""

    model = CharityCase
    template_name = "cases/detail.html"
    context_object_name = "case"

    def get_queryset(self):
        # Allow viewing pending cases only for owners and admins
        if self.request.user.is_authenticated and (
            self.request.user.is_admin_user
            or CharityCase.objects.filter(
                pk=self.kwargs["pk"], created_by=self.request.user
            ).exists()
        ):
            return CharityCase.objects.all()
        return CharityCase.objects.filter(verification_status="approved")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = self.object.title

        # Get related donations (you'll implement this later)
        # context['recent_donations'] = self.object.donations.order_by('-created_at')[:5]

        # Check if user can edit this case
        context["can_edit"] = self.request.user.is_authenticated and (
            self.request.user == self.object.created_by
            or self.request.user.is_admin_user
        )

        return context


class CaseCreateView(LoginRequiredMixin, CreateView):
    """Create a new charity case"""

    model = CharityCase
    form_class = CharityCaseForm
    template_name = "cases/create.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(
            self.request, "Your campaign has been created and is pending approval."
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("cases:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create New Campaign"
        return context


class CaseUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing charity case"""

    model = CharityCase
    form_class = CharityCaseForm
    template_name = "cases/update.html"

    def get_queryset(self):
        # Only allow editing own cases or admin can edit all
        if self.request.user.is_admin_user:
            return CharityCase.objects.all()
        return CharityCase.objects.filter(created_by=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Your campaign has been updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("cases:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Edit: {self.object.title}"
        return context


class CaseDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a charity case"""

    model = CharityCase
    template_name = "cases/delete.html"
    success_url = reverse_lazy("cases:list")

    def get_queryset(self):
        # Only allow deleting own cases or admin can delete all
        if self.request.user.is_admin_user:
            return CharityCase.objects.all()
        return CharityCase.objects.filter(created_by=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Campaign has been deleted successfully.")
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Delete: {self.object.title}"
        return context


class CaseSearchView(ListView):
    """Search charity cases"""

    model = CharityCase
    template_name = "cases/search.html"
    context_object_name = "cases"
    paginate_by = 12

    def get_queryset(self):
        query = self.request.GET.get("q", "")
        if query:
            return (
                CharityCase.objects.filter(verification_status="approved")
                .filter(
                    Q(title__icontains=query)
                    | Q(description__icontains=query)
                    | Q(beneficiary_name__icontains=query)
                    | Q(tags__icontains=query)
                )
                .order_by("-created_at")
            )
        return CharityCase.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Search Results"
        context["search_query"] = self.request.GET.get("q", "")
        return context


class CategoryListView(TemplateView):
    """Display categories with case counts"""

    template_name = "cases/categories.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Browse by Category"

        # Get category counts
        categories = []
        for category_key, category_label in CharityCase.CATEGORY_CHOICES:
            count = CharityCase.objects.filter(
                category=category_key, verification_status="approved"
            ).count()
            categories.append(
                {"key": category_key, "label": category_label, "count": count}
            )

        context["categories"] = categories
        return context


class FeaturedCasesView(ListView):
    """Display featured charity cases"""

    model = CharityCase
    template_name = "cases/featured.html"
    context_object_name = "cases"

    def get_queryset(self):
        # Featured cases: high urgency, good progress, recently created
        return (
            CharityCase.objects.filter(verification_status="approved")
            .filter(Q(urgency_flag="critical") | Q(urgency_flag="high"))
            .order_by("-created_at")[:6]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Featured Campaigns"
        return context


class CaseStatsView(TemplateView):
    """Display statistics about charity cases"""

    template_name = "cases/stats.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Campaign Statistics"

        # Calculate stats
        all_cases = CharityCase.objects.filter(verification_status="approved")
        context["stats"] = {
            "total_cases": all_cases.count(),
            "total_target": all_cases.aggregate(Sum("target_amount"))[
                "target_amount__sum"
            ]
            or 0,
            "total_collected": all_cases.aggregate(Sum("collected_amount"))[
                "collected_amount__sum"
            ]
            or 0,
            "categories": {
                category[0]: all_cases.filter(category=category[0]).count()
                for category in CharityCase.CATEGORY_CHOICES
            },
        }

        return context
