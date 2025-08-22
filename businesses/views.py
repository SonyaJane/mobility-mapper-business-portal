from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django import template
from django.contrib import messages

from accounts.models import UserProfile
from businesses.models import Business, Category, AccessibilityFeature
from .forms import BusinessRegistrationForm, WheelerVerificationForm
from .models import Business, WheelerVerification, PricingTier, Category, WheelerVerificationRequest
from .models import Category

# custom template filter for dictionary access
register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@login_required
def register_business(request):
    # Get the user profile and active pricing tiers
    user_profile = UserProfile.objects.get(user=request.user)
    pricing_tiers = PricingTier.objects.filter(is_active=True)
    
    # Redirect if user already has a business record
    from .models import Business
    try:
        Business.objects.get(business_owner=user_profile)
        return redirect('business_dashboard')
    except Business.DoesNotExist:
        pass

    import json
    if request.method == 'POST':
        post_data = request.POST.copy()
        try:
            if post_data.get('opening_hours'):
                json.loads(post_data['opening_hours'])
        except Exception:
            post_data['opening_hours'] = ''
        form = BusinessRegistrationForm(post_data, request.FILES)
        if form.is_valid():
            business = form.save(commit=False)
            business.business_owner = request.user.userprofile
            billing_frequency = form.cleaned_data.get('billing_frequency')
            request.session['billing_frequency'] = billing_frequency
            business.opening_hours = post_data.get('opening_hours', '')
            business.save()
            # Persist categories and accessibility features
            form.save_m2m()
            # Handle custom 'Other' category text
            other_cat = form.cleaned_data.get('other_category')
            if other_cat:
                from django.template.defaultfilters import slugify
                from .models import Category as CatModel
                slug = slugify(other_cat)
                category_obj, created = CatModel.objects.get_or_create(code=slug, defaults={'name': other_cat})
                business.categories.add(category_obj)
            # Update user profile flags
            user_profile.has_business = True
            user_profile.has_registered_business = True
            user_profile.save()
            return redirect('business_dashboard')
    else:
        form = BusinessRegistrationForm()

    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    # Determine selected values to preserve on form error
    if request.method == 'POST':
        selected_categories = request.POST.getlist('categories')
        selected_accessibility_features = request.POST.getlist('accessibility_features')
    else:
        selected_categories = []
        selected_accessibility_features = []
    return render(request, 'businesses/register_business.html', {
        'form': form,
        'pricing_tiers': pricing_tiers,
        'days_of_week': days_of_week,
        'selected_categories': selected_categories,
        'selected_accessibility_features': selected_accessibility_features,
        'page_title': 'Register Your Business',
    })
    
@require_GET
def business_detail(request, pk):
    """
    Public-facing business details page.
    """
    business = get_object_or_404(Business, pk=pk, is_approved=True)
    # Parse opening_hours JSON for display
    import json
    opening_hours = None
    try:
        if business.opening_hours:
            opening_hours = json.loads(business.opening_hours)
    except Exception:
        opening_hours = None
    # Prepare JSON for client-side map rendering
    business_json = {
        "business_name": business.business_name,
        "location": {
            "x": business.location.x,
            "y": business.location.y,
        },
    }
    # Check if current wheeler user has already requested verification
    user_has_requested = False
    user_request_approved = False
    profile = getattr(request.user, 'userprofile', None)
    if request.user.is_authenticated and profile and profile.is_wheeler:
        from .models import WheelerVerificationRequest
        user_has_requested = WheelerVerificationRequest.objects.filter(
            business=business,
            wheeler=request.user,
            approved=False
        ).exists()
        user_request_approved = WheelerVerificationRequest.objects.filter(
            business=business,
            wheeler=request.user,
            approved=True
        ).exists()
    return render(request, 'businesses/business_detail.html', {
        'business': business,
        'opening_hours': opening_hours,
        'page_title': business.business_name,
        'business_json': business_json,
        'user_has_requested': user_has_requested,
        'user_request_approved': user_request_approved,
    })

