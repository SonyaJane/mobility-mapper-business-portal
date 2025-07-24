
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from accounts.models import UserProfile


@login_required
def dashboard_view(request):
    approved_businesses = []
    pending_businesses = []
    profile = getattr(request.user, 'userprofile', None)
    if profile and profile.is_wheeler:
        from businesses.models import WheelerVerificationRequest, Business
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
    return render(request, 'accounts/account_dashboard.html', {
        'approved_businesses': approved_businesses,
        'pending_businesses': pending_businesses,
    })

@login_required
def postlogin_redirect(request):
    user_profile = UserProfile.objects.get(user=request.user)
    if hasattr(user_profile, 'has_business') and user_profile.has_business:
        return redirect('business_dashboard')
    return redirect('account_dashboard')
