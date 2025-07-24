
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from accounts.models import UserProfile


@login_required
def dashboard_view(request):
    return render(request, 'accounts/account_dashboard.html')

@login_required
def postlogin_redirect(request):
    user_profile = UserProfile.objects.get(user=request.user)
    if hasattr(user_profile, 'has_business') and user_profile.has_business:
        return redirect('business_dashboard')
    return redirect('account_dashboard')
