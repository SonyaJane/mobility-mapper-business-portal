from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from accounts.models import UserProfile
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from .forms import UserProfileForm

from businesses.models import WheelerVerificationRequest, Business, WheelerVerification


@login_required
def edit_profile(request):
    profile = request.user.userprofile
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
    approved_businesses = []
    pending_businesses = []
    business_verification_status = {}
    verified_businesses = []
    verification_reports = []
    profile = getattr(request.user, 'userprofile', None)
    # user profile photo
    profile_photo = profile.photo.url if profile and profile.photo else None
    if profile and profile.is_wheeler:
        approved_business_ids = WheelerVerificationRequest.objects.filter(
            wheeler=request.user,
            approved=True
        ).values_list('business_id', flat=True)
        pending_business_ids = WheelerVerificationRequest.objects.filter(
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
    user_profile = UserProfile.objects.get(user=request.user)
    if hasattr(user_profile, 'has_business') and user_profile.has_business:
        return redirect('business_dashboard')
    return redirect('account_dashboard')


def validate_username(request):
    """AJAX endpoint to check if a username is available."""
    username = request.GET.get('username', '').strip()
    User = get_user_model()
    available = not User.objects.filter(username__iexact=username).exists()
    return JsonResponse({'available': available})
