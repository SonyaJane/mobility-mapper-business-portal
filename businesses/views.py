from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from accounts.models import UserProfile
from .forms import BusinessRegistrationForm
from .models import Business
from django.contrib import messages

@login_required
def register_business(request):
    user_profile = UserProfile.objects.get(user=request.user)

    # Redirect if business already exists
    if user_profile.has_business:
        return redirect('business_dashboard')

    if request.method == 'POST':
        form = BusinessRegistrationForm(request.POST)
        if form.is_valid():
            business = form.save(commit=False)
            business.owner = request.user
            business.save()

            # Update user profile
            user_profile.has_business = True
            user_profile.save()

            return redirect('business_dashboard')
    else:
        form = BusinessRegistrationForm()

    return render(request, 'businesses/register_business.html', {'form': form})


@login_required
def business_dashboard(request):
    try:
        business = Business.objects.get(owner=request.user)
    except Business.DoesNotExist:
        business = None

    return render(request, 'businesses/business_dashboard.html', {'business': business})


@login_required
def edit_business(request):
    business = get_object_or_404(Business, owner=request.user)

    if request.method == 'POST':
        form = BusinessRegistrationForm(request.POST, instance=business)
        if form.is_valid():
            form.save()
            messages.success(request, "Business updated successfully.")
            return redirect('business_dashboard')
    else:
        form = BusinessRegistrationForm(instance=business)

    return render(request, 'businesses/edit_business.html', {'form': form})


@login_required
def delete_business(request):
    business = get_object_or_404(Business, owner=request.user)

    if request.method == 'POST':
        business.delete()

        # Update the user profile to reflect no business
        user_profile = request.user.userprofile
        user_profile.has_business = False
        user_profile.save()

        messages.success(request, "Business deleted successfully.")
        return redirect('business_dashboard')

    return render(request, 'businesses/delete_business_confirm.html', {'business': business})
