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

"""Generate fake users, businesses, verifications and associated image references.

Key points:
 - Image field values now use <subdir>/filename (no legacy 'media/' prefix).
 - Optional direct upload to Cloudinary with --upload-cloud (idempotent overwrite).
 - Public IDs = filename stem, enabling stable re-generation.
"""

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
from django.conf import settings  # (may remain for future use; safe if unused)

fake = Faker("en_GB")

# Extract UserProfile field options
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

# Track used name combinations to ensure uniqueness
used_name_combos = set()

# (Removed --upload-cloud flag and Cloudinary upload support)

# Resolve base media directories
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
profile_photo_dir = os.path.join(base_dir, 'media', 'profile_photos')

# Load all profile photo files
all_photo_files = sorted([f for f in os.listdir(profile_photo_dir)
                         if os.path.isfile(os.path.join(profile_photo_dir, f))])

# Reserve first 10 profile photos for wheeler users
photo_files = all_photo_files[:10]
print(all_photo_files)
# Reserve next 36 profile photos for business users
business_photo_files = all_photo_files[10:46]
print(business_photo_files)
# Create 20 fake wheeler user instances:
# first 10 use profile photo filenames as names, 
# next 10 have random names and no profile photo
for i in range(20):
    print(i)
    if i < len(photo_files):
        # get next file name in photo_files
        fname = photo_files[i]
        # derive name from filename
        stem = os.path.splitext(fname)[0]
        parts = stem.replace('-', ' ').replace('_', ' ').split()
        first_name = parts[0].title()
        last_name = ' '.join(p.title() for p in parts[1:]) if len(parts) > 1 else ''
        photo_path = f"profile_photos/{fname}"
        username = f"{first_name.lower()}_{last_name.lower()}".rstrip('_')
        # add name combo to used set
        name_combo = (first_name, last_name)
        used_name_combos.add(name_combo)
    else:
        photo_path = ''
        first_name = fake.first_name()
        last_name = fake.last_name()                
        # Ensure name combo is unique
        name_combo = (first_name, last_name)
        while name_combo in used_name_combos:
            first_name = fake.first_name()
            last_name = fake.last_name()
            name_combo = (first_name, last_name)
        used_name_combos.add(name_combo)
        username = f"{first_name.lower()}_{last_name.lower()}".rstrip('_')
    
    # derive email from username
    email = f"{username}@example.com"
    
    # random password
    password = make_password("testpass123")

    # Assign user PK
    user_pk = i + 1

    # Create user dictionary
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
    # Append user to users list
    users.append(user)
    
    ### user profile instances ###
    # Assign 1 or 2 mobility devices to wheeler users
    devices = random.sample(MOBILITY_DEVICES, k=random.randint(1, 2))
    # Other mobility device (not in devices list)
    other_device = fake.sentence(nb_words=3) if 'other' in devices else ''
    # Generate timestamps so updated_at is after created_at and both before now
    created_at = fake.date_time_this_year(tzinfo=timezone.utc)
    updated_at = fake.date_time_between(start_date=created_at, end_date="now", tzinfo=timezone.utc)
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
            "mobility_devices_other": other_device,
            "age_group": random.choice(AGE_GROUPS),
            "created_at": str(created_at),
            "updated_at": str(updated_at),
            "photo": photo_path,
        }
    }
    profiles.append(profile)
    user_profiles_without_business.append(user_pk)

# Generate 100 fake business users 
# (is_wheeler=False, has_business=True, mobility_device=None)
for i in range(100):
    # derive names and ensure uniqueness
    if i < len(business_photo_files):
        # fixed from business_photo_files
        biz_fname = business_photo_files[i]
        stem = os.path.splitext(biz_fname)[0]
        parts = stem.replace('-', ' ').replace('_', ' ').split()
        first_name = parts[0].title()
        last_name = ' '.join(p.title() for p in parts[1:]) if len(parts) > 1 else ''
        username = f"{first_name.lower()}_{last_name.lower()}".rstrip('_')
        # record combos
        used_name_combos.add((first_name, last_name))
        used_usernames.add(username)
    else:
        # random names - loop until both name and username are unique
        while True:
            first_name = fake.first_name()
            last_name = fake.last_name()
            name_combo = (first_name, last_name)
            username = f"{first_name.lower()}_{last_name.lower()}".rstrip('_')
            if name_combo in used_name_combos or username in used_usernames:
                continue
            used_name_combos.add(name_combo)
            used_usernames.add(username)
            break
    
    # derive email from username
    email = f"{username}@example.com"
    password = make_password("testpass123")
    user_pk = i + 21 # we already have 20 users
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
    # Assign a business profile photo for first 36 business users
    if i < len(business_photo_files):
        biz_fname = business_photo_files[i]
        photo_path = f"mobility_mapper_business_portal/profile_photos/{biz_fname}"
    else:
        photo_path = ''
    
    # Generate timestamps so updated_at is after created_at and both before now
    user_created_at = fake.date_time_this_year(tzinfo=timezone.utc)
    user_updated_at = fake.date_time_between(start_date=user_created_at, end_date="now", tzinfo=timezone.utc)

    profile = {
        "model": "accounts.userprofile",
        "pk": user_pk,
        "fields": {
            "user": user_pk,
            "photo": photo_path,
            "is_wheeler": False,
            "has_business": True,
            "has_registered_business": True,
            "mobility_devices": [],
            "mobility_devices_other": '',
            "country": "UK",
            "county": random.choice(UK_COUNTIES),
            "age_group": random.choice(AGE_GROUPS),
            "created_at": str(user_created_at),
            "updated_at": str(user_updated_at),
        }
    }
    profiles.append(profile)
    user_profiles_with_business.append(user_pk)

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

