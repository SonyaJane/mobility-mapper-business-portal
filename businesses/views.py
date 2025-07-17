from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import BusinessRegistrationForm
from accounts.models import UserProfile

@login_required
def register_business(request):
    user_profile = UserProfile.objects.get(user=request.user)

    # Redirect if business already exists
    if user_profile.has_business:
        return redirect('dashboard')

    if request.method == 'POST':
        form = BusinessRegistrationForm(request.POST)
        if form.is_valid():
            business = form.save(commit=False)
            business.owner = request.user
            business.save()

            # Update user profile
            user_profile.has_business = True
            user_profile.save()

            return redirect('dashboard')
    else:
        form = BusinessRegistrationForm()

    return render(request, 'businesses/register_business.html', {'form': form})
