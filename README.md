# mobility-mapper-business-portal

load data
python manage.py loaddata fixtures/pricing_tiers.json

Test the full admin workflow:

Approve a WheelerVerificationRequest in the admin.
Confirm the user receives an email with the correct link.
Click the link and ensure it goes to the correct verification form.


Test the dashboard and user experience:

Make sure the "Submit Verification" button appears for approved requests.
Ensure the verification form works and saves data/photos as expected.

Review and improve:

Add any missing validation or error handling.
Polish UI/UX for the dashboard and verification process.
Add tests for the new workflow