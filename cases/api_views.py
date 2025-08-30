import re
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, F, Q, Sum
from django.utils import timezone
from rest_framework import filters, permissions, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from sklearn.feature_extraction.text import TfidfVectorizer

from users.permissions import IsAdminOrReadOnly, IsAdminUser, IsOwnerOrAdmin

from .models import CaseUpdate, CharityCase
from .serializers import (
    CaseUpdateCreateSerializer,
    CaseUpdateSerializer,
    CharityCaseCreateSerializer,
    CharityCaseDetailSerializer,
    CharityCaseListSerializer,
    CharityCaseSearchSerializer,
    CharityCaseStatusSerializer,
    CharityCaseUpdateSerializer,
)

User = get_user_model()


class CharityCaseViewSet(ModelViewSet):
    """ViewSet for charity cases CRUD operations"""

    permission_classes = [AllowAny]  # Custom permissions handled in methods

    def get_queryset(self):
        """Return filtered queryset based on user permissions"""
        queryset = CharityCase.objects.select_related(
            "created_by", "approved_by"
        ).prefetch_related("donations")

        # Non-admin users can only see approved cases
        if (
            not self.request.user.is_authenticated
            or not self.request.user.is_admin_user
        ):
            queryset = queryset.filter(verification_status="approved")

        return queryset.order_by("-created_at")

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == "list":
            return CharityCaseListSerializer
        elif self.action == "create":
            return CharityCaseCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return CharityCaseUpdateSerializer
        elif self.action == "update_status":
            return CharityCaseStatusSerializer
        return CharityCaseDetailSerializer

    def get_permissions(self):
        """Return appropriate permissions based on action"""
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        elif self.action == "create":
            return [IsAuthenticated()]
        elif self.action in ["update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        elif self.action == "update_status":
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]

    def list(self, request):
        """List charity cases with filtering"""
        queryset = self.get_queryset()

        # Apply filters
        category = request.GET.get("category")
        if category:
            queryset = queryset.filter(category=category)

        location = request.GET.get("location")
        if location:
            queryset = queryset.filter(location__icontains=location)

        urgency = request.GET.get("urgency")
        if urgency:
            queryset = queryset.filter(urgency_flag=urgency)

        status_filter = request.GET.get("status")
        if status_filter == "active":
            queryset = queryset.filter(
                verification_status="approved", collected_amount__lt=F("target_amount")
            )
        elif status_filter == "completed":
            queryset = queryset.filter(collected_amount__gte=F("target_amount"))

        min_amount = request.GET.get("min_amount")
        if min_amount:
            try:
                queryset = queryset.filter(target_amount__gte=float(min_amount))
            except ValueError:
                pass

        max_amount = request.GET.get("max_amount")
        if max_amount:
            try:
                queryset = queryset.filter(target_amount__lte=float(max_amount))
            except ValueError:
                pass

        # Ordering
        ordering = request.GET.get("ordering", "-created_at")
        if ordering:
            queryset = queryset.order_by(ordering)

        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        """Create new charity case"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            case = serializer.save()
            return Response(
                CharityCaseDetailSerializer(case).data, status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=["patch"],
        permission_classes=[IsAuthenticated, IsAdminUser],
    )
    def update_status(self, request, pk=None):
        """Update case verification status (admin only)"""
        case = self.get_object()
        serializer = CharityCaseStatusSerializer(
            case, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"])
    def donations(self, request, pk=None):
        """Get donations for a specific case"""
        case = self.get_object()
        from donations.serializers import DonationPublicSerializer

        donations = case.donations.filter(status="completed").order_by("-created_at")

        page = self.paginate_queryset(donations)
        if page is not None:
            serializer = DonationPublicSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = DonationPublicSerializer(donations, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def similar(self, request, pk=None):
        """Get similar cases"""
        case = self.get_object()
        similar_cases = (
            CharityCase.objects.filter(
                category=case.category, verification_status="approved"
            )
            .exclude(id=case.id)
            .order_by("-created_at")[:5]
        )

        serializer = CharityCaseListSerializer(similar_cases, many=True)
        return Response(serializer.data)


class CaseUpdateViewSet(ModelViewSet):
    """ViewSet for case updates"""

    serializer_class = CaseUpdateSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        """Return case updates"""
        return CaseUpdate.objects.select_related("case", "created_by").order_by(
            "-created_at"
        )

    def get_serializer_class(self):
        """Return appropriate serializer"""
        if self.action == "create":
            return CaseUpdateCreateSerializer
        return CaseUpdateSerializer

    def get_permissions(self):
        """Return appropriate permissions"""
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAuthenticated(), IsOwnerOrAdmin()]


class CharityCaseSearchView(APIView):
    """API view for searching charity cases"""

    permission_classes = [AllowAny]

    def get(self, request):
        """Search charity cases"""
        # Validate search parameters
        search_serializer = CharityCaseSearchSerializer(data=request.GET)
        if not search_serializer.is_valid():
            return Response(
                search_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        validated_data = search_serializer.validated_data

        # Start with approved cases
        queryset = CharityCase.objects.filter(verification_status="approved")

        # Text search
        query = validated_data.get("q")
        if query:
            # Simple text search - can be enhanced with full-text search
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(beneficiary_name__icontains=query)
                | Q(tags__icontains=query)
            )

        # Apply filters
        category = validated_data.get("category")
        if category:
            queryset = queryset.filter(category=category)

        location = validated_data.get("location")
        if location:
            queryset = queryset.filter(location__icontains=location)

        urgency = validated_data.get("urgency")
        if urgency:
            queryset = queryset.filter(urgency_flag=urgency)

        min_amount = validated_data.get("min_amount")
        if min_amount:
            queryset = queryset.filter(target_amount__gte=min_amount)

        max_amount = validated_data.get("max_amount")
        if max_amount:
            queryset = queryset.filter(target_amount__lte=max_amount)

        status_filter = validated_data.get("status")
        if status_filter == "active":
            from django.db.models import F

            queryset = queryset.filter(collected_amount__lt=F("target_amount"))
        elif status_filter == "completed":
            from django.db.models import F

            queryset = queryset.filter(collected_amount__gte=F("target_amount"))

        # Ordering
        ordering = validated_data.get("ordering", "-created_at")
        queryset = queryset.order_by(ordering)

        # Log search query for analytics
        if request.user.is_authenticated:
            from recommendations.models import SearchQuery

            SearchQuery.objects.create(
                user=request.user,
                query=query or "",
                category_filter=category or "",
                location_filter=location or "",
                results_count=queryset.count(),
            )

        # Serialize results
        serializer = CharityCaseListSerializer(queryset, many=True)
        return Response({"count": queryset.count(), "results": serializer.data})


class CaseCategoriesView(APIView):
    """API view for getting case categories"""

    permission_classes = [AllowAny]

    def get(self, request):
        """Get available case categories with counts"""
        categories = (
            CharityCase.objects.filter(verification_status="approved")
            .values("category")
            .annotate(
                count=Count("id"),
                total_target=Sum("target_amount"),
                total_collected=Sum("collected_amount"),
            )
            .order_by("category")
        )

        return Response(
            {
                "categories": list(categories),
                "choices": [
                    {"value": choice[0], "label": choice[1]}
                    for choice in CharityCase.CATEGORY_CHOICES
                ],
            }
        )


class CaseStatsView(APIView):
    """API view for case statistics"""

    permission_classes = [AllowAny]

    def get(self, request):
        """Get case statistics"""
        # Overall stats
        total_cases = CharityCase.objects.filter(verification_status="approved").count()
        completed_cases = CharityCase.objects.filter(
            verification_status="approved", collected_amount__gte=F("target_amount")
        ).count()
        active_cases = total_cases - completed_cases

        # Financial stats
        financial_stats = CharityCase.objects.filter(
            verification_status="approved"
        ).aggregate(
            total_target=Sum("target_amount"),
            total_collected=Sum("collected_amount"),
            avg_target=Avg("target_amount"),
        )

        # Category breakdown
        category_stats = (
            CharityCase.objects.filter(verification_status="approved")
            .values("category")
            .annotate(count=Count("id"), total_collected=Sum("collected_amount"))
            .order_by("-count")
        )

        # Recent activity
        recent_cases = CharityCase.objects.filter(
            verification_status="approved"
        ).order_by("-created_at")[:5]

        return Response(
            {
                "total_cases": total_cases,
                "active_cases": active_cases,
                "completed_cases": completed_cases,
                "completion_rate": (
                    (completed_cases / total_cases * 100) if total_cases > 0 else 0
                ),
                "financial": {
                    "total_target": financial_stats["total_target"] or 0,
                    "total_collected": financial_stats["total_collected"] or 0,
                    "average_target": financial_stats["avg_target"] or 0,
                    "collection_rate": (
                        financial_stats["total_collected"]
                        / financial_stats["total_target"]
                        * 100
                        if financial_stats["total_target"]
                        and financial_stats["total_target"] > 0
                        else 0
                    ),
                },
                "by_category": list(category_stats),
                "recent_cases": CharityCaseListSerializer(recent_cases, many=True).data,
            }
        )


class FeaturedCasesView(APIView):
    """API view for featured/trending cases"""

    permission_classes = [AllowAny]

    def get(self, request):
        """Get featured cases based on various criteria"""
        # Urgent cases
        urgent_cases = CharityCase.objects.filter(
            verification_status="approved", urgency_flag="critical"
        ).order_by("-created_at")[:3]

        # Nearly completed cases
        from django.db.models import F

        nearly_completed = CharityCase.objects.filter(
            verification_status="approved",
            collected_amount__gte=F("target_amount") * 0.8,
            collected_amount__lt=F("target_amount"),
        ).order_by("-created_at")[:3]

        # Popular cases (most donations)
        popular_cases = (
            CharityCase.objects.filter(verification_status="approved")
            .annotate(donation_count=Count("donations"))
            .order_by("-donation_count")[:3]
        )

        # New cases
        new_cases = CharityCase.objects.filter(
            verification_status="approved",
            created_at__gte=timezone.now() - timedelta(days=7),
        ).order_by("-created_at")[:3]

        return Response(
            {
                "urgent": CharityCaseListSerializer(urgent_cases, many=True).data,
                "nearly_completed": CharityCaseListSerializer(
                    nearly_completed, many=True
                ).data,
                "popular": CharityCaseListSerializer(popular_cases, many=True).data,
                "new": CharityCaseListSerializer(new_cases, many=True).data,
            }
        )


class PendingCasesView(APIView):
    """API view for pending cases (admin only)"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        """Get pending cases for admin review"""
        pending_cases = CharityCase.objects.filter(
            verification_status="pending"
        ).order_by("-created_at")

        serializer = CharityCaseListSerializer(pending_cases, many=True)
        return Response({"count": pending_cases.count(), "results": serializer.data})


class BulkApprovalView(APIView):
    """API view for bulk case approval (admin only)"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        """Bulk approve or reject cases"""
        case_ids = request.data.get("case_ids", [])
        action = request.data.get("action")  # 'approve' or 'reject'

        if not case_ids or action not in ["approve", "reject"]:
            return Response(
                {"error": "case_ids and valid action are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        status_value = "approved" if action == "approve" else "rejected"

        updated_count = CharityCase.objects.filter(
            id__in=case_ids, verification_status="pending"
        ).update(verification_status=status_value, approved_by=request.user)

        return Response(
            {
                "message": f"{updated_count} cases {action}d successfully",
                "updated_count": updated_count,
            }
        )
