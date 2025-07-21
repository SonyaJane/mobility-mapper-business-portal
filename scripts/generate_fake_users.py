# Run the script: python scripts/generate_fake_users.py
# Load the generated fixture: python manage.py loaddata fixtures/fake_users_fixture.json

import os
import django
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import json
import random
from faker import Faker
from datetime import timezone
from django.contrib.auth.hashers import make_password
from shapely.geometry import shape, Point
import geojson

from accounts.models import UserProfile
from businesses.models import Business, TIER_CHOICES

fake = Faker("en_GB")

# Extract values from model choices
AGE_GROUPS = [choice[0] for choice in UserProfile.AGE_GROUP_CHOICES]
MOBILITY_DEVICES = [choice[0] for choice in UserProfile.MOBILITY_DEVICE_CHOICES]
UK_COUNTIES = [choice[0] for choice in UserProfile.UK_COUNTY_CHOICES]

# Generate user profiles
user_profiles_with_business = []
user_profiles_without_business = []
users = []
profiles = []
fixture = []


# 10 fake wheeler users (is_wheeler=True, has_business=False, mobility_device set)
for i in range(10):
    username = f"wheeler_user_{i+1}"
    email = fake.email()
    password = make_password("testpass123")
    user_pk = i + 1
    user = {
        "model": "auth.user",
        "pk": user_pk,
        "fields": {
            "username": username,
            "email": email,
            "password": password,
            "is_active": True,
            "is_staff": False,
            "is_superuser": False,
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
        }
    }
    users.append(user)
    profile = {
        "model": "accounts.userprofile",
        "pk": user_pk,
        "fields": {
            "user": user_pk,
            "is_wheeler": True,
            "has_business": False,
            "country": "GB",
            "county": random.choice(UK_COUNTIES),
            "mobility_device": random.choice(MOBILITY_DEVICES),
            "age_group": random.choice(AGE_GROUPS),
            "created_at": str(fake.date_time_this_decade(tzinfo=timezone.utc)),
            "updated_at": str(fake.date_time_this_year(tzinfo=timezone.utc)),
        }
    }
    profiles.append(profile)
    user_profiles_without_business.append(user_pk)

# 10 fake business users (is_wheeler=False, has_business=True, mobility_device=None)
for i in range(10):
    username = f"business_user_{i+1}"
    email = fake.email()
    password = make_password("testpass123")
    user_pk = i + 11
    user = {
        "model": "auth.user",
        "pk": user_pk,
        "fields": {
            "username": username,
            "email": email,
            "password": password,
            "is_active": True,
            "is_staff": False,
            "is_superuser": False,
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
        }
    }
    users.append(user)
    profile = {
        "model": "accounts.userprofile",
        "pk": user_pk,
        "fields": {
            "user": user_pk,
            "is_wheeler": False,
            "has_business": True,
            "country": "UK",
            "county": random.choice(UK_COUNTIES),
            "mobility_device": None,
            "age_group": random.choice(AGE_GROUPS),
            "created_at": str(fake.date_time_this_decade(tzinfo=timezone.utc)),
            "updated_at": str(fake.date_time_this_year(tzinfo=timezone.utc)),
        }
    }
    profiles.append(profile)
    user_profiles_with_business.append(user_pk)


# Add users and profiles to fixture
fixture.extend(users)
fixture.extend(profiles)

# Add EmailAddress records for all users with emails
for user in users:
    email = user["fields"].get("email")
    if email:
        fixture.append({
            "model": "account.emailaddress",
            "pk": user["pk"],
            "fields": {
                "user": user["pk"],
                "email": email,
                "verified": True,
                "primary": True
            }
        })


# Load UK boundary GeoJSON
with open("static/geojson/uk-boundary.geojson", "r") as f:
    uk_geojson = geojson.load(f)
uk_polygon = shape(uk_geojson["features"][0]["geometry"])

# Generate businesses, each owned by a user profile with business
businesses = []
from businesses.models import Category, AccessibilityFeature
category_choices = list(Category.objects.values_list('pk', flat=True))
accessibility_choices = list(AccessibilityFeature.objects.values_list('pk', flat=True))
tier_choices = [c[0] for c in TIER_CHOICES]


# Get all pricing tier PKs (assume at least one exists)
from businesses.models import PricingTier
pricing_tiers = list(PricingTier.objects.filter(is_active=True))

for idx, owner_pk in enumerate(user_profiles_with_business):
    # Generate a random UK point within the boundary
    while True:
        lon = round(random.uniform(-7.6, 1.8), 6)
        lat = round(random.uniform(49.9, 58.7), 6)
        point = Point(lon, lat)
        if uk_polygon.contains(point):
            break
    point_wkt = f"POINT ({lon} {lat})"
    # Pick a pricing tier
    pricing_tier_obj = random.choice(pricing_tiers) if pricing_tiers else None
    pricing_tier_pk = pricing_tier_obj.pk if pricing_tier_obj else None
    # Billing frequency
    billing_frequency = random.choice(["monthly", "yearly"])
    # Logo (simulate file path)
    logo_path = None  # Or use a static test image if desired
    # Social media URLs
    website = fake.url()
    facebook_url = f"https://facebook.com/{fake.slug()}"
    instagram_url = f"https://instagram.com/{fake.slug()}"
    twitter_url = f"https://twitter.com/{fake.slug()}"
    # Phones/emails
    public_phone = fake.phone_number()
    contact_phone = fake.phone_number()
    public_email = fake.company_email()
    # Services/offers
    services_offered = fake.sentence(nb_words=6)
    special_offers = fake.sentence(nb_words=8)
    # Opening hours
    opening_hours = "Mon-Fri 09:00-17:00"  # Simple static example
    # Choose 1 category most of the time, 2 occasionally
    if random.random() < 0.8:
        categories = [random.choice(category_choices)]
    else:
        categories = random.sample(category_choices, k=2)
    businesses.append({
        "model": "businesses.business",
        "pk": idx+1,
        "fields": {
            "business_owner": owner_pk,
            "business_name": fake.company(),
            "description": fake.sentence(),
            "categories": categories,
            "location": point_wkt,
            "address": fake.address(),
            "accessibility_features": random.sample(accessibility_choices, k=random.randint(0, len(accessibility_choices))),
            "logo": logo_path,
            "website": website,
            "opening_hours": opening_hours,
            "public_phone": public_phone,
            "contact_phone": contact_phone,
            "public_email": public_email,
            "services_offered": services_offered,
            "special_offers": special_offers,
            "facebook_url": facebook_url,
            "instagram_url": instagram_url,
            "twitter_url": twitter_url,
            "pricing_tier": pricing_tier_pk,
            "billing_frequency": billing_frequency,
            "wheeler_verification_requested": fake.boolean(),
            "verified_by_wheelers": fake.boolean(),
            "wheeler_verification_notes": fake.sentence(),
            "is_approved": True,
            "created_at": str(fake.date_time_this_decade(tzinfo=timezone.utc)),
        }
    })
fixture.extend(businesses)

fixtures_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fixtures")
fixture_path = os.path.join(fixtures_dir, "fake_users_fixture.json")
with open(fixture_path, "w") as f:
    json.dump(fixture, f, indent=2)

print(f"Fixture file '{fixture_path}' created.")
