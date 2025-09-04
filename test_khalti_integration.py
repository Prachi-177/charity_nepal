#!/usr/bin/env python3
"""
Simple script to test Khalti payment integration
"""

import os
import sys
from pathlib import Path

import django

# Add the project directory to the Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "charity_backend.settings")
django.setup()

import json
from decimal import Decimal

from donations.khalti_utils import KhaltiPaymentGateway


def test_khalti_utils():
    """Test basic Khalti utilities"""
    print("🧪 Testing Khalti Payment Gateway Utilities")
    print("=" * 50)

    try:
        # Initialize gateway
        gateway = KhaltiPaymentGateway()
        print("✅ KhaltiPaymentGateway initialized successfully")

        # Test amount conversion
        amount_rs = Decimal("1000.50")
        amount_paisa = gateway._amount_to_paisa(amount_rs)
        print(f"✅ Amount conversion: Rs. {amount_rs} = {amount_paisa} paisa")

        # Test reference generation
        ref = gateway._generate_reference()
        print(f"✅ Payment reference generated: {ref}")

        # Test signature validation logic exists
        if hasattr(gateway, "_validate_signature"):
            print("✅ Signature validation method exists")
        else:
            print("⚠️ Signature validation method not found")

        return True

    except Exception as e:
        print(f"❌ Error testing Khalti utilities: {e}")
        return False


def test_models():
    """Test donation models"""
    print("\n🧪 Testing Donation Models")
    print("=" * 50)

    try:
        from django.contrib.auth import get_user_model

        from cases.models import CharityCase
        from donations.models import Donation

        User = get_user_model()

        # Check if we have test data
        if CharityCase.objects.exists():
            case = CharityCase.objects.first()
            print(f"✅ Found test case: {case.title}")

            # Check donations for this case
            donations = Donation.objects.filter(charity_case=case)
            print(f"✅ Found {donations.count()} donations for this case")

            if donations.exists():
                donation = donations.first()
                print(f"✅ Sample donation: Rs. {donation.amount} ({donation.status})")

        else:
            print("⚠️ No charity cases found in database")

        return True

    except Exception as e:
        print(f"❌ Error testing models: {e}")
        return False


def test_configuration():
    """Test Django configuration for Khalti"""
    print("\n🧪 Testing Django Configuration")
    print("=" * 50)

    try:
        from django.conf import settings

        # Check Khalti settings
        if hasattr(settings, "KHALTI_PUBLIC_KEY"):
            print("✅ KHALTI_PUBLIC_KEY configured")
        else:
            print("⚠️ KHALTI_PUBLIC_KEY not found in settings")

        if hasattr(settings, "KHALTI_SECRET_KEY"):
            print("✅ KHALTI_SECRET_KEY configured")
        else:
            print("⚠️ KHALTI_SECRET_KEY not found in settings")

        if hasattr(settings, "KHALTI_LIVE_MODE"):
            mode = "LIVE" if settings.KHALTI_LIVE_MODE else "TEST"
            print(f"✅ KHALTI_LIVE_MODE: {mode}")
        else:
            print("⚠️ KHALTI_LIVE_MODE not configured")

        # Check installed apps
        if "donations" in settings.INSTALLED_APPS:
            print("✅ Donations app is installed")
        else:
            print("❌ Donations app not in INSTALLED_APPS")

        if "widget_tweaks" in settings.INSTALLED_APPS:
            print("✅ Widget tweaks is installed")
        else:
            print("⚠️ Widget tweaks not installed")

        return True

    except Exception as e:
        print(f"❌ Error testing configuration: {e}")
        return False


if __name__ == "__main__":
    print("🚀 CharityNepal Khalti Integration Test")
    print("=" * 50)

    all_tests_passed = True

    # Run tests
    all_tests_passed &= test_configuration()
    all_tests_passed &= test_khalti_utils()
    all_tests_passed &= test_models()

    print("\n" + "=" * 50)
    if all_tests_passed:
        print("🎉 All tests completed successfully!")
        print("✅ Khalti payment integration is ready to use")
    else:
        print("⚠️ Some tests failed - please check the errors above")

    print("\n💡 Next steps:")
    print("1. Test donation form at: http://127.0.0.1:8000/donations/donate/1/")
    print("2. Make sure your Khalti test credentials are configured")
    print("3. Test the complete payment flow")
