from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, F, Q, Sum
from django.db.models.functions import TruncMonth, TruncWeek
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from cases.models import CharityCase
from users.permissions import IsAdminUser, IsOwnerOrAdmin

from .models import Donation
from .serializers import (
    BulkDonationUpdateSerializer,
    DonationCreateSerializer,
    DonationDetailSerializer,
    DonationHistorySerializer,
    DonationListSerializer,
    DonationPublicSerializer,
    DonationStatsSerializer,
)

User = get_user_model()


class DonationViewSet(ModelViewSet):
    """ViewSet for donation CRUD operations"""

    def get_queryset(self):
        """Return filtered queryset based on user permissions"""
        if self.request.user.is_authenticated:
            if self.request.user.is_admin_user:
                return Donation.objects.select_related("donor", "case").all()
            else:
                # Users can only see their own donations
                return Donation.objects.filter(donor=self.request.user).select_related(
                    "case"
                )
        return Donation.objects.none()

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == "create":
            return DonationCreateSerializer
        elif self.action == "list":
            return DonationListSerializer
        return DonationDetailSerializer

    def get_permissions(self):
        """Return appropriate permissions based on action"""
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        elif self.action == "create":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminUser()]

    def create(self, request):
        """Create new donation"""
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            donation = serializer.save()

            # Create payment intent (will be implemented in payments app)
            # payment_intent = create_payment_intent(donation)

            return Response(
                DonationDetailSerializer(donation, context={"request": request}).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a pending donation"""
        donation = self.get_object()

        if donation.status != "pending":
            return Response(
                {"error": "Can only cancel pending donations"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        donation.status = "failed"
        donation.save()

        return Response({"message": "Donation cancelled successfully"})


class DonationCreateView(APIView):
    """API view for creating donations"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Create a new donation"""
        serializer = DonationCreateSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            donation = serializer.save()

            # Here you would integrate with payment gateway
            # For now, just return the donation details
            return Response(
                DonationDetailSerializer(donation, context={"request": request}).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DonationHistoryView(APIView):
    """API view for user's donation history"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get user's donation history"""
        donations = (
            Donation.objects.filter(donor=request.user)
            .select_related("case")
            .order_by("-created_at")
        )

        # Filters
        status_filter = request.GET.get("status")
        if status_filter:
            donations = donations.filter(status=status_filter)

        category_filter = request.GET.get("category")
        if category_filter:
            donations = donations.filter(case__category=category_filter)

        # Date range filter
        date_from = request.GET.get("date_from")
        date_to = request.GET.get("date_to")

        if date_from:
            try:
                date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
                donations = donations.filter(created_at__date__gte=date_from)
            except ValueError:
                pass

        if date_to:
            try:
                date_to = datetime.strptime(date_to, "%Y-%m-%d").date()
                donations = donations.filter(created_at__date__lte=date_to)
            except ValueError:
                pass

        serializer = DonationHistorySerializer(donations, many=True)
        return Response({"count": donations.count(), "results": serializer.data})


class DonationStatsView(APIView):
    """API view for donation statistics"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get donation statistics"""
        user = request.user

        # User's donation stats
        user_donations = Donation.objects.filter(donor=user, status="completed")
        user_stats = user_donations.aggregate(
            total_amount=Sum("amount"),
            total_donations=Count("id"),
            avg_donation=Avg("amount"),
            first_donation=(
                user_donations.order_by("created_at").first().created_at
                if user_donations.exists()
                else None
            ),
            last_donation=(
                user_donations.order_by("-created_at").first().created_at
                if user_donations.exists()
                else None
            ),
        )

        # Category breakdown
        category_stats = (
            user_donations.values("case__category")
            .annotate(count=Count("id"), total=Sum("amount"))
            .order_by("-total")
        )

        # Monthly trend (last 12 months)
        monthly_stats = (
            user_donations.filter(created_at__gte=timezone.now() - timedelta(days=365))
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(count=Count("id"), total=Sum("amount"))
            .order_by("month")
        )

        # Impact metrics
        total_helped_cases = user_donations.values("case").distinct().count()
        completed_cases_helped = (
            user_donations.filter(case__collected_amount__gte=F("case__target_amount"))
            .values("case")
            .distinct()
            .count()
        )

        return Response(
            {
                "personal": {
                    "total_donated": user_stats["total_amount"] or 0,
                    "total_donations": user_stats["total_donations"] or 0,
                    "average_donation": user_stats["avg_donation"] or 0,
                    "first_donation": user_stats["first_donation"],
                    "last_donation": user_stats["last_donation"],
                    "donation_streak": self.calculate_donation_streak(user),
                },
                "impact": {
                    "cases_helped": total_helped_cases,
                    "cases_completed": completed_cases_helped,
                    "impact_ratio": (
                        (completed_cases_helped / total_helped_cases * 100)
                        if total_helped_cases > 0
                        else 0
                    ),
                },
                "breakdown": {
                    "by_category": list(category_stats),
                    "monthly_trend": list(monthly_stats),
                },
            }
        )

    def calculate_donation_streak(self, user):
        """Calculate user's current donation streak in days"""
        donations = Donation.objects.filter(donor=user, status="completed").order_by(
            "-created_at"
        )

        if not donations.exists():
            return 0

        # Simple streak calculation - donations in consecutive days
        streak = 0
        current_date = timezone.now().date()

        for donation in donations:
            donation_date = donation.created_at.date()
            if (current_date - donation_date).days <= streak + 1:
                streak += 1
                current_date = donation_date
            else:
                break

        return streak


class BulkDonationUpdateView(APIView):
    """API view for bulk donation updates (admin only)"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        """Bulk update donation statuses"""
        serializer = BulkDonationUpdateSerializer(data=request.data)
        if serializer.is_valid():
            donation_ids = serializer.validated_data["donation_ids"]
            new_status = serializer.validated_data["status"]

            updated_count = Donation.objects.filter(id__in=donation_ids).update(
                status=new_status
            )

            # If marking as completed, update case collected amounts
            if new_status == "completed":
                donations = Donation.objects.filter(id__in=donation_ids)
                for donation in donations:
                    case = donation.case
                    case.collected_amount = F("collected_amount") + donation.amount
                    case.save()

            return Response(
                {
                    "message": f"{updated_count} donations updated successfully",
                    "updated_count": updated_count,
                }
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DonationReportsView(APIView):
    """API view for donation reports (admin only)"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        """Get comprehensive donation reports"""
        # Date range
        days = int(request.GET.get("days", 30))
        start_date = timezone.now() - timedelta(days=days)

        donations = Donation.objects.filter(
            created_at__gte=start_date, status="completed"
        )

        # Overall stats
        overall_stats = donations.aggregate(
            total_donations=Count("id"),
            total_amount=Sum("amount"),
            avg_donation=Avg("amount"),
            unique_donors=Count("donor", distinct=True),
        )

        # Category breakdown
        category_stats = (
            donations.values("case__category")
            .annotate(count=Count("id"), total=Sum("amount"), avg=Avg("amount"))
            .order_by("-total")
        )

        # Payment method breakdown
        payment_stats = (
            donations.values("payment_method")
            .annotate(count=Count("id"), total=Sum("amount"))
            .order_by("-total")
        )

        # Daily trends
        daily_stats = (
            donations.annotate(
                date=TruncWeek("created_at")  # Use week for longer periods
            )
            .values("date")
            .annotate(count=Count("id"), total=Sum("amount"))
            .order_by("date")
        )

        # Top donors
        top_donors = (
            donations.values("donor__email", "donor__first_name", "donor__last_name")
            .annotate(total_donated=Sum("amount"), donation_count=Count("id"))
            .order_by("-total_donated")[:10]
        )

        # Top cases
        top_cases = (
            donations.values("case__title", "case__id")
            .annotate(
                total_received=Sum("amount"), donor_count=Count("donor", distinct=True)
            )
            .order_by("-total_received")[:10]
        )

        return Response(
            {
                "period": f"Last {days} days",
                "overall": overall_stats,
                "breakdown": {
                    "by_category": list(category_stats),
                    "by_payment_method": list(payment_stats),
                    "daily_trend": list(daily_stats),
                },
                "top_performers": {
                    "donors": list(top_donors),
                    "cases": list(top_cases),
                },
            }
        )


class DonationLeaderboardView(APIView):
    """API view for donation leaderboard (public)"""

    permission_classes = [AllowAny]

    def get(self, request):
        """Get donation leaderboard"""
        period = request.GET.get("period", "all")  # all, monthly, weekly

        donations = Donation.objects.filter(status="completed")

        if period == "monthly":
            donations = donations.filter(
                created_at__gte=timezone.now() - timedelta(days=30)
            )
        elif period == "weekly":
            donations = donations.filter(
                created_at__gte=timezone.now() - timedelta(days=7)
            )

        # Top donors (non-anonymous)
        top_donors = (
            donations.filter(is_anonymous=False)
            .values("donor__first_name", "donor__last_name")
            .annotate(total_donated=Sum("amount"), donation_count=Count("id"))
            .order_by("-total_donated")[:10]
        )

        # Most supported cases
        top_cases = (
            donations.values("case__title", "case__category", "case__slug")
            .annotate(
                total_received=Sum("amount"), donor_count=Count("donor", distinct=True)
            )
            .order_by("-total_received")[:10]
        )

        # Recent large donations
        recent_large = donations.filter(
            amount__gte=1000,  # Large donations threshold
            created_at__gte=timezone.now() - timedelta(days=7),
        ).order_by("-created_at")[:5]

        return Response(
            {
                "period": period,
                "top_donors": list(top_donors),
                "top_cases": list(top_cases),
                "recent_large_donations": DonationPublicSerializer(
                    recent_large, many=True
                ).data,
            }
        )


class RecentDonationsView(APIView):
    """API view for recent donations (public)"""

    permission_classes = [AllowAny]

    def get(self, request):
        """Get recent donations"""
        limit = int(request.GET.get("limit", 20))

        recent_donations = (
            Donation.objects.filter(status="completed")
            .select_related("case", "donor")
            .order_by("-created_at")[:limit]
        )

        serializer = DonationPublicSerializer(recent_donations, many=True)
        return Response({"count": len(recent_donations), "results": serializer.data})
