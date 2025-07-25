from django.contrib.auth.decorators import login_required

# Add custom template filter for dictionary access
from django import template
register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.conf import settings
from accounts.models import UserProfile
from .forms import BusinessRegistrationForm, WheelerVerificationForm
from .models import Business, WheelerVerification, PricingTier, Category
from django.http import JsonResponse
from .models import WheelerVerificationRequest

@login_required
def register_business(request):
    # Get the user profile and active pricing tiers
    user_profile = UserProfile.objects.get(user=request.user)
    pricing_tiers = PricingTier.objects.filter(is_active=True)
    
    # Redirect if business already exists
    if user_profile.has_business:
        return redirect('business_dashboard')

    import json
    if request.method == 'POST':
        post_data = request.POST.copy()
        try:
            if post_data.get('opening_hours'):
                json.loads(post_data['opening_hours'])
        except Exception:
            post_data['opening_hours'] = ''
        form = BusinessRegistrationForm(post_data)
        if form.is_valid():
            business = form.save(commit=False)
            business.business_owner = request.user.userprofile
            billing_frequency = form.cleaned_data.get('billing_frequency')
            request.session['billing_frequency'] = billing_frequency
            business.opening_hours = post_data.get('opening_hours', '')
            business.save()
            business.categories.set(form.cleaned_data.get('categories', []))
            business.accessibility_features.set(form.cleaned_data.get('accessibility_features', []))
            user_profile.has_business = True
            user_profile.save()
            return redirect('business_dashboard')
    else:
        form = BusinessRegistrationForm()

    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return render(request, 'businesses/register_business.html', {
        'form': form,
        'pricing_tiers': pricing_tiers,
        'days_of_week': days_of_week,
    })


@login_required
def business_dashboard(request):
    import json
    try:
        business = Business.objects.get(business_owner=request.user.userprofile)
    except Business.DoesNotExist:
        business = None

    verifications = business.verifications.all() if business else []

    # For wheelers, show their submitted verifications and approval status
    user_verifications = None
    verification_status = None
    verification_approved = None
    profile = getattr(request.user, 'userprofile', None)
    if profile and profile.is_wheeler:
        from .models import WheelerVerification
        user_verifications = WheelerVerification.objects.filter(wheeler=request.user)
        verification_status = {}
        verification_approved = {}
        for v in user_verifications:
            verification_status[v.business.id] = True
            verification_approved[v.business.id] = v.approved

    # Prepare a JSON-serializable dict for the map JS if business exists
    business_json = None
    opening_hours_dict = None
    if business:
        business_json = {
            "business_name": business.business_name,
            "location": {
                "x": business.location.x,
                "y": business.location.y,
            },
            # Add more fields if needed for JS
        }
        # Parse opening_hours JSON for server-side table rendering
        try:
            if business.opening_hours:
                opening_hours_dict = json.loads(business.opening_hours)
            else:
                opening_hours_dict = None
        except Exception:
            opening_hours_dict = None

    return render(request, 'businesses/business_dashboard.html', {
        'business': business,
        'business_json': business_json,
        'verifications': verifications,
        'user_verifications': user_verifications,
        'verification_status': verification_status,
        'verification_approved': verification_approved,
        'opening_hours_dict': opening_hours_dict,
    })


@login_required
def wheeler_verification_history(request):
    profile = getattr(request.user, 'userprofile', None)
    if not profile or not profile.is_wheeler:
        messages.error(request, "Only verified Wheelers can view their verification history.")
        return redirect('home')

    requests = WheelerVerificationRequest.objects.filter(wheeler=request.user).order_by('-requested_at')
    # For each request, annotate whether a verification has been submitted and approved
    verification_status = {}
    verification_approved = {}
    from .models import WheelerVerification
    for req in requests:
        verification = WheelerVerification.objects.filter(business=req.business, wheeler=req.wheeler).first()
        verification_status[req.id] = bool(verification)
        verification_approved[req.id] = verification.approved if verification else False
    return render(request, 'businesses/wheeler_verification_history.html', {
        'requests': requests,
        'verification_status': verification_status,
        'verification_approved': verification_approved,
    })



