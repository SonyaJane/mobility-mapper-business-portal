
# Demo Data & Fake User/Business Generation

To support development, testing, and demonstration of the Mobility Mapper Business Portal, the project includes a robust system for generating realistic fake users, businesses, and associated verification data. This is achieved through a custom Python script and a set of fixture files.

## Existing Fixtures

The script relies on several fixture files containing fixed data required for six core models. These fixtures are located in the `fixtures/` directory of their corresponding app, and include:

- `accessibility_features.json` — Business app: List of all possible accessibility features.
- `business_categories.json` — Business app: Grouped business categories for classification.
- `membership_tiers.json` — Business app: Definitions, pricing, and benefits of each membership tier.
- `counties.json` — Accounts app: List of UK counties for user and business addresses.
- `age_groups.json` — Accounts app: Age group options for user profiles.
- `mobility_devices.json` — Accounts app: List of supported mobility devices for wheelers.

These fixtures must be loaded into the database before running the fake data generation script, because they are used to populate the fake data.

They can be loaded using the following command:

```bash
python manage.py loaddata accounts\fixtures\counties.json \
businesses\fixtures\accessibility_features.json \
businesses\fixtures\business_categories.json \
businesses\fixtures\membership_tiers.json \
accounts\fixtures\age_groups.json \
accounts\fixtures\mobility_devices.json
```

## Script

- The script `scripts/generate_fake_users.py` creates a large set of fake users for testing and demonstration purposes.
- Creates fake users (wheelers and business owners) with unique profiles and optional profile photos.
- Generates businesses, each linked to a business owner, with realistic addresses, categories, accessibility features, and membership tiers.
- Produces WheelerVerification reports, applications, and associated photos for verified businesses.
- Simulates purchases for memberships and wheeler verifications, with correct pricing logic for each tier.
- Ensures all relationships (users, profiles, businesses, verifications, purchases) are consistent and realistic.

**Output:**
- Writes Django fixture files for each model to their respective `fixtures/` folders, ready for `loaddata`.
- Handles all required dependencies and lookups for foreign keys and many-to-many relationships.
- Includes logic for unique usernames, emails, and realistic timestamps.

**Usage:**
- Run using `python scripts/generate_fake_users.py`

### Loading Demo Data

The generated fixtures can be loaded using the following command:

```bash
python manage.py loaddata fixtures/user.json accounts/fixtures/userprofile.json fixtures/emailaddress.json businesses/fixtures/business.json verification/fixtures/wheelerverification.json verification/fixtures/wheelerverificationapplication.json verification/fixtures/wheelerverificationphoto.json checkout/fixtures/purchase.json accounts/fixtures/counties.json businesses/fixtures/accessibility_features.json businesses/fixtures/business_categories.json businesses/fixtures/membership_tiers.json accounts/fixtures/age_groups.json accounts/fixtures/mobility_devices.json
```
