from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect

from accounts.models import UserProfile
from businesses.models import Business
from verification.models import WheelerVerificationApplication, WheelerVerification

from .forms import UserProfileForm


@login_required
def edit_profile(request):
    """
    Display and process the user profile edit form.
    
    GET: Renders the profile edit form pre-populated with the current user's data.
    POST: Validates and saves submitted profile changes, then redirects to the account dashboard.
    
    Parameters:
        request (HttpRequest): The incoming request object (must be authenticated).
    
    Returns:
        HttpResponse: Rendered edit profile template on GET or invalid POST.
        HttpResponseRedirect: Redirect to 'account_dashboard' after successful save.
    """
    # Ensure a UserProfile exists for the current user
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('account_dashboard')
    else:
        form = UserProfileForm(instance=profile)
    return render(request, 'accounts/edit_profile.html', {'form': form, 'page_title': 'Edit Profile'})


@login_required
def dashboard_view(request):
    """
    Render the personal dashboard for the authenticated user.
    
    If the user is a wheeler, aggregates:
      - Approved and pending business verification applications
      - Whether the user has submitted verifications for approved businesses
      - A list of businesses the user has verified and related report data
    
    Always includes the user's profile photo (if present).

    Parameters:
        request (HttpRequest): The authenticated request.
    
    Returns:
        HttpResponse: Rendered dashboard template with context data.
    """
    approved_businesses = []
    pending_businesses = []
    business_verification_status = {}
    verified_businesses = []
    verification_reports = []
    profile = getattr(request.user, 'profile', None)
    # user profile photo
    profile_photo = profile.photo.url if profile and profile.photo else None
    if profile and profile.is_wheeler:
        approved_business_ids = WheelerVerificationApplication.objects.filter(
            wheeler=request.user,
            approved=True
        ).values_list('business_id', flat=True)
        pending_business_ids = WheelerVerificationApplication.objects.filter(
            wheeler=request.user,
            approved=False
        ).values_list('business_id', flat=True)
        approved_businesses = Business.objects.filter(id__in=approved_business_ids)
        pending_businesses = Business.objects.filter(id__in=pending_business_ids)
        # For each approved business, check if a verification has been submitted by this user
        for business in approved_businesses:
            has_verification = WheelerVerification.objects.filter(business=business, wheeler=request.user).exists()
            business_verification_status[business.id] = has_verification
        # Businesses the user has verified
        verifications = WheelerVerification.objects.filter(wheeler=request.user)
        for verification in verifications:
            verified_businesses.append(verification.business)
            verification_reports.append({
                'business': verification.business,
                'approved': verification.approved,
                'date_verified': verification.date_verified,
            })
    return render(request, 'accounts/account_dashboard.html', {
        'profile_photo': profile_photo,
        'approved_businesses': approved_businesses,
        'pending_businesses': pending_businesses,
        'business_verification_status': business_verification_status,
        'verification_reports': verification_reports,
        'page_title': 'Personal Dashboard',
    })


@login_required
def postlogin_redirect(request):
    """
    Decide post-login routing based on the user's profile.
    
    If the user owns/manages a business, redirect to the business dashboard;
    otherwise redirect to the personal account dashboard. Ensures a profile exists.
    
    Parameters:
        request (HttpRequest): The authenticated request.
    
    Returns:
        HttpResponseRedirect: Redirect to 'business_dashboard' or 'account_dashboard'.
    """
    # Ensure a profile exists for routing decisions
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if hasattr(user_profile, 'has_business') and user_profile.has_business:
        return redirect('business_dashboard')
    return redirect('account_dashboard')


def validate_username(request):
    """AJAX endpoint to check if a username is available.
    
    Expects 'username' as a GET parameter.
    
    Parameters:
        request (HttpRequest): The incoming request.
    
    Returns:
        JsonResponse: {'available': bool} indicating availability.
    """
    username = request.GET.get('username', '').strip()
    User = get_user_model()
    available = not User.objects.filter(username__iexact=username).exists()
    return JsonResponse({'available': available})
