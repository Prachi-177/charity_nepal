#!/usr/bin/env python
"""
Quick script to check database status for ML algorithms
"""
import os
import sys

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "charity_backend.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.db import models

from cases.models import CharityCase


def main():
    User = get_user_model()

    print("=== DATABASE STATUS ===")
    print(f"Total Users: {User.objects.count()}")
    print(f"Total Cases: {CharityCase.objects.count()}")
    print(
        f'Approved Cases: {CharityCase.objects.filter(verification_status="approved").count()}'
    )

    try:
        from donations.models import Donation

        print(f"Total Donations: {Donation.objects.count()}")
        print(
            f'Completed Donations: {Donation.objects.filter(status="completed").count()}'
        )
    except ImportError:
        print("Donations model not found")

    print("\n=== SAMPLE DATA CHECK ===")
    if CharityCase.objects.exists():
        case = CharityCase.objects.first()
        print(f"Sample Case: {case.title[:50]}...")
        print(f"Category: {case.category}")
        print(f"Target Amount: {case.target_amount}")
        print(f"Status: {case.verification_status}")
    else:
        print("No cases in database")

    print("\n=== CATEGORIES BREAKDOWN ===")
    categories = (
        CharityCase.objects.values("category")
        .annotate(count=models.Count("id"))
        .order_by("-count")
    )
    for cat in categories:
        print(f'{cat["category"]}: {cat["count"]} cases')

    print("\n=== ML ALGORITHM STATUS ===")
    approved_cases = CharityCase.objects.filter(verification_status="approved").count()
    if approved_cases >= 5:
        print("✅ Content-Based Filtering: Ready (needs 5+ cases)")
    else:
        print(
            f"❌ Content-Based Filtering: Need {5 - approved_cases} more approved cases"
        )

    try:
        from donations.models import Donation

        completed_donations = Donation.objects.filter(status="completed").count()
        if completed_donations >= 10:
            print("✅ Hybrid Recommendations: Ready (needs 10+ donations)")
        else:
            print(
                f"❌ Hybrid Recommendations: Need {10 - completed_donations} more completed donations"
            )
    except ImportError:
        print("❌ Hybrid Recommendations: Donations model not available")

    print("\n=== WHAT YOU NEED TO DO ===")
    if approved_cases < 5:
        print("1. Create and approve at least 5 charity cases")
    if approved_cases >= 5:
        print("✅ You have enough cases for basic ML features")

    try:
        from donations.models import Donation

        if Donation.objects.filter(status="completed").count() < 10:
            print("2. Add some donation data for better recommendations")
    except ImportError:
        print("2. Set up the donations app for full ML functionality")


if __name__ == "__main__":
    main()
