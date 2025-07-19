# Run with python manage.py seed_businesses
import random
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from faker import Faker

from businesses.models import Business, CATEGORY_CHOICES, TIER_CHOICES
from django.contrib.auth import get_user_model

User = get_user_model()
fake = Faker()

class Command(BaseCommand):
    help = 'Seed the database with fake businesses'

    def handle(self, *args, **kwargs):
        categories = [c[0] for c in CATEGORY_CHOICES]
        tiers = [t[0] for t in TIER_CHOICES]

        for i in range(10):
            # Create a fake user as owner
            email = fake.unique.email()
            user = User.objects.create_user(email=email, password="testpass123")

            business = Business.objects.create(
                owner=user,
                name=fake.company(),
                description=fake.text(),
                category=random.choice(categories),
                location=Point(
                    fake.longitude(min_value=-7.6, max_value=1.8),  # UK-ish bounds
                    fake.latitude(min_value=50.0, max_value=58.6)
                ),
                address=fake.address(),
                tier=random.choice(tiers),
                is_approved=True,
                accessibility_features=random.sample(
                    [
                        'step_free', 'wide_doors', 'accessible_toilet', 'hearing_loop',
                        'assistance_available', 'low_counter', 'disabled_parking'
                    ],
                    k=random.randint(1, 4)
                ),
            )

            self.stdout.write(self.style.SUCCESS(f"Created: {business.name}"))
