import random
from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.text import slugify

from cases.models import CaseUpdate, CharityCase
from donations.models import Donation

User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database with sample data for CharityNepal"

    def add_arguments(self, parser):
        parser.add_argument(
            "--users",
            type=int,
            default=20,
            help="Number of users to create (default: 20)",
        )
        parser.add_argument(
            "--cases",
            type=int,
            default=30,
            help="Number of charity cases to create (default: 30)",
        )
        parser.add_argument(
            "--donations",
            type=int,
            default=100,
            help="Number of donations to create (default: 100)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing data before seeding",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write(self.style.WARNING("Clearing existing data..."))
            Donation.objects.all().delete()
            CaseUpdate.objects.all().delete()
            CharityCase.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.SUCCESS("Existing data cleared."))

        # Create admin user if not exists
        self.create_admin_user()

        # Create sample users
        users, created_users = self.create_users(options["users"])
        total_users = len(users)
        self.stdout.write(
            self.style.SUCCESS(
                f"Users: {created_users} created, {total_users - created_users} existing, {total_users} total"
            )
        )

        # Create charity cases
        cases, created_cases = self.create_cases(users, options["cases"])
        total_cases = len(cases)
        self.stdout.write(
            self.style.SUCCESS(
                f"Cases: {created_cases} created, {total_cases - created_cases} existing, {total_cases} total"
            )
        )

        # Create case updates
        updates, created_updates = self.create_case_updates(cases, users)
        total_updates = len(updates)
        self.stdout.write(
            self.style.SUCCESS(
                f"Updates: {created_updates} created, {total_updates - created_updates} existing, {total_updates} total"
            )
        )

        # Create donations
        donations, created_donations = self.create_donations(
            users, cases, options["donations"]
        )
        total_donations = len(donations)
        self.stdout.write(
            self.style.SUCCESS(
                f"Donations: {created_donations} created, {total_donations - created_donations} existing, {total_donations} total"
            )
        )

        self.stdout.write(
            self.style.SUCCESS("Database seeding completed successfully!")
        )

    def create_admin_user(self):
        """Create admin user if doesn't exist"""
        if (
            not User.objects.filter(email="admin@charitynepal.org").exists()
            and not User.objects.filter(username="admin").exists()
        ):
            admin = User.objects.create_user(
                username="admin",
                email="admin@charitynepal.org",
                password="admin123",
                first_name="Admin",
                last_name="User",
                role="admin",
                is_staff=True,
                is_superuser=True,
                is_verified=True,
                phone="+977-9801234567",
                address="Kathmandu, Nepal",
            )
            self.stdout.write(
                self.style.SUCCESS(
                    "Admin user created: admin@charitynepal.org / admin123"
                )
            )
        else:
            self.stdout.write("Admin user already exists, skipping creation")

    def create_users(self, count):
        """Create sample users"""
        users = []
        created_count = 0

        # Sample Nepali names and locations
        first_names = [
            "Bibek",
            "Sita",
            "Ram",
            "Maya",
            "Krishna",
            "Gita",
            "Arjun",
            "Shanti",
            "Prakash",
            "Kamala",
            "Rajesh",
            "Sunita",
            "Dipesh",
            "Radha",
            "Mahesh",
            "Laxmi",
            "Suresh",
            "Prabha",
            "Naresh",
            "Mina",
            "Ramesh",
            "Sangita",
            "Deepak",
            "Sushila",
            "Ganesh",
            "Urmila",
            "Bikash",
            "Sarita",
            "Umesh",
            "Bina",
        ]

        last_names = [
            "Sharma",
            "Shrestha",
            "Gurung",
            "Tamang",
            "Rai",
            "Limbu",
            "Magar",
            "Thapa",
            "Poudel",
            "Adhikari",
            "Khadka",
            "Basnet",
            "KC",
            "Bhandari",
            "Koirala",
            "Regmi",
            "Subedi",
            "Karki",
            "Acharya",
            "Bhattarai",
        ]

        locations = [
            "Kathmandu",
            "Pokhara",
            "Lalitpur",
            "Bhaktapur",
            "Chitwan",
            "Dharan",
            "Butwal",
            "Nepalgunj",
            "Birgunj",
            "Janakpur",
            "Hetauda",
            "Dhangadhi",
            "Siddharthanagar",
            "Mahendranagar",
            "Gorkha",
            "Baglung",
            "Tansen",
            "Ilam",
            "Biratnagar",
            "Rajbiraj",
        ]

        for i in range(count):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            email = f"{first_name.lower()}.{last_name.lower()}{i}@email.com"
            username = f"{first_name.lower()}{last_name.lower()}{i}"

            # Skip if user already exists
            if User.objects.filter(email=email).exists():
                existing_user = User.objects.get(email=email)
                users.append(existing_user)
                continue

            if User.objects.filter(username=username).exists():
                # If username exists but email doesn't, modify username
                username = f"{username}_{random.randint(1000, 9999)}"

            user = User.objects.create_user(
                username=username,
                email=email,
                password="password123",
                first_name=first_name,
                last_name=last_name,
                role=random.choice(["donor"]),  # Most users are donors
                is_verified=random.choice([True, False]),
                phone=f"+977-98{random.randint(10000000, 99999999)}",
                address=f"{random.choice(locations)}, Nepal",
            )
            users.append(user)
            created_count += 1

        return users, created_count

    def create_cases(self, users, count):
        """Create sample charity cases"""
        cases = []
        created_count = 0

        # Sample case data for different categories
        case_templates = {
            "cancer": [
                {
                    "title": "Help {name} Fight Cancer",
                    "description": "{name}, a {age}-year-old from {location}, has been diagnosed with {cancer_type} cancer. The family is struggling to afford the expensive treatment and medication required. Your donation can help save {name}'s life and give them a fighting chance against this deadly disease.",
                    "beneficiary_ages": [25, 45, 60, 35, 28, 55],
                    "cancer_types": [
                        "lung",
                        "breast",
                        "liver",
                        "blood",
                        "bone",
                        "brain",
                    ],
                    "amounts": [50000, 75000, 100000, 150000, 200000, 300000],
                }
            ],
            "accident": [
                {
                    "title": "Emergency Surgery for {name} After Road Accident",
                    "description": "{name}, {age} years old, was severely injured in a road accident in {location}. Multiple surgeries and long-term rehabilitation are needed. The family cannot afford the mounting medical bills. Please help {name} recover and get back to a normal life.",
                    "beneficiary_ages": [20, 30, 45, 25, 35, 40],
                    "amounts": [30000, 50000, 75000, 100000, 125000],
                }
            ],
            "education": [
                {
                    "title": "Support {name}'s Education Dream",
                    "description": "{name} is a bright {age}-year-old student from {location} who dreams of becoming a doctor/engineer. Despite excellent grades, the family cannot afford school fees and educational materials. Help {name} continue their education and build a better future.",
                    "beneficiary_ages": [16, 17, 18, 19, 20, 21],
                    "amounts": [15000, 25000, 35000, 50000, 75000],
                }
            ],
            "medical": [
                {
                    "title": "Medical Treatment for {name}",
                    "description": "{name}, a {age}-year-old from {location}, is suffering from a serious medical condition that requires immediate treatment. The family is facing financial hardship and cannot afford the necessary medical care. Your support can help {name} get the treatment they desperately need.",
                    "beneficiary_ages": [30, 45, 60, 25, 35, 50],
                    "amounts": [25000, 40000, 60000, 80000, 120000],
                }
            ],
            "disaster": [
                {
                    "title": "Disaster Relief for {name}'s Family",
                    "description": "{name}'s family from {location} has lost everything in a natural disaster. Their house was destroyed, and they have no shelter or basic necessities. Help this family rebuild their life and get back on their feet during this difficult time.",
                    "beneficiary_ages": [35, 40, 45, 50, 30],
                    "amounts": [20000, 35000, 50000, 75000, 100000],
                }
            ],
        }

        nepal_locations = [
            "Kathmandu",
            "Pokhara",
            "Lalitpur",
            "Bhaktapur",
            "Chitwan",
            "Dharan",
            "Butwal",
            "Nepalgunj",
            "Birgunj",
            "Janakpur",
            "Hetauda",
            "Gorkha",
            "Baglung",
            "Tansen",
            "Ilam",
            "Biratnagar",
            "Palpa",
            "Syangja",
        ]

        nepali_names = [
            "Hari",
            "Sita",
            "Ram",
            "Maya",
            "Krishna",
            "Gita",
            "Arjun",
            "Shanti",
            "Prakash",
            "Kamala",
            "Rajesh",
            "Sunita",
            "Dipesh",
            "Radha",
            "Mahesh",
            "Laxmi",
            "Suresh",
            "Prabha",
            "Naresh",
            "Mina",
            "Raman",
            "Bimala",
        ]

        for i in range(count):
            category = random.choice(list(case_templates.keys()))
            template = random.choice(case_templates[category])

            beneficiary_name = random.choice(nepali_names)
            beneficiary_age = random.choice(template["beneficiary_ages"])
            location = random.choice(nepal_locations)
            target_amount = random.choice(template["amounts"])

            title = template["title"].format(name=beneficiary_name)

            # Skip if case with same title already exists
            if CharityCase.objects.filter(title=title).exists():
                existing_case = CharityCase.objects.get(title=title)
                cases.append(existing_case)
                continue

            description = template["description"].format(
                name=beneficiary_name,
                age=beneficiary_age,
                location=location,
                cancer_type=(
                    random.choice(template.get("cancer_types", [""]))
                    if "cancer_types" in template
                    else ""
                ),
            )

            # Random completion percentage (0-90% for variety)
            completion_pct = random.uniform(0, 0.9)
            collected_amount = Decimal(str(target_amount * completion_pct))

            # Random deadline (1-6 months from now)
            deadline = timezone.now() + timedelta(days=random.randint(30, 180))

            case = CharityCase.objects.create(
                title=title,
                description=description,
                category=category,
                target_amount=Decimal(str(target_amount)),
                collected_amount=collected_amount,
                verification_status=random.choice(
                    ["approved", "approved", "approved", "pending", "rejected"]
                ),  # Mostly approved
                urgency_flag=random.choice(["low", "medium", "high", "critical"]),
                location=location,
                beneficiary_name=beneficiary_name,
                beneficiary_age=beneficiary_age,
                contact_phone=f"+977-98{random.randint(10000000, 99999999)}",
                contact_email=f"contact{i}@example.com",
                created_by=random.choice(users),
                deadline=deadline,
                tags=(
                    f"{category}, Nepal, help, medical"
                    if category == "medical"
                    else f"{category}, Nepal, help"
                ),
            )

            cases.append(case)
            created_count += 1

        return cases, created_count

    def create_case_updates(self, cases, users):
        """Create case updates for some cases"""
        updates = []
        created_count = 0

        update_templates = [
            "Thank you for your generous support! We have reached {percentage}% of our goal.",
            "Latest medical report shows positive progress. Treatment is ongoing.",
            "Surgery was successful! {name} is recovering well in the hospital.",
            "We are grateful for all the donations received so far. Every contribution helps.",
            "Update on {name}'s condition: The doctors are optimistic about recovery.",
            "Medical bills for this week have been covered thanks to your donations.",
            "Family update: {name} is showing signs of improvement and staying positive.",
        ]

        # Add updates to 70% of approved cases
        for case in random.sample(cases, int(len(cases) * 0.7)):
            if case.verification_status == "approved":
                num_updates = random.randint(1, 4)

                for j in range(num_updates):
                    template = random.choice(update_templates)
                    description = template.format(
                        name=case.beneficiary_name,
                        percentage=int(case.completion_percentage),
                    )

                    update_title = f"Update #{j+1}: Progress Report"

                    # Skip if update with same title for this case already exists
                    if CaseUpdate.objects.filter(
                        case=case, title=update_title
                    ).exists():
                        existing_update = CaseUpdate.objects.get(
                            case=case, title=update_title
                        )
                        updates.append(existing_update)
                        continue

                    # Create update with random date within case lifetime
                    days_ago = random.randint(1, 30)
                    created_at = timezone.now() - timedelta(days=days_ago)

                    update = CaseUpdate.objects.create(
                        case=case,
                        title=update_title,
                        description=description,
                        created_by=case.created_by,
                    )
                    # Manually set created_at
                    update.created_at = created_at
                    update.save()

                    updates.append(update)
                    created_count += 1

        return updates, created_count

    def create_donations(self, users, cases, count):
        """Create sample donations"""
        donations = []
        created_count = 0

        # Only create donations for approved cases
        approved_cases = [
            case for case in cases if case.verification_status == "approved"
        ]

        if not approved_cases:
            self.stdout.write(
                self.style.WARNING("No approved cases found. Cannot create donations.")
            )
            return donations, created_count

        donation_messages = [
            "Wishing you a speedy recovery!",
            "Stay strong! We are with you.",
            "Hope this helps. Get well soon!",
            "Sending prayers and support.",
            "May God bless you and your family.",
            "Together we can make a difference.",
            "Hope for your quick recovery.",
            "Stay positive and keep fighting!",
            "Best wishes for your treatment.",
            "You are not alone in this fight.",
        ]

        payment_methods = ["esewa", "khalti", "bank_transfer"]

        for i in range(count):
            case = random.choice(approved_cases)
            donor = random.choice(users)

            # Random donation amount (10-5000)
            amount = Decimal(str(random.randint(10, 5000)))

            # Make some donations anonymous (20%)
            is_anonymous = random.random() < 0.2

            # Generate unique payment reference
            payment_ref = f"PAY{random.randint(100000, 999999)}"

            # Skip if donation with same payment reference already exists
            while Donation.objects.filter(payment_reference=payment_ref).exists():
                payment_ref = f"PAY{random.randint(100000, 999999)}"

            donation = Donation.objects.create(
                donor=donor,
                case=case,
                amount=amount,
                payment_method=random.choice(payment_methods),
                payment_reference=payment_ref,
                transaction_id=f"TXN{random.randint(100000000, 999999999)}",
                status=random.choice(
                    ["completed", "completed", "completed", "pending"]
                ),  # Mostly completed
                is_anonymous=is_anonymous,
                donor_message=(
                    random.choice(donation_messages) if random.random() < 0.6 else None
                ),
                ip_address=f"192.168.1.{random.randint(1, 255)}",
            )

            # Set random creation date (within last 60 days)
            days_ago = random.randint(1, 60)
            donation.created_at = timezone.now() - timedelta(days=days_ago)
            if donation.status == "completed":
                donation.completed_at = donation.created_at + timedelta(
                    minutes=random.randint(1, 60)
                )
            donation.save()

            donations.append(donation)
            created_count += 1

        # Update collected amounts for cases based on completed donations
        for case in approved_cases:
            completed_donations = case.donations.filter(status="completed")
            total_collected = sum(d.amount for d in completed_donations)
            case.collected_amount = total_collected
            case.save()

        return donations, created_count
