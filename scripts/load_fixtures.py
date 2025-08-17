#!/usr/bin/env python
# python .\scripts\load_fixtures.py
import subprocess
import sys
import os
import json
from decouple import config

# This script runs the Django management commands to flush and load fixtures in sequence.

def main():
    # retrieve superuser credentials from .env via python-decouple
    username = config('DJANGO_SUPERUSER_USERNAME', default=None)
    email = config('DJANGO_SUPERUSER_EMAIL', default=None)
    password = config('DJANGO_SUPERUSER_PASSWORD', default=None)
    if not username or not email or not password:
        print("Error: Superuser credentials not found in .env")
        sys.exit(1)
    os.environ['DJANGO_SUPERUSER_USERNAME'] = username
    os.environ['DJANGO_SUPERUSER_EMAIL'] = email
    os.environ['DJANGO_SUPERUSER_PASSWORD'] = password
    # Load superuser defaults including profile fields
    script_dir = os.path.dirname(os.path.abspath(__file__))
    defaults_path = os.path.normpath(os.path.join(script_dir, '..', 'fixtures', 'superuser_defaults.json'))
    commands = [
        [sys.executable, 'manage.py', 'flush', '--no-input'],
        [sys.executable, 'manage.py', 'loaddata', 'fixtures/accessibility_features.json'],
        [sys.executable, 'manage.py', 'loaddata', 'fixtures/business_categories.json'],
        [sys.executable, 'manage.py', 'loaddata', 'fixtures/pricing_tiers.json'],
        [sys.executable, 'scripts/generate_fake_users.py'],
        [sys.executable, 'manage.py', 'loaddata', 'fixtures/fake_users_fixture.json'],
        [sys.executable, 'manage.py', 'createsuperuser', '--no-input'],
        # Populate profile fields from defaults JSON
        [sys.executable, 'manage.py', 'shell', '-c', (
            f"import json; d=json.load(open(r'{defaults_path}')); "
            # User updates
            "from django.contrib.auth import get_user_model; u=get_user_model().objects.get(username=d['username']); "
            "u.first_name=d['first_name']; u.last_name=d['last_name']; u.email=d.get('email', u.email); u.save(); "
            # Profile updates
            "from accounts.models import UserProfile; p, _=UserProfile.objects.get_or_create(user=u); pd=d['profile']; "
            "p.country=pd['country']; p.county=pd['county']; p.photo=pd['photo']; p.is_wheeler=pd['is_wheeler']; "
            "p.has_business=pd['has_business']; p.has_registered_business=pd['has_registered_business']; "
            "p.mobility_devices=pd['mobility_devices']; p.mobility_devices_other=pd['mobility_devices_other']; p.age_group=pd['age_group']; p.save(); "
            # Business creation
            "from businesses.models import Business, PricingTier; bd=d['business']; "
            "tier=PricingTier.objects.get(tier=bd['pricing_tier']) if bd.get('pricing_tier') else None; "
            "biz=Business.objects.create(business_owner=p, business_name=bd['name'], description=bd['description'], location=bd['location'], address=bd['address'], pricing_tier=tier, billing_frequency=bd['billing_frequency'], logo=bd['logo'], website=bd['website'], opening_hours=bd['opening_hours'], public_phone=bd['public_phone'], contact_phone=bd['contact_phone'], public_email=bd['public_email'], services_offered=bd['services_offered'], special_offers=bd['special_offers'], facebook_url=bd['facebook_url'], instagram_url=bd['instagram_url'], x_twitter_url=bd['x_twitter_url'], wheeler_verification_requested=bd['wheeler_verification_requested'], verified_by_wheelers=bd['verified_by_wheelers'], is_approved=bd['is_approved']); "
            "biz.categories.set(bd.get('categories', [])); biz.accessibility_features.set(bd.get('accessibility_features', [])); "
            "p.has_business=True; p.save();"
        )],
    ]
    for cmd in commands:
        print(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)

if __name__ == '__main__':
    main()