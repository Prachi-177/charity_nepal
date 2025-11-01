import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, ListView, TemplateView

from cases.models import CharityCase

from .forms import DonationForm
from .khalti_utils import khalti_gateway
from .models import Donation


class DonationCreateView(CreateView):
    """Create a new donation with Khalti payment integration"""

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

        # Get amount from query parameter if provided
        amount_param = self.request.GET.get("amount")
        if amount_param:
            context["prefilled_amount"] = amount_param

        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Create donation instance but don't save to database yet
        donation = form.save(commit=False)
        donation.case = self.get_case()

        if self.request.user.is_authenticated:
            donation.donor = self.request.user

        # Generate payment reference
        donation.payment_reference = khalti_gateway.generate_payment_reference()
        donation.status = "pending"
        donation.payment_method = "khalti"  # Force Khalti as payment method

        # Get client IP
        x_forwarded_for = self.request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            donation.ip_address = x_forwarded_for.split(",")[0]
        else:
            donation.ip_address = self.request.META.get("REMOTE_ADDR")

        # Get user agent
        donation.user_agent = self.request.META.get("HTTP_USER_AGENT", "")

        # Save the donation
        donation.save()

        # Handle Khalti payment
        return self.handle_khalti_payment(donation)

    def handle_khalti_payment(self, donation):
        """Handle Khalti payment initiation"""
        try:
            # Get donor information
            donor_name = donation.donor_name or "Anonymous Donor"
            donor_email = donation.donor_email or "anonymous@charity.np"

            if donation.donor and not donation.is_anonymous:
                donor_name = donation.donor.get_full_name() or donation.donor.email
                donor_email = donation.donor.email

            # Initiate payment with Khalti
            payment_response = khalti_gateway.initiate_payment(
                amount=donation.amount,
                donation_id=donation.id,
                donor_name=donor_name,
                donor_email=donor_email,
                case_title=donation.case.title,
                request=self.request,
            )

            if payment_response["success"]:
                # Update donation with payment details
                donation.payment_reference = payment_response["purchase_order_id"]
                donation.save()

                # Redirect to Khalti payment page
                return HttpResponseRedirect(payment_response["data"]["payment_url"])
            else:
                # Payment initiation failed
                donation.status = "failed"
                donation.save()
                messages.error(
                    self.request,
                    f"Failed to initiate payment: {payment_response.get('message', 'Unknown error')}",
                )
                return self.form_invalid(self.get_form())

        except Exception as e:
            donation.status = "failed"
            donation.save()
            messages.error(self.request, f"Payment initialization failed: {str(e)}")
            return self.form_invalid(self.get_form())

    def get_success_url(self):
        case = self.get_case()
        return reverse("cases:detail", kwargs={"pk": case.pk})


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


# Khalti Payment Gateway Views
def khalti_success(request, donation_id):
    """Handle successful Khalti payment callback"""
    try:
        donation = get_object_or_404(Donation, id=donation_id)
        pidx = request.GET.get("pidx")

        if not pidx:
            messages.error(
                request,
                "❌ Payment callback error: Missing payment reference. Please try again.",
            )
            return redirect("cases:detail", pk=donation.case.pk)

        # Verify payment with Khalti
        verification_response = khalti_gateway.verify_payment(pidx)

        if verification_response["success"]:
            payment_status = verification_response["status"]

            if payment_status == "completed":
                # Payment successful
                donation.status = "completed"
                donation.transaction_id = verification_response["transaction_id"]
                donation.completed_at = timezone.now()
                donation.save()

                # Update case collected amount
                case = donation.case
                completed_donations = Donation.objects.filter(
                    case=case, status="completed"
                ).aggregate(total=Sum("amount"))
                case.collected_amount = completed_donations["total"] or 0
                case.save()

                messages.success(
                    request,
                    f"🎉 Thank you for your generous donation of Rs. {donation.amount}! "
                    f"Your contribution will make a real difference.",
                )
            else:
                # Payment failed or pending
                donation.status = payment_status
                donation.save()

                messages.warning(
                    request,
                    f"Payment status: {payment_status}. Please contact support if you have any issues.",
                )
        else:
            # Verification failed
            donation.status = "failed"
            donation.save()
            messages.error(
                request,
                f"❌ Payment verification failed. {verification_response.get('message', 'Please contact support if the problem persists.')}",
            )

    except Exception as e:
        messages.error(
            request,
            f"⚠️ Unable to process your payment. Please try again or contact support. Error: {str(e)}",
        )

    return redirect("cases:detail", pk=donation.case.pk)


@csrf_exempt
@require_POST
def khalti_webhook(request):
    """Handle Khalti webhook for payment notifications"""
    try:
        payload = json.loads(request.body.decode("utf-8"))
        signature = request.headers.get("Khalti-Signature", "")

        # Verify webhook signature
        if not khalti_gateway.verify_webhook_signature(payload, signature):
            return JsonResponse({"error": "Invalid signature"}, status=400)

        # Process webhook data
        event_type = payload.get("type")
        payment_data = payload.get("data", {})

        if event_type == "payment_completed":
            # Find donation by payment reference or transaction ID
            purchase_order_id = payment_data.get("purchase_order_id")

            try:
                donation = Donation.objects.get(payment_reference=purchase_order_id)

                if donation.status != "completed":
                    donation.status = "completed"
                    donation.transaction_id = payment_data.get("transaction_id")
                    donation.completed_at = timezone.now()
                    donation.save()

                    # Update case collected amount
                    donation.case.update_collected_amount()

            except Donation.DoesNotExist:
                return JsonResponse({"error": "Donation not found"}, status=404)

        return JsonResponse({"status": "success"})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def payment_failed(request, donation_id):
    """Handle failed payment"""
    try:
        donation = get_object_or_404(Donation, id=donation_id)
        donation.status = "failed"
        donation.save()

        messages.error(
            request,
            "Payment was not completed. You can try again or choose a different payment method.",
        )
    except Exception as e:
        messages.error(request, f"Error processing failed payment: {str(e)}")

    return redirect("cases:detail", pk=donation.case.pk)


class NotificationsView(LoginRequiredMixin, TemplateView):
    """Display user notifications"""

    template_name = "donations/notifications.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Notifications"

        # Get user's recent donation activity
        user_donations = Donation.objects.filter(donor=self.request.user).order_by(
            "-created_at"
        )[:10]
        context["recent_donations"] = user_donations

        # Get campaigns created by user
        user_campaigns = CharityCase.objects.filter(
            created_by=self.request.user
        ).order_by("-created_at")[:5]
        context["recent_campaigns"] = user_campaigns

        return context


def user_donation_stats(request):
    """API view for user donation statistics"""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    from cases.models import CharityCase

    user = request.user

    # Get completed donation stats
    user_donations = Donation.objects.filter(donor=user, status="completed")

    total_donations = user_donations.count()
    total_amount = user_donations.aggregate(total=Sum("amount"))["total"] or 0

    # Get campaign stats (created by user)
    campaign_count = CharityCase.objects.filter(created_by=user).count()

    return JsonResponse(
        {
            "donation_count": total_donations,
            "total_amount": float(total_amount),
            "campaign_count": campaign_count,
        }
    )
