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
from donations.khalti_utils import khalti_gateway

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
            donation = get_object_or_404(Donation, id=donation_id, donor=request.user)

            # Get the Khalti gateway
            gateway = PaymentIntent.objects.get(name="khalti")

            # Create payment intent
            payment_intent = PaymentIntent.objects.create(
                donation=donation,
                gateway=gateway,
                amount=donation.amount,
                currency="NPR",
                status="pending",
                return_url=request.build_absolute_uri(f"/donations/khalti/success/{donation.id}/"),
                cancel_url=request.build_absolute_uri(f"/donations/khalti/failed/{donation.id}/"),
                expires_at=timezone.now() + timezone.timedelta(hours=1)
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
            logger.error(f"Error getting payment intent: {str(e)}")
            return Response(
                {"error": "Payment intent not found"},
                status=status.HTTP_404_NOT_FOUND,
            )


class KhaltiVerificationView(APIView):
    """Verify Khalti payment"""

    def post(self, request):
        try:
            payment_intent_id = request.data.get("payment_intent_id")
            pidx = request.data.get("pidx")

            payment_intent = get_object_or_404(PaymentIntent, id=payment_intent_id)
            
            # Verify payment with Khalti
            verification = khalti_gateway.verify_payment(pidx)

            if verification["success"]:
                # Update payment intent
                payment_intent.status = "succeeded"
                payment_intent.gateway_payment_id = verification["transaction_id"]
                payment_intent.processed_at = timezone.now()
                payment_intent.save()

                # Update donation
                donation = payment_intent.donation
                donation.status = "completed"
                donation.transaction_id = verification["transaction_id"]
                donation.completed_at = timezone.now()
                donation.save()

                # Update case collected amount
                donation.case.update_collected_amount()

                return Response({
                    "status": "success",
                    "message": "Payment verified successfully"
                })
            else:
                return Response(
                    {"error": "Payment verification failed"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            logger.error(f"Error verifying Khalti payment: {str(e)}")
            return Response(
                {"error": "Payment verification failed"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class KhaltiWebhookView(APIView):
    """Handle Khalti webhook"""

    def post(self, request):
        try:
            # Verify webhook signature
            signature = request.headers.get("Khalti-Signature")
            if not khalti_gateway.verify_webhook_signature(request.body, signature):
                return Response(
                    {"error": "Invalid webhook signature"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Process webhook data
            payload = json.loads(request.body)
            event_type = payload.get("type")
            payment_data = payload.get("data", {})

            if event_type == "payment.completed":
                pidx = payment_data.get("pidx")
                if pidx:
                    # Find and update payment intent
                    try:
                        payment_intent = PaymentIntent.objects.get(
                            gateway_payment_id=pidx
                        )
                        payment_intent.status = "succeeded"
                        payment_intent.processed_at = timezone.now()
                        payment_intent.save()

                        # Update donation status
                        donation = payment_intent.donation
                        donation.status = "completed"
                        donation.completed_at = timezone.now()
                        donation.save()

                        # Update case collected amount
                        donation.case.update_collected_amount()

                    except PaymentIntent.DoesNotExist:
                        logger.error(f"Payment intent not found for pidx: {pidx}")

            return Response({"status": "success"})

        except Exception as e:
            logger.error(f"Error processing Khalti webhook: {str(e)}")
            return Response(
                {"error": "Webhook processing failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class QRCodeView(APIView):
    """Generate QR code for payment"""

    def get(self, request, payment_intent_id):
        try:
            payment_intent = get_object_or_404(PaymentIntent, id=payment_intent_id)

            # Generate QR code data for Khalti
            qr_data = khalti_gateway.generate_qr_data(payment_intent)

            return Response(qr_data)

        except Exception as e:
            logger.error(f"Error generating QR code: {str(e)}")
            return Response(
                {"error": "Failed to generate QR code"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