# Get all business category IDs
category_choices = list(Category.objects.values_list('pk', flat=True))

# get all accessibility feature IDs
accessibility_choices = list(AccessibilityFeature.objects.values_list('pk', flat=True))

 # Get all pricing tier IDs
tier_choices = [c[0] for c in TIER_CHOICES]

# Get all pricing tier PKs (assume at least one exists)
pricing_tiers = list(PricingTier.objects.filter(is_active=True))

# Generate businesses for each user profile with a business
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
        logo_path = f"mobility_mapper_business_portal/business_logos/{logo_file}"
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

    # Assign accessibility features and verification status
    verified_by_wheelers = fake.boolean()
    wheeler_verification_requested = False if verified_by_wheelers else (random.random() < 0.5)
    features_for_this = random.sample(accessibility_choices, k=random.randint(1, min(3, len(accessibility_choices))))
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
            "accessibility_features": features_for_this,
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
            "created_at": str(fake.date_time_between(start_date=user_created_at, end_date="now", tzinfo=timezone.utc)),
        }
    })
fixture.extend(businesses)

# Create WheelerVerification report instances for verified businesses (3 per business)
wheeler_verifications = []
# Start a global PK counter for verifications
ver_pk = 1
for biz in businesses:
    # If the business is verified by wheelers
    if biz['fields'].get('verified_by_wheelers'):
        biz_pk = biz['pk']
        # prepare confirmed features list from business accessibility features
        # confirmed_features should always include all assigned business accessibility features
        confirmed_features = biz['fields'].get('accessibility_features', []).copy()
        # select 3 unique wheeler users for this business
        wheeler_pks = random.sample(user_profiles_without_business, k=3)
        for wheeler_pk in wheeler_pks:
            # generate verification report details
            # date after business creation
            date_verified = str(fake.date_time_between(start_date=created_at, end_date="now", tzinfo=timezone.utc))
            comments = fake.sentence()
            mobility = random.choice(MOBILITY_DEVICES)
            # additional observed accessibility features
            additional_features = []
            if random.random() < 0.5:
                possible_extras = [f for f in accessibility_choices if f not in confirmed_features]
                if possible_extras:
                    additional_features = [random.choice(possible_extras)]
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
                    'confirmed_features': confirmed_features,
                    'additional_features': additional_features,
                }
            })
            ver_pk += 1
# add them to fixture
fixture.extend(wheeler_verifications)

# Create WheelerVerificationPhoto fixtures from verification_photos
# Map accessibility feature codes to their PKs and invert mapping

# get all accessibility features
accessibility_features = list(AccessibilityFeature.objects.all())

# Map each feature to its code and PK
feature_map_code_to_pk = {feat.code: feat.pk for feat in accessibility_features}
feature_map_pk_to_code = {feat.pk: feat.code for feat in accessibility_features}

# Map each business to its accessibility feature PK list
business_feature_map = {
    biz['pk']: biz['fields'].get('accessibility_features', [])
    for biz in businesses
    if biz['fields'].get('verified_by_wheelers')
}

# List available certification photo files
verification_photo_dir = os.path.join(base_dir, 'media', 'verification_photos')
available_photos = {f for f in os.listdir(verification_photo_dir) if os.path.isfile(os.path.join(verification_photo_dir, f))}
photo_fixtures = []
photo_pk = 1
for ver in wheeler_verifications:
    biz_pk = ver['fields']['business']
    # get confirmed (business-listed features) and any additional features
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
        # track if we find a matching photo file
        found = False
        # try common image extensions
        for ext in ['.jpg', '.png', '.jpeg', '.webp']:
            fname = f"{code}{ext}"
            if fname in available_photos:
                photo_fixtures.append({
                    'model': 'businesses.wheelerverificationphoto',
                    'pk': photo_pk,
                    'fields': {
                        'verification': ver['pk'],
                        'image': f"mobility_mapper_business_portal/verification_photos/{fname}",
                        'feature': feat_pk,
                        'uploaded_at': str(fake.date_time_this_year(tzinfo=timezone.utc))
                    }
                })
                photo_pk += 1
                found = True
                break
        # notify if no file matched this feature code
        if not found:
            print(f"file not found for feature code {code}")

# extend the fixture list
fixture.extend(photo_fixtures)

# Cloud upload functionality removed; images should already exist in Cloudinary if needed.

fixtures_dir = os.path.join(base_dir, "fixtures")
os.makedirs(fixtures_dir, exist_ok=True)
fixture_path = os.path.join(fixtures_dir, "fake_users_fixture.json")
with open(fixture_path, "w") as f_out:
    json.dump(fixture, f_out, indent=2)

print(f"Fixture file '{fixture_path}' created.")
