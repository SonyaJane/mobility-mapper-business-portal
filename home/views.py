from django.shortcuts import render

def index(request):
    """
    Returns the index page with context for business/wheeler dashboard buttons.
    Uses the has_business and has_registered_business attributes from the UserProfile model.
    """
    has_business = False
    has_registered_business = False

    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        # Use the UserProfile fields directly
        has_business = request.user.profile.has_business
        has_registered_business = request.user.profile.has_registered_business

    # Attach these as attributes for template compatibility
    if request.user.is_authenticated:
        request.user.has_business = has_business
        request.user.has_registered_business = has_registered_business

    return render(
        request,
        'home/index.html',
        {
            'page_title': 'Home',
        }
    )
