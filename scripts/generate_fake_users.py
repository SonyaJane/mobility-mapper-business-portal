
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
from businesses.models import Business, CATEGORY_CHOICES, TIER_CHOICES, ACCESSIBILITY_FEATURE_CHOICES

fake = Faker()

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

for i in range(20):
    username = fake.user_name() + str(i)
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

    has_business = i < 10
    is_wheeler = fake.boolean()
    profile = {
        "model": "accounts.userprofile",
        "pk": user_pk,
        "fields": {
            "user": user_pk,
            "is_wheeler": is_wheeler,
            "has_business": has_business,
            "country": "UK" if fake.boolean(chance_of_getting_true=80) else "Other",
            "county": random.choice(UK_COUNTIES),
            "mobility_device": random.choice(MOBILITY_DEVICES) if is_wheeler else None,
            "profile_picture": "",
            "bio": fake.sentence(),
            "age_group": random.choice(AGE_GROUPS),
            "created_at": str(fake.date_time_this_decade(tzinfo=timezone.utc)),
            "updated_at": str(fake.date_time_this_year(tzinfo=timezone.utc)),
        }
    }
    profiles.append(profile)
    if has_business:
        user_profiles_with_business.append(user_pk)
    else:
        user_profiles_without_business.append(user_pk)


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
category_choices = [c[0] for c in CATEGORY_CHOICES]
tier_choices = [c[0] for c in TIER_CHOICES]
accessibility_choices = [c[0] for c in ACCESSIBILITY_FEATURE_CHOICES]

for idx, owner_pk in enumerate(user_profiles_with_business):
    # Generate a random UK point within the boundary
    while True:
        lon = round(random.uniform(-7.6, 1.8), 6)
        lat = round(random.uniform(49.9, 58.7), 6)
        point = Point(lon, lat)
        if uk_polygon.contains(point):
            break
    point_wkt = f"POINT ({lon} {lat})"
    businesses.append({
        "model": "businesses.business",
        "pk": idx+1,
        "fields": {
            "owner": owner_pk,
            "name": fake.company(),
            "description": fake.sentence(),
            "category": random.choice(category_choices),
            "location": point_wkt,
            "address": fake.address(),
            "logo": "",
            "accessibility_features": random.sample(accessibility_choices, k=random.randint(0, len(accessibility_choices))),
            "tier": random.choice(tier_choices),
            "wheeler_verification_requested": fake.boolean(),
            "verified_by_wheelers": fake.boolean(),
            "wheeler_verification_notes": fake.sentence(),
            "is_approved": True,
            "created_at": str(fake.date_time_this_decade(tzinfo=timezone.utc)),
        }
    })
fixture.extend(businesses)

fixtures_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fixtures")
os.makedirs(fixtures_dir, exist_ok=True)
fixture_path = os.path.join(fixtures_dir, "fake_users_fixture.json")
with open(fixture_path, "w") as f:
    json.dump(fixture, f, indent=2)

print(f"Fixture file '{fixture_path}' created.")
