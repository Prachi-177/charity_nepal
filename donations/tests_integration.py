"""
Test the Khalti payment integration
"""

import json
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from cases.models import CharityCase
from donations.khalti_utils import KhaltiPaymentGateway
from donations.models import Donation

User = get_user_model()


class KhaltiIntegrationTest(TestCase):
    def setUp(self):
        """Set up test data"""
        self.client = Client()

        # Create test user
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        # Create test charity case
        self.case = CharityCase.objects.create(
            title="Test Medical Case",
            description="Test description",
            target_amount=Decimal("50000.00"),
            category="medical",
            created_by=self.user,
            urgency_flag="high",
        )

    def test_donation_form_loads(self):
        """Test that donation form loads correctly"""
        self.client.login(username="testuser", password="testpass123")

        url = reverse("donations:create", args=[self.case.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Make a Donation")
        self.assertContains(response, "Khalti")

    @patch("donations.khalti_utils.requests.post")
    def test_khalti_payment_initiation(self, mock_post):
        """Test Khalti payment initiation"""
        # Mock Khalti API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "payment_url": "https://khalti.com/payment/test-url",
            "pidx": "test-pidx-123",
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        gateway = KhaltiPaymentGateway()
        result = gateway.initiate_payment(
            amount=Decimal("1000.00"),
            purchase_order_id="TEST-001",
            return_url="http://example.com/return",
            website_url="http://example.com",
        )

        self.assertTrue(result["success"])
        self.assertIn("payment_url", result)
        self.assertEqual(result["pidx"], "test-pidx-123")

    @patch("donations.khalti_utils.requests.post")
    def test_donation_creation_with_khalti(self, mock_post):
        """Test donation creation with Khalti payment method"""
        # Mock Khalti API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "payment_url": "https://khalti.com/payment/test-url",
            "pidx": "test-pidx-123",
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        self.client.login(username="testuser", password="testpass123")

        url = reverse("donations:create", args=[self.case.pk])
        data = {
            "amount": "1000.00",
            "payment_method": "khalti",
            "donor_message": "Test donation message",
            "is_anonymous": False,
        }

        response = self.client.post(url, data)

        # Should redirect to Khalti payment URL
        self.assertEqual(response.status_code, 302)

        # Check that donation was created
        donation = Donation.objects.filter(charity_case=self.case).first()
        self.assertIsNotNone(donation)
        self.assertEqual(donation.amount, Decimal("1000.00"))
        self.assertEqual(donation.payment_method, "khalti")
        self.assertEqual(donation.status, "pending")

    def test_anonymous_donation_form(self):
        """Test donation form for anonymous users"""
        url = reverse("donations:create", args=[self.case.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Donor Information")
        self.assertContains(response, "donor_name")
        self.assertContains(response, "donor_email")

    def test_authenticated_user_donation_form(self):
        """Test donation form for authenticated users"""
        self.client.login(username="testuser", password="testpass123")

        url = reverse("donations:create", args=[self.case.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Should not show donor info fields for authenticated users
        self.assertNotContains(response, "Donor Information")

    def test_donation_success_callback(self):
        """Test Khalti success callback"""
        # Create a pending donation first
        donation = Donation.objects.create(
            charity_case=self.case,
            donor=self.user,
            amount=Decimal("1000.00"),
            payment_method="khalti",
            status="pending",
            payment_reference="test-ref-123",
        )

        url = reverse("donations:khalti_success", args=[donation.pk])
        response = self.client.get(url + "?pidx=test-pidx&payment_id=test-payment-123")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Payment Successful")

    def test_donation_webhook_signature_validation(self):
        """Test webhook signature validation"""
        gateway = KhaltiPaymentGateway()

        # Test data
        payload = json.dumps({"test": "data"})
        secret_key = "test-secret-key"

        # Generate signature
        signature = gateway._generate_signature(payload, secret_key)

        # Validate signature
        is_valid = gateway._validate_signature(payload, signature, secret_key)
        self.assertTrue(is_valid)

        # Test invalid signature
        is_valid = gateway._validate_signature(payload, "invalid-signature", secret_key)
        self.assertFalse(is_valid)
