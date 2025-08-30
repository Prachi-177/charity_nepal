"""
API Integration Tests for Charity Nepal Backend
"""

import json
import sys
import time
from datetime import datetime

import requests


class APITester:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.token = None
        self.test_user_id = None
        self.test_case_id = None
        self.test_donation_id = None
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def log(self, message, status="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {status}: {message}")

    def test_user_registration(self):
        """Test user registration endpoint"""
        self.log("Testing user registration...")

        data = {
            "email": f"test_user_{int(time.time())}@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
            "first_name": "Test",
            "last_name": "User",
            "phone": "9801234567",
            "role": "donor",
        }

        response = self.session.post(f"{self.base_url}/api/auth/register/", json=data)

        if response.status_code == 201:
            self.log("✅ User registration successful")
            return True
        else:
            self.log(f"❌ User registration failed: {response.text}", "ERROR")
            return False

    def test_user_login(self):
        """Test user login and token generation"""
        self.log("Testing user login...")

        # First register a user
        timestamp = int(time.time())
        email = f"test_login_{timestamp}@example.com"
        password = "StrongPassword123!"

        register_data = {
            "email": email,
            "password": password,
            "password_confirm": password,
            "first_name": "Test",
            "last_name": "Login",
            "role": "donor",
        }

        reg_response = self.session.post(
            f"{self.base_url}/api/auth/register/", json=register_data
        )

        if reg_response.status_code != 201:
            self.log(f"❌ Could not register test user: {reg_response.text}", "ERROR")
            return False

        # Now test login
        login_data = {"email": email, "password": password}

        response = self.session.post(
            f"{self.base_url}/api/auth/login/", json=login_data
        )

        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.test_user_id = data.get("user", {}).get("id")

            # Set authorization header for future requests
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})

            self.log("✅ User login successful")
            return True
        else:
            self.log(f"❌ User login failed: {response.text}", "ERROR")
            return False

    def test_create_charity_case(self):
        """Test creating a charity case"""
        self.log("Testing charity case creation...")

        if not self.token:
            self.log("❌ No authentication token available", "ERROR")
            return False

        data = {
            "title": f"Test Charity Case {int(time.time())}",
            "description": "This is a test charity case for API testing purposes.",
            "category": "health",
            "target_amount": "50000.00",
            "urgency_level": "medium",
            "location": "Kathmandu, Nepal",
            "tags": "test,api,charity",
            "end_date": "2024-12-31",
        }

        response = self.session.post(f"{self.base_url}/api/cases/", json=data)

        if response.status_code == 201:
            case_data = response.json()
            self.test_case_id = case_data.get("id")
            self.log(f"✅ Charity case created successfully (ID: {self.test_case_id})")
            return True
        else:
            self.log(f"❌ Charity case creation failed: {response.text}", "ERROR")
            return False

    def test_list_charity_cases(self):
        """Test listing charity cases"""
        self.log("Testing charity case listing...")

        response = self.session.get(f"{self.base_url}/api/cases/")

        if response.status_code == 200:
            data = response.json()
            case_count = len(data.get("results", []))
            self.log(f"✅ Retrieved {case_count} charity cases")
            return True
        else:
            self.log(f"❌ Failed to retrieve charity cases: {response.text}", "ERROR")
            return False

    def test_create_donation(self):
        """Test creating a donation"""
        self.log("Testing donation creation...")

        if not self.token or not self.test_case_id:
            self.log("❌ Missing authentication token or case ID", "ERROR")
            return False

        data = {
            "case": self.test_case_id,
            "amount": "1000.00",
            "is_anonymous": False,
            "message": "Test donation for API testing",
        }

        response = self.session.post(f"{self.base_url}/api/donations/", json=data)

        if response.status_code == 201:
            donation_data = response.json()
            self.test_donation_id = donation_data.get("id")
            self.log(f"✅ Donation created successfully (ID: {self.test_donation_id})")
            return True
        else:
            self.log(f"❌ Donation creation failed: {response.text}", "ERROR")
            return False

    def test_get_recommendations(self):
        """Test personalized recommendations"""
        self.log("Testing personalized recommendations...")

        if not self.token:
            self.log("❌ No authentication token available", "ERROR")
            return False

        response = self.session.get(
            f"{self.base_url}/api/recommendations/personal/?count=5"
        )

        if response.status_code == 200:
            data = response.json()
            rec_count = len(data.get("recommendations", []))
            algorithm = data.get("algorithm_used", "unknown")
            self.log(
                f"✅ Retrieved {rec_count} recommendations using {algorithm} algorithm"
            )
            return True
        else:
            self.log(f"❌ Failed to get recommendations: {response.text}", "ERROR")
            return False

    def test_trending_cases(self):
        """Test trending cases endpoint"""
        self.log("Testing trending cases...")

        response = self.session.get(
            f"{self.base_url}/api/recommendations/trending/?count=5"
        )

        if response.status_code == 200:
            data = response.json()
            trending_count = len(data.get("trending_cases", []))
            self.log(f"✅ Retrieved {trending_count} trending cases")
            return True
        else:
            self.log(f"❌ Failed to get trending cases: {response.text}", "ERROR")
            return False

    def test_user_profile(self):
        """Test user profile retrieval and update"""
        self.log("Testing user profile management...")

        if not self.token:
            self.log("❌ No authentication token available", "ERROR")
            return False

        # Get current profile
        response = self.session.get(f"{self.base_url}/api/recommendations/profile/")

        if response.status_code == 200:
            profile_data = response.json()
            self.log(f"✅ Retrieved user profile")

            # Update profile
            update_data = {
                "preferred_categories": "health,education",
                "age_range": "25-34",
                "income_range": "50000-100000",
            }

            update_response = self.session.patch(
                f"{self.base_url}/api/recommendations/profile/", json=update_data
            )

            if update_response.status_code == 200:
                self.log("✅ User profile updated successfully")
                return True
            else:
                self.log(
                    f"❌ Failed to update profile: {update_response.text}", "ERROR"
                )
                return False
        else:
            self.log(f"❌ Failed to retrieve profile: {response.text}", "ERROR")
            return False

    def test_search_cases(self):
        """Test case search functionality"""
        self.log("Testing case search...")

        params = {"q": "health", "category": "health", "page_size": "10"}

        response = self.session.get(f"{self.base_url}/api/cases/search/", params=params)

        if response.status_code == 200:
            data = response.json()
            result_count = len(data.get("results", []))
            self.log(f"✅ Search returned {result_count} results")
            return True
        else:
            self.log(f"❌ Search failed: {response.text}", "ERROR")
            return False

    def run_all_tests(self):
        """Run all API tests"""
        self.log("🚀 Starting API Integration Tests")
        self.log("=" * 60)

        tests = [
            ("User Registration", self.test_user_registration),
            ("User Login", self.test_user_login),
            ("List Charity Cases", self.test_list_charity_cases),
            ("Create Charity Case", self.test_create_charity_case),
            ("Create Donation", self.test_create_donation),
            ("Get Recommendations", self.test_get_recommendations),
            ("Trending Cases", self.test_trending_cases),
            ("User Profile", self.test_user_profile),
            ("Search Cases", self.test_search_cases),
        ]

        results = []

        for test_name, test_func in tests:
            self.log(f"\n🧪 Running: {test_name}")
            self.log("-" * 40)

            try:
                result = test_func()
                results.append((test_name, result))

                if result:
                    self.log(f"✅ {test_name} completed successfully")
                else:
                    self.log(f"❌ {test_name} failed")

            except Exception as e:
                self.log(f"❌ {test_name} threw exception: {str(e)}", "ERROR")
                results.append((test_name, False))

            # Brief pause between tests
            time.sleep(0.5)

        # Print summary
        self.log("\n" + "=" * 60)
        self.log("📊 API TEST SUMMARY")
        self.log("=" * 60)

        passed = sum(1 for _, success in results if success)
        total = len(results)

        for test_name, success in results:
            status = "✅ PASSED" if success else "❌ FAILED"
            self.log(f"{status}: {test_name}")

        self.log(f"\nTotal: {total} | Passed: {passed} | Failed: {total - passed}")

        if passed == total:
            self.log("🎉 All API tests passed!")
            return True
        else:
            self.log(f"❌ {total - passed} API tests failed")
            return False


def main():
    """Main test runner"""
    import argparse

    parser = argparse.ArgumentParser(description="Run API integration tests")
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8000",
        help="Base URL for API server (default: http://127.0.0.1:8000)",
    )
    parser.add_argument(
        "--wait",
        type=int,
        default=5,
        help="Seconds to wait for server startup (default: 5)",
    )

    args = parser.parse_args()

    print(f"🔧 Testing API at: {args.url}")
    print(f"⏰ Waiting {args.wait} seconds for server startup...")
    time.sleep(args.wait)

    tester = APITester(args.url)
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
