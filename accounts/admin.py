from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from .models import UserProfile
from hijack.contrib.admin import HijackUserAdminMixin


class UserProfileInline(admin.StackedInline):
    """
    Inline admin interface for editing UserProfile within the User admin.
    """
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


class UserAdmin(HijackUserAdminMixin, DefaultUserAdmin):
    """
    Custom User admin that includes the UserProfile inline.
    """
    inlines = (UserProfileInline,)
    # show profile fields in user list
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_wheeler', 'has_business')

    def get_hijack_user(self, obj):
        """
        This enables admin users to "hijack" (log in as) another user.
        Returns the user instance to be impersonated by the django-hijack admin integration. 
        """
        return obj
    
    def is_wheeler(self, obj):
        """
        Check if the user is a wheeler based on their profile.
        """
        try:
            return obj.profile.is_wheeler
        except UserProfile.DoesNotExist:
            return False
    # Tell Django admin to display the result from is_wheeler as a boolean icon (checkmark or cross) in the admin list.
    is_wheeler.boolean = True
    # Sets the column header in the admin list to "Is Wheeler".
    is_wheeler.short_description = 'Is Wheeler'

    def has_business(self, obj):
        """
        Check if the user has a business based on their profile.
        """
        try:
            return obj.profile.has_business
        except UserProfile.DoesNotExist:
            return False
    # Display as boolean icon in admin list.
    has_business.boolean = True
    # Sets the column header in the admin list to "Has Business".
    has_business.short_description = 'Has Business'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for the UserProfile model.
    """
    list_display = (
        'user', 'email', 'country', 'county', 'is_wheeler', 'has_business',
        'mobility_devices_list', 'age_group', 'created_at', 'updated_at'
    )

    def email(self, obj):
        return obj.user.email
    email.short_description = 'Email'
    search_fields = ('user__username', 'user__email')
    
    def mobility_devices_list(self, obj):
        """Show mobility devices in a comma-separated list"""
        return ", ".join(device.name for device in obj.mobility_devices.all())
    mobility_devices_list.short_description = 'Mobility Devices'
    
admin.site.unregister(User) # Unregister the default User admin
admin.site.register(User, UserAdmin) # Register the custom User admin