#!/usr/bin/env python
# python .\scripts\load_fixtures.py
import subprocess
import sys
import os
import json
import re

# Import env.py to set environment variables
# (ensure env.py is on the PYTHONPATH)
project_root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, project_root)
import env  # loads environment variables from env.py

# This script runs the Django management commands to flush and load fixtures in sequence.

def main():
    # Load superuser defaults JSON first
    script_dir = os.path.dirname(os.path.abspath(__file__))
    superuser_path = os.path.normpath(os.path.join(script_dir, '..', 'fixtures', 'superuser_instances.json'))

    # Environment variables override defaults; fallback to JSON
    username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
    # Provide a safe fallback password if none supplied via env
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

    if not username or not email:
        print("Unable to determine superuser username/email (missing in env). Aborting.")
        sys.exit(1)

    commands = [
        [sys.executable, 'manage.py', 'flush', '--no-input'],
        [sys.executable, 'manage.py', 'loaddata', 'fixtures/accessibility_features.json'],
        [sys.executable, 'manage.py', 'loaddata', 'fixtures/business_categories.json'],
        [sys.executable, 'manage.py', 'loaddata', 'fixtures/membership_tiers.json'],
        [sys.executable, 'scripts/generate_fake_users.py'],
        [sys.executable, 'manage.py', 'loaddata', 'fixtures/fake_users_fixture.json'],
        # Create/update superuser and populate related objects in one shell
        [sys.executable, 'manage.py', 'shell', '-c', (
            f"import json; d=json.load(open(r'{superuser_path}')); "
            f"UN='{username}'; EM='{email}'; PW='{password}'; "
            "from django.contrib.auth import get_user_model; User=get_user_model(); "
            "u,created = User.objects.get_or_create(username=UN, defaults={'email': EM}); "
            "u.email = EM; u.is_staff=True; u.is_superuser=True; u.set_password(PW); "
            "u.first_name=d.get('first_name', u.first_name); u.last_name=d.get('last_name', u.last_name); u.save(); "
            "from accounts.models import UserProfile; p,_=UserProfile.objects.get_or_create(user=u); pd=d['profile']; "
            "p.photo=pd.get('photo',''); p.country=pd['country']; p.county=pd['county']; p.is_wheeler=pd['is_wheeler']; "
            "p.has_business=pd['has_business']; p.has_registered_business=pd['has_registered_business']; p.mobility_devices=pd['mobility_devices']; "
            "p.mobility_devices_other=pd['mobility_devices_other']; p.age_group=pd['age_group']; p.save(); "
            "from businesses.models import Business, MembershipTier; bd=d['business']; import django.contrib.gis.geos as geos; "
            "loc=geos.GEOSGeometry(bd['location']); tier=MembershipTier.objects.filter(tier=bd.get('membership_tier')).first() if bd.get('membership_tier') else None; "
            "biz = Business.objects.filter(business_owner=p).first() or Business.objects.create(business_owner=p, business_name=bd['name'], description=bd['description'], location=loc, address=bd['address'], membership_tier=tier, logo=bd['logo'], website=bd['website'], opening_hours=bd['opening_hours'], public_phone=bd['public_phone'], contact_phone=bd['contact_phone'], public_email=bd['public_email'], services_offered=bd['services_offered'], special_offers=bd['special_offers'], facebook_url=bd['facebook_url'], instagram_url=bd['instagram_url'], x_twitter_url=bd['x_twitter_url'], wheeler_verification_requested=bd['wheeler_verification_requested'], verified_by_wheelers=bd['verified_by_wheelers'], is_approved=bd['is_approved']); "
            "biz.categories.set(bd.get('categories', [])); biz.accessibility_features.set(bd.get('accessibility_features', [])); p.has_business=True; p.save(); "
            "print('Superuser created/updated:', u.username)"
        )],
    ]
    for cmd in commands:
        print(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)

if __name__ == '__main__':
    main()