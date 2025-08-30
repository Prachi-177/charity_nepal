from datetime import timedelta

import jwt
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.crypto import get_random_string
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from rest_framework_simplejwt.tokens import RefreshToken

from .permissions import IsOwnerOrReadOnly
from .serializers import (
    PasswordChangeSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    UserRegistrationSerializer,
)

User = get_user_model()


class UserRegistrationView(APIView):
    """API view for user registration"""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)

            # Send welcome email (optional)
            if hasattr(settings, "EMAIL_HOST_USER") and settings.EMAIL_HOST_USER:
                try:
                    send_mail(
                        "Welcome to Charity Nepal",
                        f"Welcome {user.first_name}! Your account has been created successfully.",
                        settings.EMAIL_HOST_USER,
                        [user.email],
                        fail_silently=True,
                    )
                except Exception:
                    pass  # Don't fail registration if email fails

            return Response(
                {
                    "message": "User registered successfully",
                    "user": UserProfileSerializer(user).data,
                    "tokens": {
                        "access": str(refresh.access_token),
                        "refresh": str(refresh),
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    """API view for user login"""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)

            return Response(
                {
                    "message": "Login successful",
                    "user": UserProfileSerializer(user).data,
                    "tokens": {
                        "access": str(refresh.access_token),
                        "refresh": str(refresh),
                    },
                },
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLogoutView(APIView):
    """API view for user logout"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            # Get the refresh token from request
            refresh_token = request.data.get("refresh_token")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()

            return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST
            )


class UserProfileViewSet(ModelViewSet):
    """ViewSet for user profile management"""

    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        """Return user's own profile"""
        return User.objects.filter(id=self.request.user.id)

    def get_object(self):
        """Return current user"""
        return self.request.user

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action in ["update", "partial_update"]:
            return UserProfileUpdateSerializer
        return UserProfileSerializer

    @action(detail=False, methods=["get"])
    def me(self, request):
        """Get current user's profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def donation_history(self, request):
        """Get user's donation history"""
        from donations.serializers import DonationHistorySerializer

        donations = request.user.donations.all().order_by("-created_at")

        # Pagination
        page = self.paginate_queryset(donations)
        if page is not None:
            serializer = DonationHistorySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = DonationHistorySerializer(donations, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get user's donation statistics"""
        from django.db.models import Avg, Count, Sum

        from donations.models import Donation

        user_donations = request.user.donations.filter(status="completed")
        stats = user_donations.aggregate(
            total_donated=Sum("amount"),
            total_donations=Count("id"),
            avg_donation=Avg("amount"),
        )

        # Category breakdown
        category_stats = {}
        for donation in user_donations.select_related("case"):
            category = donation.case.category
            if category not in category_stats:
                category_stats[category] = {"count": 0, "amount": 0}
            category_stats[category]["count"] += 1
            category_stats[category]["amount"] += float(donation.amount)

        return Response(
            {
                "total_donated": stats["total_donated"] or 0,
                "total_donations": stats["total_donations"] or 0,
                "average_donation": stats["avg_donation"] or 0,
                "category_breakdown": category_stats,
                "account_created": request.user.created_at,
                "last_donation": (
                    user_donations.order_by("-created_at").first().created_at
                    if user_donations.exists()
                    else None
                ),
            }
        )


class PasswordChangeView(APIView):
    """API view for changing password"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            # Use a custom method to update password
            user = request.user
            new_password = serializer.validated_data["new_password"]
            user.set_password(new_password)
            user.save()

            return Response(
                {"message": "Password changed successfully"}, status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmailVerificationView(APIView):
    """API view for email verification"""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        token = request.data.get("token")
        if not token:
            return Response(
                {"error": "Token is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Decode token (implement your token logic)
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = payload["user_id"]
            user = User.objects.get(id=user_id)
            user.is_verified = True
            user.save()

            return Response(
                {"message": "Email verified successfully"}, status=status.HTTP_200_OK
            )

        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, User.DoesNotExist):
            return Response(
                {"error": "Invalid or expired token"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ResendVerificationView(APIView):
    """API view for resending verification email"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if request.user.is_verified:
            return Response(
                {"message": "Email is already verified"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generate verification token
        payload = {
            "user_id": request.user.id,
            "exp": timezone.now() + timedelta(hours=24),
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

        # Send verification email
        try:
            send_mail(
                "Verify Your Email - Charity Nepal",
                f"Please verify your email using this token: {token}",
                settings.EMAIL_HOST_USER,
                [request.user.email],
                fail_silently=False,
            )

            return Response(
                {"message": "Verification email sent"}, status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": "Failed to send verification email"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PasswordResetView(APIView):
    """API view for password reset request"""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response(
                {"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)

            # Generate reset token
            payload = {"user_id": user.id, "exp": timezone.now() + timedelta(hours=1)}
            token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

            # Send reset email
            send_mail(
                "Password Reset - Charity Nepal",
                f"Use this token to reset your password: {token}",
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )

            return Response(
                {"message": "Password reset email sent"}, status=status.HTTP_200_OK
            )

        except User.DoesNotExist:
            # Don't reveal if email exists
            return Response(
                {"message": "If email exists, reset instructions have been sent"},
                status=status.HTTP_200_OK,
            )

        except Exception:
            return Response(
                {"error": "Failed to send reset email"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PasswordResetConfirmView(APIView):
    """API view for password reset confirmation"""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        token = request.data.get("token")
        new_password = request.data.get("new_password")

        if not token or not new_password:
            return Response(
                {"error": "Token and new password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = payload["user_id"]
            user = User.objects.get(id=user_id)

            # Validate password
            from django.contrib.auth.password_validation import validate_password

            validate_password(new_password)

            user.set_password(new_password)
            user.save()

            return Response(
                {"message": "Password reset successfully"}, status=status.HTTP_200_OK
            )

        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, User.DoesNotExist):
            return Response(
                {"error": "Invalid or expired token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            return Response(
                {"error": "Password validation failed"},
                status=status.HTTP_400_BAD_REQUEST,
            )
