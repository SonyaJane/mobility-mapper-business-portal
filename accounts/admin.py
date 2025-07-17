from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for UserProfile model. Provides:
    A table view showing both the user and their has_business status.
    The ability to search by username or email
    """
    list_display = ('user', 'has_business')
    search_fields = ('user__username', 'user__email')
