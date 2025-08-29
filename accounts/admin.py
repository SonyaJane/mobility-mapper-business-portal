from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from .models import UserProfile
from hijack.contrib.admin import HijackUserAdminMixin

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
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

class UserAdmin(HijackUserAdminMixin, DefaultUserAdmin):
    inlines = (UserProfileInline,)
    # show profile fields in user list
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_wheeler', 'has_business')

    def get_hijack_user(self, obj):
        # Return the user instance to impersonate
        return obj
    def is_wheeler(self, obj):
        return getattr(obj.userprofile, 'is_wheeler', False)
    is_wheeler.boolean = True
    is_wheeler.short_description = 'Is Wheeler'

    def has_business(self, obj):
        return getattr(obj.userprofile, 'has_business', False)
    has_business.boolean = True
    has_business.short_description = 'Has Business'

admin.site.unregister(User) # Unregister the default User admin
admin.site.register(User, UserAdmin) # Register the custom User admin