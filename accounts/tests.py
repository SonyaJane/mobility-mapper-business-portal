"""
Test suite for the accounts app covering forms, models, views, signals,
context processors, template tags, and profile photo handling.
Run using python manage.py test accounts
"""

from io import BytesIO
from PIL import Image

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.gis.geos import Point
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template import Template, Context
from django.test import TestCase, RequestFactory
from django.urls import reverse

from .models import UserProfile, AgeGroup, County, MobilityDevice
from .forms import UserProfileForm, CustomSignupForm
from .context_processors import user_profile
from businesses.models import Business
from verification.models import WheelerVerificationApplication


User = get_user_model()


def get_test_image():
    """Return an in-memory valid JPEG image wrapped as SimpleUploadedFile for upload tests."""
    img = Image.new('RGB', (100, 100), color='red')
    buf = BytesIO()
    img.save(buf, format='JPEG')
    buf.seek(0)
    return SimpleUploadedFile("test.jpg", buf.read(), content_type="image/jpeg")


def add_session_to_request(request):
    """Attach a session to a RequestFactory request instance (helper for form save tests)."""
    middleware = SessionMiddleware()
    middleware.process_request(request)
    request.session.save()


class ValidateUsernameViewTests(TestCase):
    """Tests for the validate_username view (AJAX username availability check)."""

    def setUp(self):
        """Create an existing user and store the validation endpoint URL."""
        self.url = reverse('validate_username')
        self.user = User.objects.create_user(username='existinguser', email='existing@example.com', password='testpass123')

    def test_username_available(self):
        """Username not in use should return available=True JSON response."""
        response = self.client.get(self.url, {'username': 'newuser'})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'available': True})

    def test_username_taken(self):
        """Existing username should return available=False JSON response."""
        response = self.client.get(self.url, {'username': 'existinguser'})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'available': False})

    def test_username_blank(self):
        """Blank username should be treated as available (no collision)."""
        response = self.client.get(self.url, {'username': ''})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'available': True})


