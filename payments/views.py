"""
Payment processing views
"""

import json
import logging

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from donations.models import Donation

from .models import PaymentIntent
from .serializers import PaymentIntentSerializer

User = get_user_model()
logger = logging.getLogger(__name__)


class CreatePaymentIntentView(APIView):
    """Create payment intent for donation"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            donation_id = request.data.get("donation_id")
            payment_method = request.data.get("payment_method", "esewa")

            donation = get_object_or_404(Donation, id=donation_id, donor=request.user)

            # Create payment intent
            payment_intent = PaymentIntent.objects.create(
                donation=donation,
                payment_method=payment_method,
                amount=donation.amount,
                currency="NPR",
                status="pending",
            )

            serializer = PaymentIntentSerializer(payment_intent)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating payment intent: {str(e)}")
            return Response(
                {"error": "Failed to create payment intent"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PaymentIntentDetailView(APIView):
    """Get payment intent details"""

    def get(self, request, payment_intent_id):
        try:
            payment_intent = get_object_or_404(PaymentIntent, id=payment_intent_id)
            serializer = PaymentIntentSerializer(payment_intent)
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Error retrieving payment intent: {str(e)}")
            return Response(
                {"error": "Payment intent not found"}, status=status.HTTP_404_NOT_FOUND
            )


class EsewaVerificationView(APIView):
    """Verify eSewa payment"""

    def post(self, request):
        try:
            payment_intent_id = request.data.get("payment_intent_id")
            transaction_code = request.data.get("transaction_code")

            payment_intent = get_object_or_404(PaymentIntent, id=payment_intent_id)

            # TODO: Implement actual eSewa verification API call
            # For now, simulate successful verification

            payment_intent.status = "completed"
            payment_intent.save()

            # Update donation status
            donation = payment_intent.donation
            donation.status = "completed"
            donation.completed_at = timezone.now()
            donation.save()

            return Response(
                {"status": "success", "message": "Payment verified successfully"}
            )

        except Exception as e:
            logger.error(f"Error verifying eSewa payment: {str(e)}")
            return Response(
                {"error": "Payment verification failed"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class KhaltiVerificationView(APIView):
    """Verify Khalti payment"""

    def post(self, request):
        try:
            payment_intent_id = request.data.get("payment_intent_id")
            token = request.data.get("token")
            amount = request.data.get("amount")

            payment_intent = get_object_or_404(PaymentIntent, id=payment_intent_id)

            # TODO: Implement actual Khalti verification API call
            # For now, simulate successful verification

            payment_intent.status = "completed"
            payment_intent.save()

            # Update donation status
            donation = payment_intent.donation
            donation.status = "completed"
            donation.completed_at = timezone.now()
            donation.save()

            return Response(
                {"status": "success", "message": "Payment verified successfully"}
            )

        except Exception as e:
            logger.error(f"Error verifying Khalti payment: {str(e)}")
            return Response(
                {"error": "Payment verification failed"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class EsewaCallbackView(APIView):
    """Handle eSewa callback"""

    def post(self, request):
        # Handle eSewa payment callback
        return Response({"status": "received"})


class KhaltiWebhookView(APIView):
    """Handle Khalti webhook"""

    def post(self, request):
        # Handle Khalti webhook
        return Response({"status": "received"})


class QRCodeView(APIView):
    """Generate QR code for payment"""

    def get(self, request, payment_intent_id):
        try:
            payment_intent = get_object_or_404(PaymentIntent, id=payment_intent_id)

            # TODO: Generate actual QR code
            qr_data = {
                "payment_intent_id": payment_intent.id,
                "amount": str(payment_intent.amount),
                "currency": payment_intent.currency,
            }

            return Response(qr_data)

        except Exception as e:
            logger.error(f"Error generating QR code: {str(e)}")
            return Response(
                {"error": "Failed to generate QR code"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TransactionHistoryView(APIView):
    """Get transaction history"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            # Get user's payment intents
            payment_intents = PaymentIntent.objects.filter(
                donation__donor=request.user
            ).order_by("-created_at")

            serializer = PaymentIntentSerializer(payment_intents, many=True)
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Error retrieving transaction history: {str(e)}")
            return Response(
                {"error": "Failed to retrieve transactions"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PaymentAnalyticsView(APIView):
    """Get payment analytics (admin only)"""

    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        try:
            # Basic analytics
            total_payments = PaymentIntent.objects.filter(status="completed").count()
            total_amount = sum(
                pi.amount for pi in PaymentIntent.objects.filter(status="completed")
            )

            analytics = {
                "total_payments": total_payments,
                "total_amount": total_amount,
                "currency": "NPR",
            }

            return Response(analytics)

        except Exception as e:
            logger.error(f"Error generating payment analytics: {str(e)}")
            return Response(
                {"error": "Failed to generate analytics"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