@login_required
def business_dashboard(request):
    import json
    try:
        business = Business.objects.get(business_owner=request.user.userprofile)
    except Business.DoesNotExist:
        business = None

    # print debug info
    # print all business attributes
    if business:
        for attr, value in business.__dict__.items():
            if not attr.startswith('_'):
                print(f"Business {attr}: {value}")

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
        }
        # Parse and normalize opening_hours JSON for server-side table rendering
        if business.opening_hours:
            try:
                raw = json.loads(business.opening_hours)
                normalized = {}
                for day, info in raw.items():
                    periods = []
                    # Legacy format: dict with 'closed' and 'periods'
                    if isinstance(info, dict) and 'periods' in info:
                        if not info.get('closed', False):
                            for p in info.get('periods', []):
                                start = p.get('open')
                                end = p.get('close')
                                if start and end:
                                    periods.append({'start': start, 'end': end})
                    # New list-only format
                    elif isinstance(info, list):
                        for p in info:
                            start = p.get('start') or p.get('open')
                            end = p.get('end') or p.get('close')
                            if start and end:
                                periods.append({'start': start, 'end': end})
                    normalized[day] = periods
                opening_hours_dict = normalized
            except Exception:
                opening_hours_dict = None
        else:
            opening_hours_dict = None

    if business and business.logo:
        logo_url = business.logo.url  
    else:
        logo_url = ''
        
    return render(request, 'businesses/business_dashboard.html', {
        'business': business,
        'logo_url': logo_url,
        'business_json': business_json,
        'verifications': verifications,
        'user_verifications': user_verifications,
        'verification_status': verification_status,
        'verification_approved': verification_approved,
        'opening_hours_dict': opening_hours_dict,
        'page_title': 'Business Dashboard',
    })
 
@login_required
def business_request_wheeler_verification(request, pk):
    # Allow business owner to request Wheelers to verify their business
    business = get_object_or_404(Business, pk=pk, business_owner=request.user.userprofile)
    if request.method == 'POST':
        business.wheeler_verification_requested = True
        business.save()
        messages.success(request, "Your request to have Wheelers verify your business has been sent.")
        return redirect('business_dashboard')
    return render(request, 'businesses/business_request_wheeler_verification.html', {'business': business})

@login_required
def wheeler_verification_history(request):
    profile = getattr(request.user, 'userprofile', None)
    is_superuser = request.user.is_superuser
    if not profile or (not profile.is_wheeler and not is_superuser):
        messages.error(request, "Only verified Wheelers can view their verification history.")
        return redirect('home')

    requests = WheelerVerificationRequest.objects.filter(wheeler=request.user).order_by('-requested_at')
    # For each request, annotate whether a verification has been submitted and approved
    # For wheelers, build status, approval, and ID mappings for their verifications
    verification_status = {}
    verification_approved = {}
    verification_id_map = {}
    for req in requests:
        verification = WheelerVerification.objects.filter(business=req.business, wheeler=req.wheeler).first()
        if verification:
            verification_status[req.id] = True
            verification_approved[req.id] = verification.approved
            verification_id_map[req.id] = verification.id
        else:
            verification_status[req.id] = False
            verification_approved[req.id] = False
            verification_id_map[req.id] = None
    return render(request, 'businesses/wheeler_verification_history.html', {
        'requests': requests,
        'verification_status': verification_status,
        'verification_approved': verification_approved,
        'verification_id_map': verification_id_map,
        'page_title': 'Your Verification History',
    })