@login_required
def edit_business(request):
    business = get_object_or_404(Business, business_owner=request.user.userprofile)

    pricing_tiers = PricingTier.objects.filter(is_active=True)
    import json
    if request.method == 'POST':
        post_data = request.POST.copy()
        # Ensure opening_hours is stored as text
        try:
            if post_data.get('opening_hours'):
                # Validate it's valid JSON
                json.loads(post_data['opening_hours'])
        except Exception:
            post_data['opening_hours'] = ''
        form = BusinessRegistrationForm(post_data, request.FILES, instance=business)
        if form.is_valid():
            business = form.save(commit=False)
            business.business_owner = request.user.userprofile
            # Store opening_hours as text
            business.opening_hours = post_data.get('opening_hours', '')
            business.save()
            # Update categories
            business.categories.set(form.cleaned_data.get('categories', []))
            # Update accessibility features
            business.accessibility_features.set(form.cleaned_data.get('accessibility_features', []))
            messages.success(request, "Business updated successfully.")
            return redirect('business_dashboard')
    else:
        # Deserialize opening_hours JSON for the form field
        initial = business.opening_hours if business.opening_hours else ''
        form = BusinessRegistrationForm(instance=business, initial={'opening_hours': initial})

    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return render(request, 'businesses/edit_business.html', {
        'form': form,
        'pricing_tiers': pricing_tiers,
        'days_of_week': days_of_week,
    })


@login_required
def delete_business(request):
    business = get_object_or_404(Business, business_owner=request.user.userprofile)

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

    business = get_object_or_404(Business, pk=pk, is_approved=True)
    profile = getattr(request.user, 'userprofile', None)
    if not request.user.is_authenticated or not profile or not profile.is_wheeler:
        messages.error(request, "Only verified Wheelers can request to verify a business.")
        return redirect('public_business_detail', pk=pk)

    # Count current verifications
    verification_count = business.verifications.count()
    required_verifications = 2
    cost_per_verification = 20
    wheeler_share = 10

    # Prevent double-requesting
    if WheelerVerification.objects.filter(business=business, wheeler=request.user).exists():
        messages.info(request, "You have already verified this business.")
        return redirect('public_business_detail', pk=pk)

    if request.method == 'POST':
        from .models import WheelerVerificationRequest
        # Prevent duplicate requests
        if WheelerVerificationRequest.objects.filter(business=business, wheeler=request.user, approved=False).exists():
            return render(request, 'businesses/request_submitted.html', {'business': business})
        else:
            from django.core.mail import mail_admins
            WheelerVerificationRequest.objects.create(business=business, wheeler=request.user)
            mail_admins(
                subject="New Wheeler Verification Request",
                message=f"A new request to verify accessibility features has been submitted for {business.business_name} by {request.user.username}. Review and approve in the admin panel.",
            )
            return render(request, 'businesses/request_submitted.html', {'business': business})

    return render(request, 'businesses/request_wheeler_verification.html', {
        'business': business,
        'verification_count': verification_count,
        'required_verifications': required_verifications,
        'cost_per_verification': cost_per_verification,
        'wheeler_share': wheeler_share,
    })


@login_required
def submit_wheeler_verification(request, pk):
    business = get_object_or_404(Business, pk=pk)
    profile = getattr(request.user, 'userprofile', None)
    if not profile or not profile.is_wheeler:
        messages.error(request, "You must be a verified Wheeler to submit a verification.")
        return redirect('home')

    # Prevent double-verifying
    if WheelerVerification.objects.filter(business=business, wheeler=request.user).exists():
        messages.info(request, "You have already verified this business.")
        return redirect('home')

    if request.method == 'POST':
        form = WheelerVerificationForm(request.POST, request.FILES, business=business)
        if form.is_valid():
            verification = form.save(commit=False)
            verification.business = business
            verification.wheeler = request.user
            verification.mobility_device = request.POST.get('mobility_device')
            verification.save()

            # Save confirmed features and additional features
            confirmed = form.cleaned_data.get('confirmed_features')
            additional = form.cleaned_data.get('additional_features')
            # update business with new features
            if additional:
                for feature in additional:
                    business.accessibility_features.add(feature)
                business.save()


            # Handle photo uploads (save to WheelerVerificationPhoto model)
            photos = request.FILES.getlist('photos')
            from .models import WheelerVerificationPhoto
            for photo in photos:
                WheelerVerificationPhoto.objects.create(verification=verification, image=photo)

            # Automatically approve if >= 2 verifications
            if business.verifications.count() >= 2:
                business.verified_by_wheelers = True
                business.wheeler_verification_requested = False
                business.save()

            messages.success(request, "Thank you for verifying this business!")
            return redirect('home')
    else:
        form = WheelerVerificationForm(business=business)

    return render(request, 'businesses/submit_verification.html', {
        'form': form,
        'business': business,
    })
    
    
