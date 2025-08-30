import json
from datetime import datetime, timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Avg, Case, Count, F, FloatField, Q, Sum, When
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from cases.models import CharityCase
from donations.models import Donation
from users.models import User


@method_decorator(staff_member_required, name="dispatch")
class DashboardView(TemplateView):
    """Custom dashboard view with charts and analytics"""

    template_name = "admin/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get current date ranges
        today = timezone.now().date()
        last_30_days = today - timedelta(days=30)
        last_7_days = today - timedelta(days=7)

        # Basic Statistics
        total_users = User.objects.count()
        total_cases = CharityCase.objects.count()
        approved_cases = CharityCase.objects.filter(
            verification_status="approved"
        ).count()
        total_donations = Donation.objects.filter(status="completed").count()
        total_raised = (
            Donation.objects.filter(status="completed").aggregate(total=Sum("amount"))[
                "total"
            ]
            or 0
        )

        # Recent activity (last 30 days)
        recent_cases = CharityCase.objects.filter(
            created_at__date__gte=last_30_days
        ).count()
        recent_donations = Donation.objects.filter(
            created_at__date__gte=last_30_days, status="completed"
        ).count()
        recent_raised = (
            Donation.objects.filter(
                created_at__date__gte=last_30_days, status="completed"
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )

        # Category breakdown
        category_stats = (
            CharityCase.objects.values("category")
            .annotate(count=Count("id"), total_raised=Sum("collected_amount"))
            .order_by("-count")
        )

        # Success rate by category
        success_stats = (
            CharityCase.objects.values("category")
            .annotate(
                total=Count("id"),
                completed=Count(
                    "id", filter=Q(collected_amount__gte=F("target_amount"))
                ),
                avg_completion=Avg(
                    Case(
                        When(
                            target_amount__gt=0,
                            then=F("collected_amount") * 100.0 / F("target_amount"),
                        ),
                        default=0,
                        output_field=FloatField(),
                    )
                ),
            )
            .order_by("-avg_completion")
        )

        # Monthly trends (last 12 months)
        monthly_data = []
        for i in range(11, -1, -1):
            month_date = today.replace(day=1) - timedelta(days=i * 30)
            next_month = month_date + timedelta(days=32)
            next_month = next_month.replace(day=1)

            monthly_cases = CharityCase.objects.filter(
                created_at__date__gte=month_date, created_at__date__lt=next_month
            ).count()

            monthly_donations = Donation.objects.filter(
                created_at__date__gte=month_date,
                created_at__date__lt=next_month,
                status="completed",
            ).aggregate(count=Count("id"), total=Sum("amount"))

            monthly_data.append(
                {
                    "month": month_date.strftime("%Y-%m"),
                    "month_name": month_date.strftime("%b %Y"),
                    "cases": monthly_cases,
                    "donations_count": monthly_donations["count"] or 0,
                    "donations_amount": float(monthly_donations["total"] or 0),
                }
            )

        # Top performers
        top_cases = CharityCase.objects.filter(verification_status="approved").order_by(
            "-collected_amount"
        )[:10]

        top_donors = (
            Donation.objects.filter(status="completed", is_anonymous=False)
            .values("donor__first_name", "donor__last_name", "donor__id")
            .annotate(total_donated=Sum("amount"), donation_count=Count("id"))
            .order_by("-total_donated")[:10]
        )

        # Urgency distribution
        urgency_stats = (
            CharityCase.objects.values("urgency_flag")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        # Payment method distribution
        payment_stats = (
            Donation.objects.filter(status="completed")
            .values("payment_method")
            .annotate(count=Count("id"), total=Sum("amount"))
            .order_by("-total")
        )

        # Average donation by category
        avg_donation_by_category = (
            Donation.objects.filter(status="completed")
            .values("case__category")
            .annotate(avg_amount=Avg("amount"), count=Count("id"))
            .order_by("-avg_amount")
        )

        context.update(
            {
                "total_users": total_users,
                "total_cases": total_cases,
                "approved_cases": approved_cases,
                "total_donations": total_donations,
                "total_raised": total_raised,
                "recent_cases": recent_cases,
                "recent_donations": recent_donations,
                "recent_raised": recent_raised,
                "category_stats": category_stats,
                "success_stats": success_stats,
                "monthly_data": json.dumps(monthly_data),
                "top_cases": top_cases,
                "top_donors": top_donors,
                "urgency_stats": urgency_stats,
                "payment_stats": payment_stats,
                "avg_donation_by_category": avg_donation_by_category,
                "approval_rate": (
                    round((approved_cases / total_cases * 100), 1)
                    if total_cases > 0
                    else 0
                ),
            }
        )

        return context


@staff_member_required
def dashboard_api(request):
    """API endpoint for real-time dashboard data"""
    today = timezone.now().date()

    # Daily data for the last 30 days
    daily_data = []
    for i in range(29, -1, -1):
        date = today - timedelta(days=i)
        next_date = date + timedelta(days=1)

        cases_count = CharityCase.objects.filter(created_at__date=date).count()

        donations_data = Donation.objects.filter(
            created_at__date=date, status="completed"
        ).aggregate(count=Count("id"), total=Sum("amount"))

        daily_data.append(
            {
                "date": date.isoformat(),
                "cases": cases_count,
                "donations": donations_data["count"] or 0,
                "amount": float(donations_data["total"] or 0),
            }
        )

    # Hourly data for today
    hourly_data = []
    for hour in range(24):
        hour_start = timezone.now().replace(
            hour=hour, minute=0, second=0, microsecond=0
        )
        hour_end = hour_start + timedelta(hours=1)

        donations_count = Donation.objects.filter(
            created_at__range=[hour_start, hour_end], status="completed"
        ).count()

        hourly_data.append({"hour": hour, "donations": donations_count})

    return JsonResponse(
        {
            "daily_data": daily_data,
            "hourly_data": hourly_data,
            "timestamp": timezone.now().isoformat(),
        }
    )


@staff_member_required
def case_analytics(request, case_id):
    """Detailed analytics for a specific case"""
    try:
        case = CharityCase.objects.get(id=case_id)

        # Daily donation data for this case
        donations = case.donations.filter(status="completed").order_by("created_at")
        daily_donations = {}

        for donation in donations:
            date = donation.created_at.date()
            if date not in daily_donations:
                daily_donations[date] = {"count": 0, "amount": 0}
            daily_donations[date]["count"] += 1
            daily_donations[date]["amount"] += float(donation.amount)

        # Convert to chart data
        chart_data = []
        running_total = 0
        for date, data in sorted(daily_donations.items()):
            running_total += data["amount"]
            chart_data.append(
                {
                    "date": date.isoformat(),
                    "daily_amount": data["amount"],
                    "daily_count": data["count"],
                    "cumulative_amount": running_total,
                }
            )

        # Donor demographics
        donor_locations = (
            case.donations.filter(status="completed", is_anonymous=False)
            .values("donor__address")
            .annotate(count=Count("id"), total=Sum("amount"))
            .order_by("-total")[:10]
        )

        # Payment method breakdown
        payment_methods = (
            case.donations.filter(status="completed")
            .values("payment_method")
            .annotate(count=Count("id"), total=Sum("amount"))
        )

        return JsonResponse(
            {
                "case_title": case.title,
                "target_amount": float(case.target_amount),
                "collected_amount": float(case.collected_amount),
                "completion_percentage": float(case.completion_percentage),
                "chart_data": chart_data,
                "donor_locations": list(donor_locations),
                "payment_methods": list(payment_methods),
                "total_donors": case.donations.filter(status="completed").count(),
                "avg_donation": float(
                    case.donations.filter(status="completed").aggregate(
                        avg=Avg("amount")
                    )["avg"]
                    or 0
                ),
            }
        )

    except CharityCase.DoesNotExist:
        return JsonResponse({"error": "Case not found"}, status=404)


@require_POST
@staff_member_required
def toggle_sidebar(request):
    """Simple toggle sidebar view to satisfy Django Unfold requirements"""
    # This is just a dummy view to prevent the NoReverseMatch error
    # In a real implementation, this might store sidebar state in session
    return JsonResponse({"status": "success", "message": "Sidebar toggled"})
