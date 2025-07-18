from unicodedata import category
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from accounts.models import UserProfile
from .forms import BusinessRegistrationForm, WheelerVerificationForm
from .models import Business, WheelerVerification, CATEGORY_CHOICES
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.conf import settings
from django.core.serializers import serialize
from django.contrib.gis.geos import GEOSGeometry


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


@login_required
def request_wheeler_verification(request, pk):
    business = get_object_or_404(Business, pk=pk, owner=request.user)

    if not business.is_wheeler_verified and not business.wheeler_verification_requested:
        business.wheeler_verification_requested = True
        business.save()
        messages.success(request, "Verification request sent.")
    else:
        messages.info(request, "Verification already requested or completed.")

    return redirect('business_dashboard')


@login_required
def submit_wheeler_verification(request, pk):
    business = get_object_or_404(Business, pk=pk)

     # Ensure user is a wheeler
    profile = getattr(request.user, 'userprofile', None)
    if not profile or not profile.is_wheeler:
        messages.error(request, "You must be a verified Wheeler to submit a verification.")
        return redirect('home')
    
    # Prevent double-verifying
    if WheelerVerification.objects.filter(business=business, wheeler=request.user).exists():
        messages.info(request, "You have already verified this business.")
        return redirect('home')
    
    if request.method == 'POST':
        form = WheelerVerificationForm(request.POST)
        if form.is_valid():
            verification = form.save(commit=False)
            verification.business = business
            verification.wheeler = request.user
            verification.save()
            
            # Automatically approve if >= 3 verifications
            if business.verifications.count() >= 3:
                business.verified_by_wheelers = True
                # clear the verification request flag
                business.wheeler_verification_requested = False
                business.save()
            
            messages.success(request, "Thank you for verifying this business!")
            return redirect('home')
    else:
        form = WheelerVerificationForm()

    return render(request, 'businesses/submit_verification.html', {
        'form': form,
        'business': business,
    })
    
    
def public_business_detail(request, pk):
    business = get_object_or_404(Business, pk=pk, is_approved=True)

    has_user_verified = False
    if request.user.is_authenticated and hasattr(request.user, 'userprofile') and request.user.userprofile.is_wheeler:
        has_user_verified = WheelerVerification.objects.filter(business=business, wheeler=request.user).exists()

    return render(request, 'businesses/public_business_detail.html', {
        'business': business,
        'has_user_verified': has_user_verified,
        'OS_MAPS_API_KEY': settings.OS_MAPS_API_KEY,
    })
    
    
def public_business_list(request):
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    businesses = Business.objects.filter(is_approved=True)

    if query:
        businesses = businesses.filter(
            Q(name__icontains=query) |
            Q(address__icontains=query) |
            Q(description__icontains=query)
        )

    if category:
            businesses = businesses.filter(category=category)

    categories = [c for c in CATEGORY_CHOICES]
    businesses = businesses.order_by('name')
    paginator = Paginator(businesses, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    geojson = []
    for biz in page_obj:
        if biz.location:
            geojson.append({
                'id': biz.id,
                'name': biz.name,
                'lat': biz.location.y,
                'lng': biz.location.x,
                'verified': biz.verified_by_wheelers,
            })
            
    return render(request, 'businesses/public_business_list.html', {
        'businesses': page_obj,
        'query': query,
        'category': category,
        'categories': categories,
        'geojson': geojson,
        'OS_MAPS_API_KEY': settings.OS_MAPS_API_KEY,
    })