# Run the script: python scripts/generate_fake_users.py
# python manage.py flush --no-input
# python manage.py loaddata .\fixtures\accessibility_features.json
# python manage.py loaddata ./fixtures/accessibility_features.json

# python manage.py loaddata .\fixtures\business_categories.json
# python manage.py loaddata ./fixtures/business_categories.json

# python manage.py loaddata .\fixtures\pricing_tiers.json
# python manage.py loaddata ./fixtures/pricing_tiers.json

# Load the generated fixture: 
# python manage.py loaddata fixtures/fake_users_fixture.json
# python manage.py createsuperuser

# This script generates fake user profiles and businesses for testing purposes.

import os
import django
import sys
import json
import random
import geojson

from faker import Faker
from datetime import timezone
from django.contrib.auth.hashers import make_password
from shapely.geometry import shape, Point

# Ensure project root is on PYTHONPATH and Django is set up before importing models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import UserProfile
from businesses.models import Business, TIER_CHOICES
from businesses.models import Category, AccessibilityFeature, PricingTier

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


# 2 fake wheeler users (is_wheeler=True, has_business=False, mobility_device set)
for i in range(2):
    # Setup Lilly Bishop with profile photo on first iteration
    if i == 0:
        first_name, last_name = "Lilly", "Bishop"
        # assign single profile photo
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        photo_files = os.listdir(os.path.join(base_dir, 'media', 'profile_photos'))
        photo_path = f"profile_photos/{photo_files[0]}" if photo_files else ''
    else:
        first_name, last_name = fake.first_name(), fake.last_name()
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
            "first_name": first_name,
            "last_name": last_name,
        }
    }
    users.append(user)
    # Assign mobility devices list for wheeler users
    # Assign mobility devices list for wheeler users
    devices = random.sample(MOBILITY_DEVICES, k=random.randint(1, 2))
    other_desc = fake.sentence(nb_words=3) if 'other' in devices else ''
    profile = {
        "model": "accounts.userprofile",
        "pk": user_pk,
        "fields": {
            "user": user_pk,
            "is_wheeler": True,
            "has_business": False,
            "has_registered_business": False,
            "country": "UK",
            "county": random.choice(UK_COUNTIES),
            "mobility_devices": devices,
            "mobility_devices_other": other_desc,
            "age_group": random.choice(AGE_GROUPS),
            "created_at": str(fake.date_time_this_decade(tzinfo=timezone.utc)),
            "updated_at": str(fake.date_time_this_year(tzinfo=timezone.utc)),
            "photo": photo_path,
        }
    }
    profiles.append(profile)
    user_profiles_without_business.append(user_pk)

# 100 fake business users (is_wheeler=False, has_business=True, mobility_device=None)
for i in range(100):
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
            "has_registered_business": False,
            "mobility_devices": [],
            "mobility_devices_other": '',
            "country": "UK",
            "county": random.choice(UK_COUNTIES),
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
# Prepare business logos list
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
logo_dir = os.path.join(base_dir, 'media', 'business_logos')
logo_files = sorted([f for f in os.listdir(logo_dir) if os.path.isfile(os.path.join(logo_dir, f))])
category_choices = list(Category.objects.values_list('pk', flat=True))
print(f"Found {len(category_choices)} business categories.")
accessibility_choices = list(AccessibilityFeature.objects.values_list('pk', flat=True))
tier_choices = [c[0] for c in TIER_CHOICES]

# Get all pricing tier PKs (assume at least one exists)
pricing_tiers = list(PricingTier.objects.filter(is_active=True))

for idx, owner_pk in enumerate(user_profiles_with_business):
    # Generate a random UK point within the boundary
    while True:
        lon = round(random.uniform(-7.6, 1.8), 6)
        lat = round(random.uniform(49.9, 58.7), 6)
        point = Point(lon, lat)
        if uk_polygon.contains(point):
            break
    # Use SRID prefix for proper PostGIS geometry import
    point_wkt = f"SRID=4326;POINT({lon} {lat})"
    # Pick a pricing tier
    pricing_tier_obj = random.choice(pricing_tiers) if pricing_tiers else None
    pricing_tier_pk = pricing_tier_obj.pk if pricing_tier_obj else None
    # Billing frequency
    billing_frequency = random.choice(["monthly", "yearly"])
    # Assign logo and derive business name
    if idx < len(logo_files):
        logo_file = logo_files[idx]
        logo_path = f"business_logos/{logo_file}"
        business_name = os.path.splitext(logo_file)[0].replace('_', ' ').title()
    else:
        logo_path = ''
        business_name = fake.company()
    # Website: 80% chance of having a website
    if random.random() < 0.8:
        website = fake.url()
    else:
        website = ''
    # Social media URLs
    if random.random() < 0.6:            
        facebook_url = f"https://facebook.com/{fake.slug()}"
    else:
        facebook_url = ''
    if random.random() < 0.5:
        instagram_url = f"https://instagram.com/{fake.slug()}"
    else:
        instagram_url = ''
    if random.random() < 0.5:
        x_twitter_url = f"https://x.com/{fake.slug()}"
    else:
        x_twitter_url = ''
    # Phones/emails
    if random.random() < 0.75:
        public_phone = fake.phone_number()
    else:
        public_phone = ''
    contact_phone = fake.phone_number()
    if random.random() < 0.5:
        public_email = fake.company_email()
    else:
        public_email = ''
    # Services/offers
    if random.random() < 0.5:
        services_offered = fake.sentence(nb_words=6)
    else:
        services_offered = ''
    # Special offers: 50% chance of having special offers
    if random.random() < 0.5:
        special_offers = fake.sentence(nb_words=8)
    else:
        special_offers = ''
    # Opening hours: 10% chance no hours submitted
    if random.random() < 0.1:
        opening_hours = ''
    else:
        # Build JSON opening hours for each day
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        opening_hours_dict = {}
        for day in days:
            # 90% chance business is open
            if random.random() < 0.9:
                # 30% of open days split into a morning and afternoon period
                if random.random() < 0.3:
                    opening_hours_dict[day] = [
                        {"start": "09:00", "end": "13:00"},
                        {"start": "14:00", "end": "17:00"}
                    ]
                else:
                    opening_hours_dict[day] = [{"start": "09:00", "end": "17:00"}]
            else:
                opening_hours_dict[day] = []
        opening_hours = json.dumps(opening_hours_dict)
    # Choose 1 category most of the time, 2 occasionally
    if random.random() < 0.8:
        categories = [random.choice(category_choices)]
    else:
        categories = random.sample(category_choices, k=2)

    verified_by_wheelers = fake.boolean()
    if verified_by_wheelers:
        # If verified, set a random note
        wheeler_verification_notes = fake.sentence()
    else:
        wheeler_verification_notes = ''
    
    if verified_by_wheelers:
        wheeler_verification_requested = False
    else:
        # 50% chance of requesting verification
        if random.random() < 0.5:
            wheeler_verification_requested = True
        else:
            wheeler_verification_requested = False

    businesses.append({
        "model": "businesses.business",
        "pk": idx+1,
        "fields": {
            "business_owner": owner_pk,
            "business_name": business_name,
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
            "x_twitter_url": x_twitter_url,
            "pricing_tier": pricing_tier_pk,
            "billing_frequency": billing_frequency,
            "wheeler_verification_requested": wheeler_verification_requested,
            "verified_by_wheelers": verified_by_wheelers,
            "wheeler_verification_notes": wheeler_verification_notes,
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