@login_required
def edit_business(request):
    business = get_object_or_404(Business, business_owner=request.user.userprofile)

    pricing_tiers = PricingTier.objects.filter(is_active=True)
    import json
    if request.method == 'POST':
        post_data = request.POST.copy()
        # Remove '__other__' marker so categories field validation passes
        if post_data.getlist('categories'):
            cleaned = [c for c in post_data.getlist('categories') if c != '__other__']
            post_data.setlist('categories', cleaned)
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
            # Persist categories and accessibility features
            form.save_m2m()
            # Handle custom 'Other' category text
            other_cat = form.cleaned_data.get('other_category')
            if other_cat:
                from django.template.defaultfilters import slugify
                from .models import Category
                slug = slugify(other_cat)
                category_obj, created = Category.objects.get_or_create(
                    code=slug,
                    defaults={'name': other_cat}
                )
                business.categories.add(category_obj)
            messages.success(request, "Business updated successfully.")
            return redirect('business_dashboard')
    else:
        # Deserialize opening_hours JSON for the form field
        initial = business.opening_hours if business.opening_hours else ''
        form = BusinessRegistrationForm(instance=business, initial={'opening_hours': initial})

    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    # Determine selected values for pre-selecting in template
    if request.method == 'POST':
        selected_categories = request.POST.getlist('categories')
        selected_accessibility_features = request.POST.getlist('accessibility_features')
    else:
        # initial render: use instance categories and features
        selected_categories = [str(pk) for pk in business.categories.values_list('pk', flat=True)]
        selected_accessibility_features = [str(pk) for pk in business.accessibility_features.values_list('pk', flat=True)]
    return render(request, 'businesses/edit_business.html', {
        'form': form,
        'pricing_tiers': pricing_tiers,
        'days_of_week': days_of_week,
        'selected_categories': selected_categories,
        'selected_accessibility_features': selected_accessibility_features,
        'page_title': 'Edit Your Business',
    })


