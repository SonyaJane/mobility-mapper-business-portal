# Run the script: python scripts/generate_fake_users.py
# python manage.py flush --no-input
# heroku run python manage.py flush

# python manage.py loaddata .\fixtures\accessibility_features.json
# heroku run python manage.py loaddata ./fixtures/accessibility_features.json

# python manage.py loaddata .\fixtures\business_categories.json
# heroku run python manage.py loaddata ./fixtures/business_categories.json

# python manage.py loaddata .\fixtures\pricing_tiers.json
# heroku run python manage.py loaddata ./fixtures/pricing_tiers.json

# Load the generated fixture: 
# python manage.py loaddata fixtures\fake_users_fixture.json
# heroku run python manage.py loaddata fixtures/fake_users_fixture.json

# python manage.py createsuperuser
# heroku run python manage.py createsuperuser

# This script generates fake user profiles and businesses for testing purposes.

import os
import re
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
# Track usernames to enforce uniqueness
used_usernames = set()


import os
# Prepare profile photos list
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
profile_photo_dir = os.path.join(base_dir, 'media', 'profile_photos')
# Load all photo files
all_photo_files = sorted([f for f in os.listdir(profile_photo_dir)
                         if os.path.isfile(os.path.join(profile_photo_dir, f))])
# First 10 for wheeler users
photo_files = all_photo_files[:10]
# Next 36 for business users
business_photo_files = all_photo_files[10:46]
# 20 fake wheeler users (first 10 use profile photo filenames as names, next 10 random without photo)
for i in range(20):
    if i < len(photo_files):
        fname = photo_files[i]
        # derive name from filename
        stem = os.path.splitext(fname)[0]
        parts = stem.replace('-', ' ').replace('_', ' ').split()
        first_name = parts[0].title()
        last_name = ' '.join(p.title() for p in parts[1:]) if len(parts) > 1 else ''
        photo_path = f"profile_photos/{fname}"
    else:
        first_name, last_name = fake.first_name(), fake.last_name()
        photo_path = ''
    # derive username and ensure uniqueness
    orig_username = f"{first_name.lower()}_{last_name.lower()}".rstrip('_')
    username = orig_username
    suffix = 1
    while username in used_usernames:
        username = f"{orig_username}_{suffix}"
        suffix += 1
    used_usernames.add(username)
    # derive email from unique username
    email = f"{username}@example.com"
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
    # derive name from photo filename for first 36 business users, else random
    if i < len(business_photo_files):
        # use filename (without extension) for naming
        biz_fname = business_photo_files[i]
        stem = os.path.splitext(biz_fname)[0]
        parts = stem.replace('-', ' ').replace('_', ' ').split()
        first_name = parts[0].title()
        last_name = ' '.join(p.title() for p in parts[1:]) if len(parts) > 1 else ''
    else:
        first_name = fake.first_name()
        last_name = fake.last_name()
    # derive username and ensure uniqueness
    orig_username = f"{first_name.lower()}_{last_name.lower()}".rstrip('_')
    username = orig_username
    suffix = 1
    while username in used_usernames:
        username = f"{orig_username}_{suffix}"
        suffix += 1
    used_usernames.add(username)
    # derive email from unique username
    email = f"{username}@example.com"
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
            "first_name": first_name,
            "last_name": last_name,
        }
    }
    users.append(user)
    # Assign business profile photo for first 36 business users
    if i < len(business_photo_files):
        biz_fname = business_photo_files[i]
        photo_path = f"profile_photos/{biz_fname}"
    else:
        photo_path = ''
    profile = {
        "model": "accounts.userprofile",
        "pk": user_pk,
        "fields": {
            "user": user_pk,
            "photo": photo_path,
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
# Add users and profiles to fixture
fixture.extend(users)
fixture.extend(profiles)
# Build lookup for owner user info to generate business emails
user_map = {u['pk']: u['fields'] for u in users if u.get('model') == 'auth.user'}

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
        # UK format phone number: (01xxx) xxxxxx
        area = ''.join(str(random.randint(0, 9)) for _ in range(3))
        number = ''.join(str(random.randint(0, 9)) for _ in range(6))
        public_phone = f"(01{area}) {number}"
    else:
        public_phone = ''
    # always generate a contact phone in same format
    area_c = ''.join(str(random.randint(0, 9)) for _ in range(3))
    number_c = ''.join(str(random.randint(0, 9)) for _ in range(6))
    contact_phone = f"(01{area_c}) {number_c}"
    if random.random() < 0.5:
        # custom public email: local part from 'hello' or owner name, domain from business name
        owner = user_map.get(owner_pk, {})
        first = owner.get('first_name', '').lower() or 'hello'
        last = owner.get('last_name', '').lower() or ''
        locals_choices = ['hello', first]
        if first and last:
            locals_choices.append(f"{first}.{last}")
        local = random.choice(locals_choices)
        # sanitize business name for domain
        domain_key = re.sub(r'[^A-Za-z0-9]', '', business_name).lower() or 'business'
        public_email = f"{local}@{domain_key}.com"
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
    # Determine if Wheeler verification was done
    # we will generate verification instances below
    
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
            "address": fake.address().replace("\n", ", "),
            "accessibility_features": random.sample(accessibility_choices, k=random.randint(1, 5)),
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
            "is_approved": True,
            "created_at": str(fake.date_time_this_decade(tzinfo=timezone.utc)),
        }
    })
