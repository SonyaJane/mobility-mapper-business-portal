from django.conf import settings

def os_api_key(request):
    return {
        'OS_MAPS_API_KEY': settings.OS_MAPS_API_KEY
    }
    
def wheeler_history(request):
    """
    Expose a flag to show Wheeler Verification History link for verified Wheelers
    """
    show = False
    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        if profile and getattr(profile, 'is_wheeler', False):
            from businesses.models import WheelerVerificationRequest, WheelerVerification
            has_req = WheelerVerificationRequest.objects.filter(wheeler=request.user).exists()
            has_ver = WheelerVerification.objects.filter(wheeler=request.user).exists()
            show = has_req or has_ver
    return {'show_wheeler_history': show}
