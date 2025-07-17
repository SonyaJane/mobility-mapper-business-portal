from .models import UserProfile

def user_profile(request):
    """Context processor to add user profile to the context.
    and make it available in templates."""
     # Check if user is authenticated and has a UserProfile
    if request.user.is_authenticated:
        try:
            profile = UserProfile.objects.get(user=request.user)
            return {'user_profile': profile}
        except UserProfile.DoesNotExist:
            pass
    return {}
