"""
Test runner script for comprehensive testing
"""

import os
import subprocess
import sys

import django
from django.conf import settings
from django.test.utils import get_runner

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "charity_backend.settings")
django.setup()


def run_tests():
    """Run comprehensive test suite"""
    print("🚀 Starting Charity Nepal Backend Test Suite")
    print("=" * 60)

    # Test discovery and execution
    test_commands = [
        # Run all unit tests
        ["python", "manage.py", "test", "--verbosity=2"],
        # Check code style
        [
            "python",
            "-m",
            "flake8",
            ".",
            "--max-line-length=120",
            "--exclude=migrations,venv",
        ],
        # Run type checking if mypy is available
        ["python", "-m", "mypy", ".", "--ignore-missing-imports"],
        # Security checks
        ["python", "manage.py", "check", "--deploy"],
        # Migration checks
        ["python", "manage.py", "makemigrations", "--dry-run", "--check"],
    ]

    results = []

    for i, command in enumerate(test_commands, 1):
        test_name = command[2] if len(command) > 2 else command[1]
        print(f"\n📋 Test {i}: {test_name.upper()}")
        print("-" * 40)

        try:
            result = subprocess.run(
                command, capture_output=True, text=True, timeout=300  # 5 minute timeout
            )

            if result.returncode == 0:
                print(f"✅ {test_name} passed")
                results.append((test_name, True, result.stdout))
            else:
                print(f"❌ {test_name} failed")
                print(f"Error: {result.stderr}")
                results.append((test_name, False, result.stderr))

        except subprocess.TimeoutExpired:
            print(f"⏰ {test_name} timed out")
            results.append((test_name, False, "Test timed out"))
        except FileNotFoundError:
            print(f"⚠️ {test_name} tool not found, skipping")
            results.append((test_name, None, "Tool not available"))

    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, success, _ in results if success is True)
    failed = sum(1 for _, success, _ in results if success is False)
    skipped = sum(1 for _, success, _ in results if success is None)

    for test_name, success, output in results:
        if success is True:
            print(f"✅ {test_name}")
        elif success is False:
            print(f"❌ {test_name}")
        else:
            print(f"⚠️ {test_name} (skipped)")

    print(
        f"\nTotal: {len(results)} | Passed: {passed} | Failed: {failed} | Skipped: {skipped}"
    )

    if failed > 0:
        print("\n❌ Some tests failed. Check output above for details.")
        return False
    else:
        print("\n🎉 All available tests passed!")
        return True


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
