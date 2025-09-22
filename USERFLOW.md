# Typical User Flow for a Business User

## 1. Registration
a) Go to the [landing page](https://mm-business-portal-deed0db15d35.herokuapp.com/).
b) Click the "Get Started" button, or in the menu click "Sign Up", to create an account.
<img src="./readme_files/user_flow/get_started.png" alt="Get Started Button" width="120"/>
c) Complete the registration form:
- Starred fields (*) are mandatory.
- Choose a username - you will use this to sign in. It must be unique and contain only letters, numbers, dots, or underscores.
- For the question "Do you own or manage a business?" select 'yes'.
- For the question "Do you use a wheeled mobility device?" select 'no'.
- 
f) A confirmation email will be sent to the provided email address, click the link to verify the email.
g) After successful registration, you see a success message (toast) and are redirected to the Sign In page.

## 2. Sign In

a) Sign in using your username or email, and password.
b) If you forget your password, you can use the "Forgot Password" feature to reset it via email.
c) Upon login, you are redirected to the business dashboard where you are invited to register your business. Click the "Register Business" button to proceed.

## 3. Register a Business
a) After signing in, you are invited to register your business. Click the "Register Business" button to proceed.
b) You are taken to the business registration form.
c) Fill out the business registration form. Fields with asterisks (*) are mandatory.
d) Click the Register button to submit the form.
e) If the form is invalid, error messages are displayed at the top of the form.
f) If the form is valid:    
- If the free membership tier is selected, the business is created, and you are redirected to the business dashboard with a success message.  
- If a paid membership tier is selected (standard or premium), you are redirected to the checkout page to complete the payment. The business is created but remains in the free tier until payment is completed.

## 4. Checkout & Membership Payment
a) If a paid membership tier is selected (standard or premium), you are directed to the checkout page.
b) The purchase summary confirms that you are purchasing the selected membership tier. You have the option to change the tier before proceeding with payment.
c) Enter your payment information and click the Complete Payment button to complete the purchase. A message is shown above the 'Complete Payment' button confirming how much you will be charged for the membership.
d) A spinner is shown on a semi-transparent overlay while the payment is processed, indicating that the payment is being processed, and preventing user interaction with the page.
e) If the payment fails, an error message is displayed, and you can retry the payment.
f) Upon successful payment, you are redirected to a Payment Success page confirming that your payment has been received. You are also sent a confirmation email. The business is upgraded to the selected tier.
g) You are redirected to the business dashboard with a success message confirming the membership purchase.
h) If payment is not completed, the business remains in the free tier, and you can upgrade later from the dashboard.

## 5. Business Dashboard
a) Looking at the dashboard, see that you can:
  - View and edit business details
  - See your membership tier and click a button to view the benefits
  - Click a button to view membership upgrade options if you are on the free or standard tier
  - Request Wheeler accessibility verification
  - View Wheeler accessibility verifications reports
  - Delete the business
b) Try editing the business details by clicking the "Edit Business" button at the bottom of the dashboard.
c) You are taken to the business edit form.

## 6. Edit Business Details
a) Update any business details as needed. The form is similar to the registration form but pre-filled with existing data.
b) The business logo is displayed in the form, and you can either remove or change it (or leave it as is).
c) Click the "Save Changes" button to submit the form. (You can also cancel to return to the dashboard without saving changes, or delete the business using the "Delete Business" button. A confirmation modal appears to confirm deletion.)
d) If the form is invalid, error messages are displayed at the top of the form.
e) If the form is valid, the business details are updated, and you are redirected back to the business dashboard with a success message.

## 7. Explore Plans & Upgrade Membership
a) Back on the Business Dashboard: if you are on the free or standard tier, click the "Explore Plans" button on the dashboard.
b) You can also access the Membership Options page from the dashboard by clicking "View Current Membership" and then "Upgrade Membership."
c) Review the available membership tiers (Standard and/or Premium) and their benefits.
d) Click the "Upgrade to <desired tier>" button for the desired tier.
e) You will be taken to the checkout page.

## 8. Request Wheeler Verification
a) From the Business Dashboard: request a Wheeler to verify your business's accessibility features by clicking the "Request Verification" button on the dashboard.
b) You are taken to the Wheeler Verification request page.
c) The page explains the verification process and any associated costs (if applicable). Note that the verification is free for Premium members, £30 for Standard members, and £60 Free members. 
d) Click the "Request Verification" button to submit the request.
e) For Free and Standard members, you are taken to the checkout page to complete the payment. Premium members skip this step and are taken directly to the dashboard with a success message.
f) On the checkout page, the purchase summary confirms that you are purchasing Wheeler verification of your business accessibility features. Your tier is also displayed together with the associated cost.
g) Ensure the payment details are correct
h) Enter your payment information and click the Complete Payment button to complete the purchase. A message is shown above the 'Complete Payment' button confirming how much you will be charged for the verification.
i) A spinner is shown on a semi-transparent overlay while the payment is processed, indicating that the payment is being processed, and preventing user interaction with the page.
j) Upon successful payment, you are redirected to a Payment Success page confirming that your payment has been received. You are also sent a confirmation email.


# Typical User Flow for a Wheeler

## 1. Registration and Sign In
Follow the same steps as for a Business user, but select the "Wheeler" account type during registration.