@login_required
def explore_plans(request):
    """Display available subscription plans for businesses to review and select."""
    pricing_tiers = PricingTier.objects.filter(is_active=True).order_by('price_per_month')
    # Determine the current user's subscription tier if they have a business
    current_tier = None
    try:
        profile = request.user.userprofile
        business = Business.objects.get(business_owner=profile)
        current_tier = business.pricing_tier
    except Exception:
        current_tier = None
    # Determine higher-tier upgrade options
    upgrade_tiers = [tier for tier in pricing_tiers if not current_tier or tier.price_per_month > current_tier.price_per_month]
    upgrade_count = len(upgrade_tiers)
    return render(request, 'businesses/explore_plans.html', {
        'pricing_tiers': pricing_tiers,
        'current_tier': current_tier,
        'upgrade_tiers': upgrade_tiers,
        'upgrade_count': upgrade_count,
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

    return render(request, 'businesses/delete_business_confirm.html', {'business': business, 'page_title': 'Delete Your Business'})


@login_required
def wheeler_verification_application(request, pk):

    business = get_object_or_404(Business, pk=pk, is_approved=True)
    profile = getattr(request.user, 'userprofile', None)
    if not request.user.is_authenticated or not profile or not profile.is_wheeler:
        messages.error(request, "Only verified Wheelers can request to verify a business.")
        return redirect('accessible_business_search')

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

    return render(request, 'businesses/wheeler_verification_application.html', {
        'business': business,
        'verification_count': verification_count,
        'required_verifications': required_verifications,
        'cost_per_verification': cost_per_verification,
        'wheeler_share': wheeler_share,
        'page_title': 'Request Wheeler Verification',
    })


@login_required
def wheeler_verification_form(request, pk):
    business = get_object_or_404(Business, pk=pk)
    profile = getattr(request.user, 'userprofile', None)
    if not profile or not profile.is_wheeler:
        messages.error(request, "You must be a verified Wheeler to submit a verification.")
        return redirect('account_dashboard')

    # Prevent double-verifying
    if WheelerVerification.objects.filter(business=business, wheeler=request.user).exists():
        messages.info(request, "You have already verified this business.")
        return redirect('account_dashboard')

    if request.method == 'POST':
        # Debug: list POST and FILES dict keys
        print("POST keys:", list(request.POST.keys()))
        print("FILES keys:", list(request.FILES.keys()))
        form = WheelerVerificationForm(request.POST, request.FILES, business=business)
        if form.is_valid():
            # Debug: confirm uploaded files
            uploaded = request.FILES.getlist('photos')
            print("Uploaded files:", [f.name for f in uploaded])
            verification = form.save(commit=False)
            verification.business = business
            verification.wheeler = request.user
            verification.mobility_device = request.POST.get('mobility_device')
            # Save the verification instance
            verification.save()
            # Persist M2M feature selections explicitly
            confirmed = form.cleaned_data.get('confirmed_features') or []
            additional = form.cleaned_data.get('additional_features') or []
            verification.confirmed_features.set(confirmed)
            verification.additional_features.set(additional)
            # Handle feature-specific photo uploads for any confirmed or additional feature
            import re
            from .models import WheelerVerificationPhoto
            for field_name in request.FILES:
                # Match fields named feature_photo_<feature_pk>
                m = re.match(r'^feature_photo_(?P<pk>\d+)$', field_name)
                if not m:
                    continue
                feature_pk = int(m.group('pk'))
                try:
                    feature = AccessibilityFeature.objects.get(pk=feature_pk)
                except AccessibilityFeature.DoesNotExist:
                    continue
                # Save each uploaded file for this feature
            for upload in request.FILES.getlist(field_name):
                # Reset file pointer after any prior reads
                try:
                    upload.file.seek(0)
                except Exception:
                    pass
                WheelerVerificationPhoto.objects.create(
                    verification=verification,
                    image=upload,
                    feature=feature
                )
            # Handle general photo uploads
            for photo in request.FILES.getlist('photos'):
                # Reset file pointer before upload
                try:
                    photo.file.seek(0)
                except Exception:
                    pass
                WheelerVerificationPhoto.objects.create(verification=verification, image=photo)

            # Automatically approve if >= 3 verifications
            if business.verifications.count() >= 3:
                business.verified_by_wheelers = True
                business.wheeler_verification_requested = False
                business.save()

            # Debug: list all photos now linked to this verification
            all_photos = [(p.id, p.feature_id, p.image.name) for p in verification.photos.all()]
            print(f"Photos linked to verification {verification.id}: {all_photos}")
            messages.success(request, "Thank you for verifying this business! Please check your email for confirmation.")
            return redirect('account_dashboard')
    else:
        form = WheelerVerificationForm(business=business)

    return render(request, 'businesses/wheeler_verification_form.html', {
        'form': form,
        'business': business,
        'page_title': 'Submit Wheeler Verification',
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
        'page_title': 'Pending Verification Requests',
    })


@login_required
def verification_report(request, verification_id):
    verification = get_object_or_404(WheelerVerification, pk=verification_id)
    # Allow business owner or the Wheeler who submitted to view the report
    is_owner = (verification.business.business_owner == request.user.userprofile)
    is_wheeler = (verification.wheeler == request.user)
    # Allow superusers to view any report
    is_superuser = request.user.is_superuser
    if not (is_owner or is_wheeler or is_superuser):
        messages.error(request, "You do not have permission to view this report.")
        return redirect('business_dashboard')

    # Hide wheeler name if business owner is viewing
    show_wheeler_name = not (hasattr(request.user, 'userprofile') and verification.business.business_owner == request.user.userprofile)
    # Precompute URLs for feature-specific photos and other photos
    feature_photos_list = []
    confirmed_features = verification.confirmed_features.all()
    for feature in confirmed_features:
        photo = verification.photos.filter(feature=feature).first()
        if photo:
            url = photo.image.url
            feature_photos_list.append({'feature': feature, 'url': url})
    # Other photos without a feature
    other_photo_urls = []
    for photo in verification.photos.filter(feature__isnull=True):
        try:
            url = photo.image.url
        except Exception:
            url = str(photo.image)
        other_photo_urls.append(url)
    return render(request, 'businesses/wheeler_verification_report.html', {
        'verification': verification,
        'confirmed_features': confirmed_features,
        'feature_photos_list': feature_photos_list,
        'other_photo_urls': other_photo_urls,
        'show_wheeler_name': show_wheeler_name,
        'page_title': 'Verification Report',
    })
    

@require_GET
def ajax_search_businesses(request):
    print("AJAX search triggered", request.GET)
    term = request.GET.get('q', '').strip()
    cat_id = request.GET.get('category')
    # allow multiple accessibility filters
    access = request.GET.getlist('accessibility')
    qs = Business.objects.all()
    if term:
        qs = qs.filter(
            Q(business_name__icontains=term) |
            Q(description__icontains=term) |
            Q(categories__name__icontains=term) |
            Q(categories__tags__contains=[term])
        )
    if cat_id:
        qs = qs.filter(categories__id=cat_id)
    if access:
        # filter businesses matching all of the selected features
        for feature in access:
            qs = qs.filter(accessibility_features__name=feature)
        qs = qs.distinct()
    # Attempt to filter by map viewport bounds, suppress any errors
    try:
        min_lat = request.GET.get('min_lat')
        min_lng = request.GET.get('min_lng')
        max_lat = request.GET.get('max_lat')
        max_lng = request.GET.get('max_lng')
        if min_lat and min_lng and max_lat and max_lng:
            min_lat_f, max_lat_f = float(min_lat), float(max_lat)
            min_lng_f, max_lng_f = float(min_lng), float(max_lng)
            qs = qs.filter(
                location__y__gte=min_lat_f,
                location__y__lte=max_lat_f,
                location__x__gte=min_lng_f,
                location__x__lte=max_lng_f
            )
    except Exception:
        # If spatial lookup fails (e.g., unsupported backend), ignore bounds filter
        pass
    results = []
    for biz in qs.distinct():
        # Determine logo URL (empty string if no logo)
        logo_url = biz.logo.url if getattr(biz, 'logo', None) else ''
        results.append({
            'id': biz.id,
            'business_name': biz.business_name,
            'categories': list(biz.categories.values_list('name', flat=True)),
            'address': biz.address,
            'location': {'lat': biz.location.y, 'lng': biz.location.x} if biz.location else None,
            'is_wheeler_verified': getattr(biz, 'verified_by_wheelers', False),
            'accessibility_features': list(biz.accessibility_features.values_list('name', flat=True)),
            'public_phone': biz.public_phone,
            'contact_phone': biz.contact_phone,
            'public_email': biz.public_email,
            'website': biz.website,
            'opening_hours': biz.opening_hours,
            'special_offers': biz.special_offers,
            'services_offered': biz.services_offered,
            'description': biz.description,
            'logo': logo_url,
            'wheeler_verification_requested': biz.wheeler_verification_requested,
        })
    return JsonResponse({'businesses': results})


def accessible_business_search(request):
    """
    Called when accessible business search page is loaded.
    JS carries out initial search.
    """
    user_profile = None
    if request.user.is_authenticated:
        from accounts.models import UserProfile
        user_profile = UserProfile.objects.get(user=request.user)
    
    # Provide full list of accessibility features for the filter dropdown
    accessibility_features = AccessibilityFeature.objects.all()
    return render(request, 'businesses/accessible_business_search.html', {
        'is_verified_wheeler': bool(user_profile and user_profile.is_wheeler),
        'accessibility_features': accessibility_features,
        'page_title': 'Accessible Business Search',
    })
    
    
@login_required
def cancel_wheeler_verification_request(request, business_id):
    """Allow a wheeler to cancel their pending verification request for a business."""
    profile = getattr(request.user, 'userprofile', None)
    if not profile or not profile.is_wheeler:
        messages.error(request, "Only verified Wheelers can cancel verification requests.")
        return redirect('account_dashboard')
    # Find and delete the pending request
    req = WheelerVerificationRequest.objects.filter(
        business_id=business_id,
        wheeler=request.user,
        approved=False
    ).first()
    if req:
        req.delete()
        messages.success(request, "Your verification request has been cancelled.")
    else:
        messages.info(request, "No pending verification request found to cancel.")
    return redirect('account_dashboard')
