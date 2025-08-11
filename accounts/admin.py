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
        'mobility_devices', 'age_group', 'created_at', 'updated_at'
    )

    def email(self, obj):
        return obj.user.email
    email.short_description = 'Email'
    search_fields = ('user__username', 'user__email')

class UserAdmin(HijackUserAdminMixin, DefaultUserAdmin):
    inlines = (UserProfileInline,)
    def get_hijack_user(self, obj):
        # Return the user instance to impersonate
        return obj

admin.site.unregister(User) # Unregister the default User admin
admin.site.register(User, UserAdmin) # Register the custom User admin