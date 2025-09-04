"""
Khalti payment gateway integration utilities for CharityNepal
"""

import hashlib
import hmac
import json
import uuid
from decimal import Decimal
from typing import Any, Dict, Optional

import requests
from django.conf import settings
from django.urls import reverse


class KhaltiPaymentGateway:
    """
    Khalti Payment Gateway integration for Nepal
    """

    # Khalti API endpoints
    KHALTI_GATEWAY_URL = "https://a.khalti.com/api/v2/epayment/initiate/"
    KHALTI_VERIFY_URL = "https://a.khalti.com/api/v2/epayment/lookup/"

    # Test endpoints (for development)
    TEST_GATEWAY_URL = "https://a.khalti.com/api/v2/epayment/initiate/"
    TEST_VERIFY_URL = "https://a.khalti.com/api/v2/epayment/lookup/"

    def __init__(self):
        """Initialize Khalti gateway with settings"""
        self.secret_key = getattr(settings, "KHALTI_SECRET_KEY", "")
        self.public_key = getattr(settings, "KHALTI_PUBLIC_KEY", "")
        self.is_live = getattr(settings, "KHALTI_LIVE_MODE", False)

        if not self.secret_key or not self.public_key:
            raise ValueError("Khalti API keys are not configured in settings")

    def generate_payment_reference(self) -> str:
        """Generate unique payment reference"""
        return f"CN-{uuid.uuid4().hex[:12].upper()}"

    def initiate_payment(
        self,
        amount: Decimal,
        donation_id: int,
        donor_name: str,
        donor_email: str,
        case_title: str,
        request,
    ) -> Dict[str, Any]:
        """
        Initiate payment with Khalti

        Args:
            amount: Donation amount in NPR
            donation_id: Database donation ID
            donor_name: Name of the donor
            donor_email: Email of the donor
            case_title: Title of the charity case
            request: Django request object for building URLs

        Returns:
            Dict containing payment initiation response
        """
        # Convert amount to paisa (Khalti uses paisa as base unit)
        amount_in_paisa = int(amount * 100)

        # Generate unique purchase order ID
        purchase_order_id = self.generate_payment_reference()

        # Build URLs
        return_url = request.build_absolute_uri(
            reverse("donations:khalti_success", kwargs={"donation_id": donation_id})
        )
        website_url = request.build_absolute_uri("/")

        # Prepare payload
        payload = {
            "return_url": return_url,
            "website_url": website_url,
            "amount": amount_in_paisa,
            "purchase_order_id": purchase_order_id,
            "purchase_order_name": f"Donation to {case_title[:50]}",
            "customer_info": {
                "name": donor_name,
                "email": donor_email,
            },
            "amount_breakdown": [
                {"label": "Donation Amount", "amount": amount_in_paisa}
            ],
            "product_details": [
                {
                    "identity": str(donation_id),
                    "name": f"Donation to {case_title}",
                    "total_price": amount_in_paisa,
                    "quantity": 1,
                    "unit_price": amount_in_paisa,
                }
            ],
        }

        headers = {
            "Authorization": f"key {self.secret_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                self.KHALTI_GATEWAY_URL,
                headers=headers,
                data=json.dumps(payload),
                timeout=30,
            )
            response.raise_for_status()
            return {
                "success": True,
                "data": response.json(),
                "purchase_order_id": purchase_order_id,
            }
        except requests.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to initiate payment with Khalti",
            }

    def verify_payment(self, pidx: str) -> Dict[str, Any]:
        """
        Verify payment status with Khalti

        Args:
            pidx: Payment index from Khalti callback

        Returns:
            Dict containing verification response
        """
        headers = {
            "Authorization": f"key {self.secret_key}",
            "Content-Type": "application/json",
        }

        payload = {"pidx": pidx}

        try:
            response = requests.post(
                self.KHALTI_VERIFY_URL,
                headers=headers,
                data=json.dumps(payload),
                timeout=30,
            )
            response.raise_for_status()
            verification_data = response.json()

            return {
                "success": True,
                "data": verification_data,
                "status": verification_data.get("status", "unknown").lower(),
                "transaction_id": verification_data.get("transaction_id"),
                "amount": Decimal(str(verification_data.get("total_amount", 0)))
                / 100,  # Convert from paisa
            }
        except requests.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to verify payment with Khalti",
            }

    def generate_signature(self, data: dict) -> str:
        """
        Generate HMAC signature for webhook verification

        Args:
            data: Webhook payload data

        Returns:
            HMAC signature string
        """
        message = json.dumps(data, sort_keys=True, separators=(",", ":"))
        signature = hmac.new(
            self.secret_key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        return signature

    def verify_webhook_signature(self, payload: dict, signature: str) -> bool:
        """
        Verify webhook signature

        Args:
            payload: Webhook payload
            signature: Received signature

        Returns:
            True if signature is valid
        """
        expected_signature = self.generate_signature(payload)
        return hmac.compare_digest(expected_signature, signature)


# Singleton instance
khalti_gateway = KhaltiPaymentGateway()
