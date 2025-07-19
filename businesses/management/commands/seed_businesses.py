# Run with python generate_business_fixture.py
# python manage.py loaddata fake_businesses_fixture.json
import json
import random
from faker import Faker

# import category choices from businesses.models
from businesses.models import CATEGORY_CHOICES, TIER_CHOICES, ACCESSIBILITY_FEATURE_CHOICES
fake = Faker()

def generate_businesses(n=10, owner_id=1):
    businesses = []
    for i in range(n):
        lat, lng = fake.latitude(), fake.longitude()
        features = random.sample(ACCESSIBILITY_FEATURE_CHOICES, k=random.randint(1, 4))

        businesses.append({
            "model": "businesses.business",
            "pk": i + 1,
            "fields": {
                "owner": owner_id,
                "name": fake.company(),
                "description": fake.paragraph(),
                "category": random.choice(CATEGORY_CHOICES),
                "location": f"POINT({lng} {lat})",
                "address": fake.address(),
                "logo": "",
                "accessibility_features": features,
                "tier": random.choice(TIER_CHOICES),
                "wheeler_verification_requested": fake.boolean(chance_of_getting_true=30),
                "verified_by_wheelers": fake.boolean(chance_of_getting_true=20),
                "wheeler_verification_notes": fake.sentence(),
                "is_approved": True,
                "created_at": fake.date_time_this_year().isoformat()
            }
        })
    return businesses

if __name__ == "__main__":
    data = generate_businesses()
    with open("fake_businesses_fixture.json", "w") as f:
        json.dump(data, f, indent=2)
    print("✅ Fixture created: fake_businesses_fixture.json")