class CustomSignupFormTests(TestCase):
    """Tests for the CustomSignupForm validation and save behaviour."""

    def setUp(self):
        """Create base related objects for signup form tests."""
        self.age_group = AgeGroup.objects.create(name='36-45', label='36 to 45')
        self.county = County.objects.create(name='signupshire', label='Signupshire')
        self.mobility_device, _ = MobilityDevice.objects.get_or_create(name='scooter', defaults={'label': 'Scooter'})

    def test_signup_form_valid(self):
        """Form with complete correct data should be valid."""
        form = CustomSignupForm(data={
            'username': 'signupuser',
            'email': 'signup@example.com',
            'confirm_email': 'signup@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'first_name': 'Sign',
            'last_name': 'Up',
            'country': 'UK',
            'county': self.county.id,
            'age_group': self.age_group.id,
            'has_business': 'False',
            'is_wheeler': 'True',
            'mobility_devices': [self.mobility_device.id],
        })
        self.assertTrue(form.is_valid())

    def test_signup_form_password_mismatch(self):
        """Different password1/password2 should invalidate the form."""
        form = CustomSignupForm(data={
            'username': 'signupuser2',
            'email': 'signup2@example.com',
            'password1': 'StrongPass123!',
            'password2': 'WrongPass123!',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_signup_form_email_mismatch(self):
        """Mismatched email and confirm_email should raise error on confirm_email."""
        form = CustomSignupForm(data={
            'username': 'signupuser3',
            'email': 'signup3@example.com',
            'confirm_email': 'different@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'first_name': 'Sign',
            'last_name': 'Up',
            'country': 'UK',
            'county': self.county.id,
            'age_group': self.age_group.id,
            'has_business': 'False',
            'is_wheeler': 'True',
            'mobility_devices': [self.mobility_device.id],
        })
        self.assertFalse(form.is_valid())
        self.assertIn('confirm_email', form.errors)

    def test_signup_form_duplicate_username(self):
        """Duplicate username should produce a validation error on username field."""
        User.objects.create_user(username='dupeuser', email='dupe@example.com', password='testpass123')
        form = CustomSignupForm(data={
            'username': 'dupeuser',
            'email': 'new@example.com',
            'confirm_email': 'new@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'first_name': 'Dupe',
            'last_name': 'User',
            'country': 'UK',
            'county': self.county.id,
            'age_group': self.age_group.id,
            'has_business': 'False',
            'is_wheeler': 'True',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_signup_form_with_profile_photo(self):
        """Valid signup including a profile photo should save the image to profile."""
        photo = get_test_image()
        form = CustomSignupForm(data={
            'username': 'signupwithphoto',
            'email': 'signupwithphoto@example.com',
            'confirm_email': 'signupwithphoto@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'first_name': 'Photo',
            'last_name': 'User',
            'country': 'UK',
            'county': self.county.id,
            'age_group': self.age_group.id,
            'has_business': 'False',
            'is_wheeler': 'True',
            'mobility_devices': [self.mobility_device.id],
        }, files={'photo': photo})
        self.assertTrue(form.is_valid())
        factory = RequestFactory()
        request = factory.post(reverse('account_signup'))
        # Add a session to the request
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        user = form.save(request)
        profile = UserProfile.objects.get(user=user)
        self.assertTrue(bool(profile.photo))

    def test_signup_form_required_fields(self):
        """Verify presence/absence of required fields drives validity and related error keys."""
        age_group, _ = AgeGroup.objects.get_or_create(name='46-55', defaults={'label': '46 to 55'})
        county, _ = County.objects.get_or_create(name='SignupCounty', defaults={'label': 'Signup County'})
        mobility_device, _ = MobilityDevice.objects.get_or_create(name='walker', defaults={'label': 'Walker'})

        form = CustomSignupForm(data={
            'username': 'signupuser4',
            'email': 'signup4@example.com',
            'confirm_email': 'signup4@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'first_name': 'Sign',
            'last_name': 'Up',
            'country': 'UK',
            'county': county.id,
            'age_group': age_group.id,
            'has_business': 'False',
            'is_wheeler': 'True',
            'mobility_devices': [mobility_device.id],
        })
        self.assertTrue(form.is_valid())

        form = CustomSignupForm(data={
            'username': 'signupuser5',
            'email': 'signup5@example.com',
            'confirm_email': 'signup5@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'last_name': 'Up',
            'country': 'UK',
            'county': county.id,
            'age_group': age_group.id,
            'has_business': 'False',
            'is_wheeler': 'True',
            'mobility_devices': [mobility_device.id],
        })
        self.assertFalse(form.is_valid())
        self.assertIn('first_name', form.errors)

        form = CustomSignupForm(data={
            'username': 'signupuser6',
            'email': 'signup6@example.com',
            'confirm_email': 'signup6@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'first_name': 'Sign',
            'country': 'UK',
            'county': county.id,
            'age_group': age_group.id,
            'has_business': 'False',
            'is_wheeler': 'True',
            'mobility_devices': [mobility_device.id],
        })
        self.assertFalse(form.is_valid())
        self.assertIn('last_name', form.errors)

        form = CustomSignupForm(data={
            'username': 'signupuser7',
            'email': 'signup7@example.com',
            'confirm_email': 'signup7@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'first_name': 'Sign',
            'last_name': 'Up',
            'country': 'UK',
            'age_group': age_group.id,
            'has_business': 'False',
            'is_wheeler': 'True',
            'mobility_devices': [mobility_device.id],
        })
        self.assertFalse(form.is_valid())
        self.assertIn('county', form.errors)

        form = CustomSignupForm(data={
            'username': 'signupuser8',
            'email': 'signup8@example.com',
            'confirm_email': 'signup8@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'first_name': 'Sign',
            'last_name': 'Up',
            'country': 'UK',
            'county': county.id,
            'has_business': 'False',
            'is_wheeler': 'True',
            'mobility_devices': [mobility_device.id],
        })
        self.assertFalse(form.is_valid())
        self.assertIn('age_group', form.errors)

    def test_signup_form_business_fields(self):
        """Check business/wheeler combos, missing mobility devices, and invalid foreign keys."""
        county = County.objects.create(name='BusinessCounty', label='Business County')
        mobility_device, _ = MobilityDevice.objects.get_or_create(name='scooter', defaults={'label': 'Scooter'})
        form = CustomSignupForm(data={
            'username': 'businessuser',
            'email': 'business@example.com',
            'confirm_email': 'business@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'first_name': 'Business',
            'last_name': 'User',
            'country': 'UK',
            'county': county.id,
            'age_group': self.age_group.id,
            'has_business': 'True',
            'is_wheeler': 'True',
            'mobility_devices': [mobility_device.id],
        })
        self.assertTrue(form.is_valid())

        form = CustomSignupForm(data={
            'username': 'incompleteuser',
            'email': 'incomplete@example.com',
            'confirm_email': 'incomplete@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'first_name': 'Incomplete',
            'last_name': 'User',
            'country': 'UK',
            'county': county.id,
            'age_group': self.age_group.id,
            'has_business': 'True',
            'is_wheeler': 'True',
            # Missing mobility_devices
        })
        self.assertFalse(form.is_valid())
        self.assertIn('mobility_devices', form.errors)

        form = CustomSignupForm(data={
            'username': 'usernocountymob',
            'email': 'usernocountymob@example.com',
            'confirm_email': 'usernocountymob@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'first_name': 'NoCountyMob',
            'last_name': 'User',
            'country': 'UK',
            'county': '999',  # Non-existent county ID
            'age_group': '36-45',
            'has_business': 'True',
            'is_wheeler': 'True',
            'mobility_devices': ['888'],  # Non-existent device ID
        })
        self.assertFalse(form.is_valid())
        self.assertIn('county', form.errors)
        self.assertIn('mobility_devices', form.errors)

        # Test: is_wheeler True, no mobility_devices (should be invalid)
        form = CustomSignupForm(data={
            'username': 'incompleteuser',
            'email': 'incomplete@example.com',
            'confirm_email': 'incomplete@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'first_name': 'Incomplete',
            'last_name': 'User',
            'country': 'UK',
            'county': county.id,
            'age_group': self.age_group.id,
            'has_business': 'True',
            'is_wheeler': 'True',
            # 'mobility_devices' omitted
        })
        self.assertFalse(form.is_valid())
        self.assertIn('mobility_devices', form.errors)

        # Test: is_wheeler False, no mobility_devices (should be valid)
        form = CustomSignupForm(data={
            'username': 'nowheeleruser',
            'email': 'nowheeler@example.com',
            'confirm_email': 'nowheeler@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'first_name': 'NoWheeler',
            'last_name': 'User',
            'country': 'UK',
            'county': county.id,
            'age_group': self.age_group.id,
            'has_business': 'True',
            'is_wheeler': 'False',
            # 'mobility_devices' omitted
        })
        self.assertTrue(form.is_valid())


class UserProfileModelMethodTests(TestCase):
    """Tests for UserProfile model relations and string output behaviour."""

    def setUp(self):
        """Create a user and related reference objects for model tests."""
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        self.age_group = AgeGroup.objects.create(name='18-25', label='18 to 25')
        self.county = County.objects.create(name='Testshire', label='Testshire')
        self.mobility_device = MobilityDevice.objects.create(name='manual_wheelchair', label='Manual wheelchair')

    def test_profile_fields(self):
        """Assign and retrieve profile foreign key fields correctly."""
        profile = self.user.profile
        profile.age_group = self.age_group
        profile.county = self.county
        profile.save()
        self.assertEqual(profile.age_group.label, '18 to 25')
        self.assertEqual(profile.county.name, 'Testshire')

    def test_mobility_devices_many_to_many(self):
        """Add mobility device to M2M and ensure membership."""
        profile = self.user.profile
        profile.mobility_devices.add(self.mobility_device)
        self.assertIn(self.mobility_device, profile.mobility_devices.all())

    def test_get_full_name(self):
        """Check full name retrieval (direct or fallback)."""
        self.user.first_name = "Test"
        self.user.last_name = "User"
        self.user.save()
        profile = self.user.profile
        if hasattr(profile, "get_full_name"):
            self.assertEqual(profile.get_full_name(), "Test User")
        else:
            self.assertEqual(f"{self.user.first_name} {self.user.last_name}", "Test User")

    def test_is_business_owner(self):
        """Validate business ownership flag or property behaviour toggling has_business."""
        profile = self.user.profile
        if hasattr(profile, "is_business_owner"):
            self.assertFalse(profile.is_business_owner)
            profile.has_business = True
            profile.save()
            self.assertTrue(profile.is_business_owner)
        else:
            self.assertFalse(profile.has_business)
            profile.has_business = True
            profile.save()
            self.assertTrue(profile.has_business)

    def test_userprofile_str(self):
        """__str__ of profile should return associated username."""
        profile = self.user.profile
        self.assertEqual(str(profile), 'testuser')
      

class UserProfileFormTests(TestCase):
    """Tests for the UserProfileForm validation edge cases and success paths."""

    def setUp(self):
        """Create user and standard reference objects for form tests."""
        self.user = User.objects.create_user(username='formuser', email='form@example.com', password='testpass123')
        self.age_group = AgeGroup.objects.create(name='26-35', label='26 to 35')
        self.county = County.objects.create(name='formshire', label='Formshire')
        self.mobility_device = MobilityDevice.objects.create(name='power_wheelchair', label='Power wheelchair')

    def test_valid_form(self):
        """Complete form with required fields should validate successfully."""
        form = UserProfileForm(data={
            'first_name': 'Test',
            'last_name': 'User',
            'country': 'UK',
            'county': self.county.id,
            'age_group': self.age_group.id,
            'has_business': 'True',
            'is_wheeler': 'True',
            'mobility_devices': [self.mobility_device.id],
        })
        self.assertTrue(form.is_valid())

    def test_invalid_form_missing_required(self):
        """Missing all required fields should produce errors (e.g., first_name)."""
        form = UserProfileForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('first_name', form.errors)

    def test_form_edge_cases(self):
        """Validate multiple edge scenarios: bad IDs, blanks, unexpected fields, types."""
        form = UserProfileForm(data={
            'first_name': 'Edge',
            'last_name': 'Case',
            'country': 'UK',
            'county': 'not_an_id',
            'age_group': self.age_group.id,
            'has_business': 'True',
            'is_wheeler': 'True',
            'mobility_devices': [self.mobility_device.id],
        })
        self.assertFalse(form.is_valid())
        self.assertIn('county', form.errors)

        form = UserProfileForm(data={
            'first_name': 'Edge',
            'last_name': 'Case',
            'country': 'UK',
            'county': self.county.id,
            'age_group': self.age_group.id,
            'has_business': 'True',
            'is_wheeler': 'True',
            'mobility_devices': [self.mobility_device.id],
            'mobility_devices_other': '',
        })
        self.assertTrue(form.is_valid())

        form = UserProfileForm(data={
            'first_name': 'Edge',
            'last_name': 'Case',
            'country': 'UK',
            'county': self.county.id,
            'age_group': 'not_an_id',
            'has_business': 'True',
            'is_wheeler': 'True',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('age_group', form.errors)

        form = UserProfileForm(data={
            'first_name': 'Edge',
            'last_name': 'Case',
            'county': self.county.id,
            'age_group': self.age_group.id,
            'has_business': 'True',
            'is_wheeler': 'True',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('country', form.errors)

        form = UserProfileForm(data={
            'first_name': 'Edge',
            'last_name': 'Case',
            'country': 'UK',
            'county': self.county.id,
            'age_group': self.age_group.id,
            'has_business': 'True',
            'is_wheeler': 'True',
            'mobility_devices': 'not_a_list',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('mobility_devices', form.errors)

        form = UserProfileForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('first_name', form.errors)
        self.assertIn('last_name', form.errors)
        self.assertIn('country', form.errors)

        form = UserProfileForm(data={
            'first_name': 'Test',
            'last_name': 'User',
            'country': 'UK',
            'county': self.county.id,
            'age_group': self.age_group.id,
            'has_business': 'True',
            'is_wheeler': 'True',
            'mobility_devices': [self.mobility_device.id],
            'unexpected_field': 'surprise',
        })
        self.assertTrue(form.is_valid())


class UserProfileSignalTests(TestCase):
    """Tests for automatic UserProfile creation and uniqueness via signals."""

    def test_userprofile_created_on_user_creation(self):
        """Creating a user should automatically create its profile via signal."""
        user = get_user_model().objects.create_user(username='signaluser', email='signal@example.com', password='testpass123')
        self.assertTrue(UserProfile.objects.filter(user=user).exists())

    def test_userprofile_deleted_on_user_deletion(self):
        """Deleting a user should delete related profile (cascade)."""
        user = get_user_model().objects.create_user(username='signaluser2', email='signal2@example.com', password='testpass123')
        profile_id = user.profile.id
        user.delete()
        self.assertFalse(UserProfile.objects.filter(id=profile_id).exists())

    def test_userprofile_not_created_twice(self):
        """Signal should not create duplicate profiles on repeated get_or_create calls."""
        user = get_user_model().objects.create_user(username='signaluser3', email='signal3@example.com', password='testpass123')
        profile_count = UserProfile.objects.filter(user=user).count()
        UserProfile.objects.get_or_create(user=user)
        self.assertEqual(UserProfile.objects.filter(user=user).count(), profile_count)


class UserProfileContextProcessorTests(TestCase):
    """Tests for the user_profile context processor injecting profile only when authenticated."""

    def setUp(self):
        """Create a test user for context processor tests."""
        self.user = get_user_model().objects.create_user(username='contextuser', email='context@example.com', password='testpass123')

    def test_user_profile_injected_for_authenticated(self):
        """Authenticated request should include user_profile in context."""
        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.user
        context = user_profile(request)
        self.assertIn('user_profile', context)
        self.assertEqual(context['user_profile'], self.user.profile)

    def test_user_profile_not_injected_for_anonymous(self):
        """Anonymous user should not receive user_profile key in context."""
        factory = RequestFactory()
        request = factory.get('/')
        request.user = AnonymousUser()
        context = user_profile(request)
        self.assertNotIn('user_profile', context)


class EditProfileViewTests(TestCase):
    """Tests for edit profile view: auth, form processing, and field logic."""

    def setUp(self):
        """Create user, profile, and reference objects for the edit profile tests."""
        self.user = User.objects.create_user(
            username='edituser',
            email='edit@example.com',
            password='testpass123',
            first_name='Edit',
            last_name='Jones')
        self.profile = UserProfile.objects.get(user=self.user)
        self.age_group = AgeGroup.objects.create(name='26-35', label='26 to 35')
        self.county = County.objects.create(name='EditCounty', label='Edit County')
        self.mobility_device = MobilityDevice.objects.create(name='power_wheelchair', label='Power wheelchair')

    def test_edit_profile_view_authenticated(self):
        """Authenticated user should get 200 for edit profile page."""
        self.client.login(username='edituser', password='testpass123')
        response = self.client.get(reverse('edit_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit Profile')

    def test_edit_profile_view_unauthenticated(self):
        """Unauthenticated user should be redirected when accessing edit profile."""
        response = self.client.get(reverse('edit_profile'))
        self.assertEqual(response.status_code, 302)

    def test_edit_profile_template_content(self):
        """Edit profile page should contain expected form elements and JS includes."""
        self.client.login(username='edituser', password='testpass123')
        response = self.client.get(reverse('edit_profile'))
        content = response.content.decode()
        self.assertIn('<form', content)
        self.assertIn('csrfmiddlewaretoken', content)
        self.assertIn('first_name', content)
        self.assertIn('last_name', content)
        self.assertIn('country', content)
        self.assertIn('county', content)
        self.assertIn('has_business', content)
        self.assertIn('is_wheeler', content)
        self.assertIn('mobility_devices', content)
        self.assertIn('mobility_devices_other', content)
        self.assertIn('age_group', content)
        self.assertIn('Profile Photo', content)
        self.assertIn('input type="file"', content)
        self.assertIn('Save Changes', content)
        self.assertIn('Cancel', content)
        self.assertIn('src="/static/js/edit_profile', content)

    def test_edit_profile_permission(self):
        """Changes posted by another user should not modify target user's data."""
        other_user = User.objects.create_user(username='otheruser', email='other@example.com', password='testpass123')
        self.client.login(username='otheruser', password='testpass123')
        self.client.post(reverse('edit_profile'), {
            'first_name': 'Hacker',
            'last_name': 'User',
            'country': self.county.id,
            'county': self.county.id,
            'age_group': self.age_group.id,
            'has_business': 'False',
            'is_wheeler': 'True',
            'mobility_devices': [self.mobility_device.id],
        })
        self.user.refresh_from_db()
        self.assertNotEqual(self.user.first_name, 'Hacker')

    def test_edit_profile_post_valid(self):
        """Valid POST should redirect and persist updates."""
        self.client.login(username='edituser', password='testpass123')
        response = self.client.post(reverse('edit_profile'), {
            'first_name': 'Edit',
            'last_name': 'Post',
            'country': 'UK',
            'county': self.county.id,
            'age_group': self.age_group.id,
            'has_business': 'True',
            'is_wheeler': 'True',
            'mobility_devices': [self.mobility_device.id],
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Edit')

    def test_edit_profile_post_invalid(self):
        """Invalid POST should return form errors without persisting changes."""
        self.client.login(username='edituser', password='testpass123')
        response = self.client.post(reverse('edit_profile'), {
            'first_name': '',
            'last_name': '',
            'country': '',
            'county': '',
            'age_group': '',
        })
        form = response.context['form']
        self.assertIn('first_name', form.errors)
        self.assertIn('last_name', form.errors)
        self.assertIn('country', form.errors)
        self.assertIn('age_group', form.errors)
        self.assertIn('has_business', form.errors)
        self.assertIn('is_wheeler', form.errors)
        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Edit')

    def test_edit_profile_post_multiple_mobility_devices(self):
        """Selecting multiple mobility devices should persist both to profile."""
        device2 = MobilityDevice.objects.create(name='walker', label='Walker')
        self.client.login(username='edituser', password='testpass123')
        response = self.client.post(reverse('edit_profile'), {
            'first_name': 'Edit',
            'last_name': 'MultiDevice',
            'country': 'UK',
            'county': self.county.id,
            'age_group': self.age_group.id,
            'has_business': 'True',
            'is_wheeler': 'True',
            'mobility_devices': [self.mobility_device.id, device2.id],
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.profile.mobility_devices.count(), 2)

    def test_edit_profile_no_changes(self):
        """Posting unchanged data should not alter stored profile values."""
        self.client.login(username='edituser', password='testpass123')
        profile = self.user.profile
        profile.country = "UK"
        profile.save()
        data = {
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'country': profile.country,
            'county': profile.county_id or '',
            'age_group': profile.age_group_id or '',
            'mobility_devices': [d.id for d in profile.mobility_devices.all()],
            'mobility_devices_other': profile.mobility_devices_other or '',
            'is_wheeler': profile.is_wheeler,
            'has_business': profile.has_business,
        }
        self.client.post(reverse('edit_profile'), data)
        profile.refresh_from_db()
        self.assertEqual(profile.country, "UK")

    def test_edit_profile_change_single_field(self):
        """Changing a subset of fields should only update those fields."""
        self.client.login(username='edituser', password='testpass123')
        old_last_name = self.user.last_name
        data = {
            'first_name': 'Changed',
            'last_name': self.user.last_name,
            'country': 'UK',
            'county': self.county.id,
            'age_group': self.age_group.id,
            'mobility_devices': [self.mobility_device.id],
            'mobility_devices_other': 'Test device',
            'is_wheeler': 'True',
            'has_business': 'True',
        }
        self.client.post(reverse('edit_profile'), data)
        self.user.profile.refresh_from_db()
        self.user = User.objects.get(pk=self.user.pk)
        self.assertEqual(self.user.first_name, 'Changed')
        self.assertEqual(self.user.last_name, old_last_name)

    def test_edit_profile_optional_fields(self):
        """Optional field updates (county, age_group, devices) should persist correctly."""
        county = County.objects.create(name='EdgeCounty', label='Edge County')
        age_group = AgeGroup.objects.create(name='18-25', label='18 to 25')
        device = MobilityDevice.objects.create(name='manual_wheelchair', label='Manual wheelchair')
        self.client.login(username='edituser', password='testpass123')
        data = {
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'country': 'UK',
            'county': county.id,
            'age_group': age_group.id,
            'mobility_devices': [device.id],
            'mobility_devices_other': 'Test device',
            'is_wheeler': 'True',
            'has_business': 'True',
        }
        self.client.post(reverse('edit_profile'), data)
        profile = self.user.profile
        profile.refresh_from_db()
        self.assertEqual(profile.county, county)
        self.assertEqual(profile.age_group, age_group)
        self.assertIn(device, profile.mobility_devices.all())
        self.assertEqual(profile.mobility_devices_other, 'Test device')

    def test_edit_profile_invalid_foreign_keys(self):
        """Invalid FK values should trigger validation errors on those fields."""
        self.client.login(username='edituser', password='testpass123')
        data = {
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'country': 'UK',
            'county': 9999,
            'age_group': 9999,
            'mobility_devices': [9999],
            'mobility_devices_other': '',
            'is_wheeler':  'False',
            'has_business':  'False',
        }
        response = self.client.post(reverse('edit_profile'), data)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertFormError(form, 'county', 'Select a valid choice. That choice is not one of the available choices.')
        self.assertFormError(form, 'age_group', 'Select a valid choice. That choice is not one of the available choices.')

    def test_edit_profile_remove_photo(self):
        """Submitting with photo-clear should remove existing profile photo."""
        self.client.login(username='edituser', password='testpass123')
        profile = self.user.profile
        photo = get_test_image()
        profile.photo.save('test.jpg', photo, save=True)
        self.client.post(reverse('edit_profile'), {
            'first_name': 'Remove',
            'last_name': 'Photo',
            'country': 'UK',
            'county': self.county.id,
            'age_group': self.age_group.id,
            'has_business': 'False',
            'is_wheeler': 'False',
            'photo-clear': 'on',
        })
        self.user.refresh_from_db()
        self.assertFalse(bool(self.user.profile.photo))

    def test_edit_profile_photo_upload(self):
        """Uploading a valid image should store it on the profile."""
        self.client.login(username='edituser', password='testpass123')
        img = Image.new('RGB', (100, 100), color='red')
        buf = BytesIO()
        img.save(buf, format='JPEG')
        buf.seek(0)
        photo = SimpleUploadedFile("test.jpg", buf.read(), content_type="image/jpeg")
        response = self.client.post(reverse('edit_profile'), {
            'first_name': 'Edit',
            'last_name': 'Photo',
            'country': 'UK',
            'county': self.county.id,
            'age_group': self.age_group.id,
            'has_business': 'True',
            'is_wheeler': 'True',
            'mobility_devices': [self.mobility_device.id],
            'photo': photo,
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(bool(self.user.profile.photo))

    def test_edit_profile_invalid_photo_upload(self):
        """Invalid file type should raise validation error on photo field."""
        self.client.login(username='edituser', password='testpass123')
        bad_photo = SimpleUploadedFile("test.txt", b"not an image", content_type="text/plain")
        response = self.client.post(reverse('edit_profile'), {
            'first_name': 'Edit',
            'last_name': 'BadPhoto',
            'country': 'UK',
            'county': self.county.id,
            'age_group': self.age_group.id,
            'has_business': 'True',
            'is_wheeler': 'True',
            'mobility_devices': [self.mobility_device.id],
            'photo': bad_photo,
        })
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFormError(form, 'photo', 'Please upload a PNG, JPEG or WEBP profile photo. SVG or other formats are not allowed.')

    def test_edit_profile_invalid_image_extension(self):
        # Purpose: Ensure that uploading a non-image file as a profile photo returns a validation error.
        self.client.login(username='edituser', password='testpass123')
        bad_file = SimpleUploadedFile("bad.txt", b"notanimage", content_type="text/plain")
        response = self.client.post(reverse('edit_profile'), {
            'country': 'UK',
            'photo': bad_file,
        })
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertFormError(form, 'photo', 'Please upload a PNG, JPEG or WEBP profile photo. SVG or other formats are not allowed.')

    def test_edit_profile_missing_required_field(self):
        # Purpose: Ensure that omitting a required field (country) in the edit profile form returns a validation error.
        self.client.login(username='edituser', password='testpass123')
        response = self.client.post(reverse('edit_profile'), {
            # 'country' is omitted
        })
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertFormError(form, 'country', 'This field is required.')

    def test_edit_profile_remove_all_optional_fields(self):
        self.client.login(username='edituser', password='testpass123')
        profile = self.user.profile
        profile.county = self.county
        profile.age_group = self.age_group
        profile.mobility_devices.add(self.mobility_device)
        profile.mobility_devices_other = "Test"
        profile.save()
        data = {
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'country': 'UK',
            'county': self.county.id,
            'age_group': self.age_group.id,
            'mobility_devices': [],
            'mobility_devices_other': '',
            'is_wheeler': 'False',
            'has_business': 'True',
        }
        response = self.client.post(reverse('edit_profile'), data)
        profile.refresh_from_db()
        self.user.profile.refresh_from_db()
        profile = self.user.profile
        self.assertEqual(profile.mobility_devices.count(), 0)
        self.assertEqual(profile.mobility_devices_other, '')

    def test_edit_profile_set_and_unset_is_wheeler(self):
        self.client.login(username='edituser', password='testpass123')
        # Set is_wheeler True
        data = {
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'country': 'UK',
            'county': self.county.id,
            'age_group': self.age_group.id,
            'is_wheeler': 'True',
            'has_business': 'True',
            'mobility_devices': [self.mobility_device.id],
        }
        response = self.client.post(reverse('edit_profile'), data)
        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()
        profile = self.user.profile
        self.assertTrue(profile.is_wheeler)
        # Set is_wheeler False
        data['is_wheeler'] = 'False'
        response = self.client.post(reverse('edit_profile'), data)
        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()
        profile = self.user.profile
        self.assertFalse(profile.is_wheeler)

    def test_edit_profile_set_and_unset_has_business(self):
        self.client.login(username='edituser', password='testpass123')
        # Set has_business True
        data = {
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'country': 'UK',
            'county': self.county.id,
            'age_group': self.age_group.id,
            'is_wheeler': 'True',
            'has_business': 'True',
            'mobility_devices': [self.mobility_device.id],
        }
        response = self.client.post(reverse('edit_profile'), data)
        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()
        profile = self.user.profile
        self.assertTrue(profile.has_business)
        # Set has_business  'False'
        data['has_business'] = 'False'
        response = self.client.post(reverse('edit_profile'), data)
        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()
        profile = self.user.profile
        self.assertFalse(profile.has_business)


class ProfilePhotoTests(TestCase):
    """
    Tests for profile photo display, upload, removal, and validation.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='photouser',
            email='photo@example.com',
            password='testpass123',
            first_name='Edit',
            last_name='Photo'
        )
        self.client.login(username='photouser', password='testpass123')
        self.profile = self.user.profile
        # Add required non-optional fields for the profile form
        self.county = County.objects.create(name='PhotoCounty', label='Photo County')
        self.age_group = AgeGroup.objects.create(name='36-45', label='36 to 45')
        self.profile.has_business = 'False'
        self.profile.is_wheeler = 'False'
        self.profile.save()

    def test_dashboard_displays_actual_profile_photo(self):
        """
        If the user has uploaded a profile photo, the dashboard displays it (not the placeholder).
        """
        photo = get_test_image()
        self.profile.photo.save('test.jpg', photo, save=True)
        response = self.client.get(reverse('account_dashboard'))
        # Should contain the uploaded photo's URL, not the placeholder
        self.assertIn(self.profile.photo.url, response.content.decode())
        self.assertNotIn('profile_photo_placeholder', response.content.decode())

    def test_edit_profile_photo_upload(self):
        """
        Test uploading a valid profile photo using a real in-memory image.
        """
        img = Image.new('RGB', (100, 100), color='red')
        buf = BytesIO()
        img.save(buf, format='JPEG')
        buf.seek(0)
        photo = SimpleUploadedFile("test.jpg", buf.read(), content_type="image/jpeg")
        response = self.client.post(reverse('edit_profile'), {
            'first_name': 'Edit',
            'last_name': 'Photo',
            'country': 'UK',
            'county': self.county.id,
            'age_group': self.age_group.id,
            'has_business': 'False',
            'is_wheeler': 'False',
            'photo': photo,
        })
        self.assertEqual(response.status_code, 302)
        self.profile.refresh_from_db()
        self.assertTrue(bool(self.profile.photo))

    def test_edit_profile_remove_photo(self):
        """
        Removing a profile photo (if your form supports it) clears the photo.
        """
        photo = get_test_image()
        self.profile.photo.save('test.jpg', photo, save=True)
        response = self.client.post(reverse('edit_profile'), {
            'first_name': 'Remove',
            'last_name': 'Photo',
            'country': 'UK',
            'county': self.county.id,
            'age_group': self.age_group.id,
            'has_business': 'False',
            'is_wheeler': 'False',
            'photo-clear': 'on',
        })
        self.profile.refresh_from_db()
        self.assertFalse(bool(self.profile.photo))

    def test_edit_profile_invalid_photo_upload(self):
        # Test uploading an invalid photo file type
        bad_photo = SimpleUploadedFile("test.txt", b"not an image", content_type="text/plain")
        response = self.client.post(reverse('edit_profile'), {
            'first_name': 'Edit',
            'last_name': 'BadPhoto',
            'country': 'UK',
            'county': self.county.id,
            'age_group': self.age_group.id,
            'has_business': 'False',
            'is_wheeler': 'False',
            'photo': bad_photo,
        })
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFormError(form, 'photo', 'Please upload a PNG, JPEG or WEBP profile photo. SVG or other formats are not allowed.')

    def test_delete_and_upload_new_photo(self):
        """Removing then re-uploading a profile photo should persist the new image."""
        photo = get_test_image()
        self.profile.photo.save('test.jpg', photo, save=True)
        self.client.post(reverse('edit_profile'), {
            'first_name': 'Remove',
            'last_name': 'Photo',
            'country': 'UK',
            'county': self.county.id,
            'age_group': self.age_group.id,
            'has_business': 'False',
            'is_wheeler': 'False',
            'photo-clear': 'on',
        })
        self.profile.refresh_from_db()
        self.assertFalse(bool(self.profile.photo))
        photo2 = get_test_image()
        self.client.post(reverse('edit_profile'), {
            'first_name': 'Reupload',
            'last_name': 'Photo',
            'country': 'UK',
            'county': self.county.id,
            'age_group': self.age_group.id,
            'has_business': 'False',
            'is_wheeler': 'False',
            'photo': photo2,
        })
        self.profile.refresh_from_db()
        self.assertTrue(bool(self.profile.photo))

    def test_upload_too_large_or_invalid_photo(self):
        """Oversized or invalid formatted images should trigger appropriate errors."""
        big_file = SimpleUploadedFile("big.jpg", b"x" * (6 * 1024 * 1024), content_type="image/jpeg")
        response = self.client.post(reverse('edit_profile'), {
            'first_name': 'Big',
            'last_name': 'File',
            'country': 'UK',
            'county': self.county.id,
            'age_group': self.age_group.id,
            'has_business': 'False',
            'is_wheeler': 'False',
            'photo': big_file,
        })
        form = response.context['form']
        self.assertFormError(form, 'photo', 'Profile photo file too large (maximum 5 MB).')
        bad_file = SimpleUploadedFile("bad.txt", b"notanimage", content_type="text/plain")
        response = self.client.post(reverse('edit_profile'), {
            'first_name': 'Bad',
            'last_name': 'File',
            'country': 'UK',
            'county': self.county.id,
            'age_group': self.age_group.id,
            'has_business': 'False',
            'is_wheeler': 'False',
            'photo': bad_file,
        })
        form = response.context['form']
        self.assertFormError(form, 'photo', 'Please upload a PNG, JPEG or WEBP profile photo. SVG or other formats are not allowed.')


class DashboardViewTests(TestCase):
    """Tests for account dashboard visibility, redirects, and conditional content."""

    def setUp(self):
        """Create a user to exercise dashboard scenarios."""
        self.user = User.objects.create_user(username='viewuser', email='view@example.com', password='testpass123')

    def test_account_dashboard_view_authenticated(self):
        """Authenticated user should see dashboard (status 200)."""
        self.client.login(username='viewuser', password='testpass123')
        response = self.client.get(reverse('account_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.username)

    def test_account_dashboard_view_unauthenticated(self):
        """Unauthenticated user should be redirected from dashboard."""
        response = self.client.get(reverse('account_dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_account_dashboard_view_unauthenticated_redirect_url(self):
        """Redirect URL should contain login path with next parameter."""
        response = self.client.get(reverse('account_dashboard'))
        self.assertRedirects(response, f'/accounts/login/?next={reverse("account_dashboard")}')

    def test_dashboard_redirects_unauthenticated(self):
        """Dashboard should redirect to login for anonymous users."""
        response = self.client.get(reverse('account_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_dashboard_template_used(self):
        """Correct template should be used for dashboard view."""
        self.client.login(username='viewuser', password='testpass123')
        response = self.client.get(reverse('account_dashboard'))
        self.assertTemplateUsed(response, 'accounts/account_dashboard.html')

    def test_dashboard_renders_profile_fields(self):
        """Dashboard should display both core and optional profile information when present."""
        self.client.login(username='viewuser', password='testpass123')
        profile = self.user.profile
        profile.country = "UK"
        county = County.objects.create(name='Testshire', label='Testshire')
        age_group = AgeGroup.objects.create(name='18-25', label='18 to 25')
        device = MobilityDevice.objects.create(name='manual_wheelchair', label='Manual wheelchair')
        profile.county = county
        profile.age_group = age_group
        profile.is_wheeler = True
        profile.has_business = True
        profile.save()
        profile.mobility_devices.add(device)
        response = self.client.get(reverse('account_dashboard'))
        # Always rendered
        self.assertContains(response, "viewuser")
        self.assertContains(response, "view@example.com")
        self.assertContains(response, "UK")
        # Conditionally rendered
        self.assertContains(response, "Testshire")  # County
        self.assertContains(response, "18 to 25")   # Age Group
        self.assertContains(response, "Manual wheelchair")  # Mobility Device
        # Header (first/last name)
        self.assertContains(response, f"{self.user.first_name} {self.user.last_name}")

    def test_dashboard_profile_photo_placeholder(self):
        """Placeholder image should render when no profile photo exists."""
        self.client.login(username='viewuser', password='testpass123')
        response = self.client.get(reverse('account_dashboard'))
        self.assertContains(response, 'profile_photo_placeholder')

    def test_dashboard_wheeler_section_shown(self):
        """Wheeler-specific sections should render for wheeler users with related data."""
        self.client.login(username='viewuser', password='testpass123')
        profile = self.user.profile
        profile.is_wheeler = True
        profile.save()

        business = Business.objects.create(
            business_owner=profile,
            business_name="Test Biz",
            location=Point(-0.1278, 51.5074),
        )
        WheelerVerificationApplication.objects.create(
            wheeler=self.user,
            business=business,
            approved=True
        )

        UserModel = get_user_model()
        other_user = UserModel.objects.create_user(username='pendinguser', email='pending@example.com', password='testpass123')
        other_profile = other_user.profile

        pending_business = Business.objects.create(
            business_owner=other_profile,
            business_name="Pending Biz",
            location=Point(-0.1279, 51.5075),
        )
        WheelerVerificationApplication.objects.create(
            wheeler=self.user,
            business=pending_business,
            approved=False
        )

        response = self.client.get(reverse('account_dashboard'))

        # Always rendered for wheelers
        self.assertContains(response, "Wheeler Accessibility Verification")
        # Rendered if there are approved businesses to verify
        self.assertContains(response, "Businesses you have been approved to verify")
        # Rendered if there are pending applications
        self.assertContains(response, "Businesses you have applied to verify")

    def test_dashboard_wheeler_section_hidden_for_non_wheeler(self):
        """Non-wheeler users should not see wheeler-only headings/content."""
        self.client.login(username='viewuser', password='testpass123')
        profile = self.user.profile
        profile.is_wheeler = False
        profile.save()
        response = self.client.get(reverse('account_dashboard'))
        content = response.content.decode()
        self.assertNotIn("Wheeler Accessibility Verification", content)
        self.assertNotIn("Businesses you have been approved to verify", content)
        self.assertNotIn("Businesses you have applied to verify", content)

    def test_dashboard_displays_mobility_devices_other(self):
        """mobility_devices_other text should display if set on profile."""
        self.client.login(username='viewuser', password='testpass123')
        profile = self.user.profile
        profile.is_wheeler = True
        profile.mobility_devices_other = "Hoverboard"
        profile.save()
        response = self.client.get(reverse('account_dashboard'))
        self.assertContains(response, "Hoverboard")

    def test_dashboard_handles_missing_profile(self):
        """Dashboard should render safely (no 500) if profile missing unexpectedly."""
        self.client.login(username='viewuser', password='testpass123')
        UserProfile.objects.filter(user=self.user).delete()
        response = self.client.get(reverse('account_dashboard'))
        self.assertNotEqual(response.status_code, 500)
        self.assertIn("Personal Dashboard", response.content.decode())


class TemplateTagTest(TestCase):
    """Tests for custom template tag filters in account_extras module."""

    def test_device_labels_filter(self):
        """device_labels filter should output comma-separated labels for devices."""
        device1 = MobilityDevice.objects.create(name='Manual wheelchair', label='Manual wheelchair')
        device2 = MobilityDevice.objects.create(name='Power wheelchair', label='Power wheelchair')

        class Devices:
            def all(self_inner):
                return [device1, device2]
        template = Template("{% load account_extras %}{{ devices|device_labels }}")
        rendered = template.render(Context({'devices': Devices()}))
        self.assertIn('Manual wheelchair', rendered)
        self.assertIn('Power wheelchair', rendered)

    def test_dict_get_filter(self):
        """dict_get filter should retrieve correct value for given key."""
        template = Template("{% load account_extras %}{{ mydict|dict_get:'foo' }}")
        rendered = template.render(Context({'mydict': {'foo': 'bar'}}))
        self.assertIn('bar', rendered)

    def test_filter_unverified_filter(self):
        """filter_unverified should return only items marked unverified per status dict."""
        class BusinessObj:
            def __init__(self, id):
                self.id = id
        b1 = BusinessObj(1)
        b2 = BusinessObj(2)
        businesses = [b1, b2]
        verification_status = {1: True, 2: False}
        template = Template(
            "{% load account_extras %}{% for b in businesses|filter_unverified:verification_status %}{{ b.id }},{% endfor %}"
        )
        rendered = template.render(Context({'businesses': businesses, 'verification_status': verification_status}))
        self.assertIn('2,', rendered)
        self.assertNotIn('1,', rendered)