def public_business_detail(request, pk):
    business = get_object_or_404(Business, pk=pk, is_approved=True)

    has_user_verified = False
    has_pending_request = False
    if request.user.is_authenticated and hasattr(request.user, 'userprofile') and request.user.userprofile.is_wheeler:
        has_user_verified = WheelerVerification.objects.filter(business=business, wheeler=request.user).exists()
        from .models import WheelerVerificationRequest
        has_pending_request = WheelerVerificationRequest.objects.filter(
            business=business,
            wheeler=request.user,
            approved=False,
            reviewed=False
        ).exists()

    # Prepare a JSON-serializable dict for the map JS
    business_json = {
        "business_name": business.business_name,
        "location": {
            "x": business.location.x,
            "y": business.location.y,
        },
        # Add more fields if needed for JS
    }
    return render(request, 'businesses/public_business_detail.html', {
        'business': business,
        'business_json': business_json,
        'has_user_verified': has_user_verified,
        'has_pending_request': has_pending_request,
        'OS_MAPS_API_KEY': settings.OS_MAPS_API_KEY,
    })
    
    
def public_business_list(request):
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    businesses = Business.objects.filter(is_approved=True)

    if query:
        businesses = businesses.filter(
            Q(business_name__icontains=query) |
            Q(address__icontains=query) |
            Q(description__icontains=query)
        )

    if category:
        businesses = businesses.filter(categories__code=category)

    from .models import Category
    categories = list(Category.objects.all())
    businesses = businesses.order_by('business_name')
    paginator = Paginator(businesses, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    geojson = []
    for biz in page_obj:
        if biz.location:
            geojson.append({
                'id': biz.id,
                'name': biz.business_name,
                'lat': biz.location.y,
                'lng': biz.location.x,
                'verified': biz.verified_by_wheelers,
                'verification_requested': biz.wheeler_verification_requested,
                'address': biz.address,
                'categories': list(biz.categories.values_list('name', flat=True)),
                'accessibility_features': list(biz.accessibility_features.values_list('name', flat=True)),
            })
    return render(request, 'businesses/public_business_list.html', {
        'businesses': page_obj,
        'query': query,
        'category': category,
        'categories': categories,
        'geojson': geojson,
        'OS_MAPS_API_KEY': settings.OS_MAPS_API_KEY,
    })


@login_required
def pending_verification_requests(request):
    # Only show to wheelers
    profile = getattr(request.user, 'userprofile', None)
    if not profile or not profile.is_wheeler:
        messages.error(request, "Only verified Wheelers can view pending verification requests.")
        return redirect('home')

    businesses = Business.objects.filter(wheeler_verification_requested=True, verified_by_wheelers=False)
    from .models import WheelerVerificationRequest, WheelerVerification
    approved_business_ids = WheelerVerificationRequest.objects.filter(
        wheeler=request.user,
        approved=True
    ).values_list('business_id', flat=True)
    already_verified_business_ids = WheelerVerification.objects.filter(
        wheeler=request.user,
        approved=True
    ).values_list('business_id', flat=True)
    return render(request, 'businesses/pending_verification_requests.html', {
        'businesses': businesses,
        'approved_business_ids': list(approved_business_ids),
        'already_verified_business_ids': list(already_verified_business_ids),
    })
    
@login_required
def verification_report(request, verification_id):
    verification = get_object_or_404(WheelerVerification, pk=verification_id)
    # Only allow business owner to view their own business's reports
    if verification.business.business_owner != request.user.userprofile:
        messages.error(request, "You do not have permission to view this report.")
        return redirect('business_dashboard')

    # Hide wheeler name if business owner is viewing
    show_wheeler_name = not (hasattr(request.user, 'userprofile') and verification.business.business_owner == request.user.userprofile)
    return render(request, 'businesses/verification_report.html', {
        'verification': verification,
        'additional_features': [],
        'show_wheeler_name': show_wheeler_name,
    })
    