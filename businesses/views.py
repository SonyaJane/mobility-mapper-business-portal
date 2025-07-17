from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import BusinessProfileForm

@login_required
def business_register(request):
    if request.method == 'POST':
        form = BusinessProfileForm(request.POST)
        if form.is_valid():
            business = form.save(commit=False)
            business.owner = request.user
            business.save()
            return redirect('dashboard')
    else:
        form = BusinessProfileForm()
    
    return render(request, 'businesses/business_register.html', {'form': form})