fixture.extend(businesses)

# Create WheelerVerification instances for verified businesses (3 per business)
wheeler_verifications = []
# Start a global PK counter for verifications
ver_pk = 1
for biz in businesses:
    if biz['fields'].get('verified_by_wheelers'):
        biz_pk = biz['pk']
        # prepare confirmed features list
        base_confirmed = biz['fields'].get('accessibility_features', []).copy()
        # select up to 3 unique wheeler users for this business
        wheeler_pks = random.sample(user_profiles_without_business, k=min(3, len(user_profiles_without_business)))
        for wheeler_pk in wheeler_pks:
            # generate verification details
            date_verified = str(fake.date_time_this_year(tzinfo=timezone.utc))
            comments = fake.sentence()
            mobility = random.choice(MOBILITY_DEVICES)
            # determine additional feature optionally
            confirmed = base_confirmed.copy()
            additional = []
            if random.random() < 0.5:
                possible_extras = [f for f in accessibility_choices if f not in confirmed]
                if possible_extras:
                    additional = [random.choice(possible_extras)]
            wheeler_verifications.append({
                'model': 'businesses.wheelerverification',
                'pk': ver_pk,
                'fields': {
                    'business': biz_pk,
                    'wheeler': wheeler_pk,
                    'date_verified': date_verified,
                    'comments': comments,
                    'mobility_device': mobility,
                    'approved': True,
                    'confirmed_features': confirmed,
                    'additional_features': additional,
                }
            })
            ver_pk += 1
# add them to fixture
fixture.extend(wheeler_verifications)

# Create WheelerVerificationPhoto fixtures from media/verification_photos
# Map accessibility feature codes to their PKs and invert mapping
features = list(AccessibilityFeature.objects.all())
feature_map_code_to_pk = {feat.code: feat.pk for feat in features}
feature_map_pk_to_code = {feat.pk: feat.code for feat in features}
# Map each business to its accessibility feature PK list
business_feature_map = {biz['pk']: biz['fields'].get('accessibility_features', []) for biz in businesses}
# List available photo files
verification_photo_dir = os.path.join(base_dir, 'media', 'verification_photos')
available_photos = {f for f in os.listdir(verification_photo_dir) if os.path.isfile(os.path.join(verification_photo_dir, f))}
photo_fixtures = []
photo_pk = 1
for ver in wheeler_verifications:
    biz_pk = ver['fields']['business']
    # get confirmed (business-listed) and any additional features
    biz_features = business_feature_map.get(biz_pk, [])
    additional_features = ver['fields'].get('additional_features', [])
    feature_pks = set(biz_features) | set(additional_features)
    if not feature_pks:
        continue
    # include all confirmed and additional feature photos
    for feat_pk in feature_pks:
        code = feature_map_pk_to_code.get(feat_pk)
        if not code:
            continue
        # try common image extensions
        for ext in ['.jpg', '.png', '.jpeg']:
            fname = f"{code}{ext}"
            if fname in available_photos:
                photo_fixtures.append({
                    'model': 'businesses.wheelerverificationphoto',
                    'pk': photo_pk,
                    'fields': {
                        'verification': ver['pk'],
                        'image': f"verification_photos/{fname}",
                        'feature': feat_pk,
                        'uploaded_at': str(fake.date_time_this_year(tzinfo=timezone.utc))
                    }
                })
                photo_pk += 1
                break
# extend the fixture list
fixture.extend(photo_fixtures)

fixtures_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fixtures")
fixture_path = os.path.join(fixtures_dir, "fake_users_fixture.json")
with open(fixture_path, "w") as f:
    json.dump(fixture, f, indent=2)

print(f"Fixture file '{fixture_path}' created.")
