# Typical User Flow for a Business User

## 1. Registration
a) Go to the [landing page](https://mm-business-portal-deed0db15d35.herokuapp.com/).
b) Click the "Get Started" button, or in the menu click "Sign Up", to create an account.
<img src="./readme_files/user_flow/get_started.png" alt="Get Started Button" width="120"/>
c) Complete the registration form.
d) A confirmation email will be sent to the provided email address, click the link to verify the email.
e) After successful registration, you see a success message (toast) and are redirected to the Sign In page.

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
- If a paid membership tier is selected, you are redirected to the checkout page to complete the payment.  

## 4. Membership Selection & Payment
- If a paid membership tier is selected, the user is directed to the checkout page.
- The user enters payment details and completes the purchase.
- Upon successful payment, the business is upgraded to the selected tier.

## 5. Business Dashboard
- The user is redirected to their business dashboard.
- Here, they can:
  - View and edit business details
  - See membership status and renewal options
  - View Wheeler verifications and accessibility reports
  - Request Wheeler accessibility verification

### 5. Request Wheeler Verification
- The user can request a Wheeler to verify their business's accessibility features.
- If the request is approved, the business owner is notified when a Wheeler submits a verification.

### 6. Manage Business Information
- The user can update business details, change membership tier, or delete the business.
- The user can view verification reports submitted by Wheelers.

### 7. Membership Management
- The user can upgrade, downgrade, or cancel their membership at any time.
- Payment history and membership status are visible in the dashboard.

### 8. Logout
- The user logs out of the portal when finished.

---

**Note:**  
Throughout the flow, the user receives notifications and feedback via toast messages and emails for important actions (registration, verification requests, approvals, payments, etc.).


# Typical User Flow for a Wheeler


