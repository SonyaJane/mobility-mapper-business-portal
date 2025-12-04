"""
Views for the businesses app.

- Handles business registration, editing, dashboard, and membership management.
- Provides AJAX search and accessible business search functionality.
- Integrates with user profiles, membership tiers, accessibility features, and verification.
"""

import json
import random
from datetime import timedelta
from urllib.parse import urlencode

from django import template
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.views.decorators.http import require_GET

from .forms import BusinessRegistrationForm, BusinessUpdateForm
from .models import Category
from .models import Business, MembershipTier
from accounts.models import UserProfile
from businesses.models import Business, AccessibilityFeature
from checkout.models import Purchase
from verification.models import WheelerVerification

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Return the value for a given key from a dictionary.
    Used as a template filter.
    """
    return dictionary.get(key)


@login_required
def register_business(request):
    """
    Handle the registration of a new business by a user.

    - Redirects to dashboard if the user already owns a business.
    - On POST: validates and saves the business, sets membership tier, and updates user profile.
    - On GET: displays the registration form.
    - If a paid tier is selected, redirects to checkout.
    """
    # Get or create the user profile
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)

    # If the user already has a business, redirect to dashboard
    if Business.objects.filter(business_owner=user_profile).exists():
        return redirect('business_dashboard')

    # get active membership tiers
    membership_tiers = MembershipTier.objects.filter(is_active=True)
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    if request.method == 'POST':
        post_data = request.POST.copy()

        opening_hours = post_data.get('opening_hours')
        if opening_hours:
            json.loads(opening_hours)
        else:
            opening_hours = ''

        form = BusinessRegistrationForm(post_data, request.FILES)

        if form.is_valid():
            # save business
            business = form.save(commit=False)
            business.business_owner = user_profile
            business.opening_hours = opening_hours
            # get intended (selected) membership tier
            intended_tier = form.cleaned_data.get('membership_tier')
            # Set new businesses tier to Free until payment completes. If no Free tier row exists
            # fall back to the canonical Free tier with PK=1 (project convention).
            free_tier = MembershipTier.objects.filter(tier__iexact='free', is_active=True).first()
            if not free_tier:
                try:
                    free_tier = MembershipTier.objects.get(pk=1)
                except MembershipTier.DoesNotExist:
                    free_tier = None
            business.membership_tier = free_tier
            business.save()
            # Persist categories and accessibility features
            form.save_m2m()

            # Update user profile flags
            user_profile.has_business = True
            user_profile.has_registered_business = True
            user_profile.save()

            # If the user selected a paid tier, redirect to checkout using the intended tier id
            # (the business itself remains on Free until the webhook upgrades it on successful payment).
            if intended_tier and intended_tier.tier in ['standard', 'premium']:
                url = reverse('checkout', args=[business.id])
                # send both membership_tier and purchase type so to checkout
                return redirect(f"{url}?{urlencode({'membership_tier': intended_tier.id, 'purchase_type': 'membership'})}")

            # otherwise, go to dashboard
            return redirect('business_dashboard')
    else:
        form = BusinessRegistrationForm()

    # Preserve selections for form errors
    selected_categories = request.POST.getlist('categories') if request.method == 'POST' else []
    selected_accessibility_features = request.POST.getlist('accessibility_features') if request.method == 'POST' else []

    return render(request, 'businesses/register_business.html', {
        'form': form,
        'membership_tiers': membership_tiers,
        'days_of_week': days_of_week,
        'selected_categories': selected_categories,
        'selected_accessibility_features': selected_accessibility_features,
        'page_title': 'Register Your Business',
    })


@login_required
def business_dashboard(request):
    """
    Display the business dashboard for the current user.

    - Shows business details, logo, verifications, and opening hours.
    - For wheelers, shows their submitted verifications and approval status.
    - Prepares JSON data for map display.
    """
    try:
        business = Business.objects.get(business_owner=getattr(request.user, 'profile', None))
    except Business.DoesNotExist:
        business = None

    verifications = business.verifications.all() if business else []

    # For wheelers, show their submitted verifications and approval status
    user_verifications = None
    verification_status = None
    verification_approved = None
    profile = getattr(request.user, 'profile', None)
    if profile and profile.is_wheeler:
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
        # Parse and normalise opening_hours JSON for server-side table rendering
        if business.opening_hours:
            try:
                raw = json.loads(business.opening_hours)
                normalized = {}
                for day, info in raw.items():
                    periods = []
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
def edit_business(request):
    """
    Allow the business owner to edit their business details.

    - Handles form validation and updates business and related categories/features.
    - Supports updating opening hours and adding custom categories.
    """
    business = get_object_or_404(Business, business_owner=getattr(request.user, 'profile', None))
    membership_tiers = MembershipTier.objects.filter(is_active=True)

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
        form = BusinessUpdateForm(post_data, request.FILES, instance=business)
        if form.is_valid():
            business = form.save(commit=False)
            business.business_owner = getattr(request.user, 'profile', None)
            # Store opening_hours as text
            business.opening_hours = post_data.get('opening_hours', '')
            business.save()
            # Persist categories and accessibility features
            form.save_m2m()
            # Handle custom 'Other' category text
            other_cat = form.cleaned_data.get('other_category')
            if other_cat:
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
        form = BusinessUpdateForm(instance=business, initial={'opening_hours': initial})

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
        'membership_tiers': membership_tiers,
        'days_of_week': days_of_week,
        'selected_categories': selected_categories,
        'selected_accessibility_features': selected_accessibility_features,
        'page_title': 'Edit Your Business',
    })


@login_required
def upgrade_membership(request):
    """
    Display available membership plans for businesses to review and select.

    - Shows upgrade options based on current membership tier.
    - Provides all active membership tiers ordered by price.
    """
    business = get_object_or_404(Business, business_owner=getattr(request.user, 'profile', None))
    current_tier = business.membership_tier
    # get all membership tiers (ordered by the membership price field)
    all_membership_tiers = MembershipTier.objects.filter(is_active=True).order_by('membership_price')
    # Determine higher-tier upgrade options using membership_price if available
    upgrade_tiers = [tier for tier in all_membership_tiers if not current_tier or (getattr(tier, 'membership_price', getattr(tier, 'membership_price', 0)) > getattr(current_tier, 'membership_price', getattr(current_tier, 'membership_price', 0)))]
    upgrade_count = len(upgrade_tiers)
    return render(request, 'businesses/upgrade_membership.html', {
        'all_membership_tiers': all_membership_tiers,
        'current_tier': current_tier,
        'upgrade_tiers': upgrade_tiers,
        'upgrade_count': upgrade_count,
        'business': business,
        'page_title': 'Upgrade Membership',
    })


@login_required
def delete_business(request):
    """
    Allow the business owner to delete their business.

    - Updates the user profile to reflect the deletion.
    - Confirms deletion via POST.
    """
    business = get_object_or_404(Business, business_owner=getattr(request.user, 'profile', None))
    if request.method == 'POST':
        business.delete()

        # Update the user profile to reflect no business
        user_profile = getattr(request.user, 'profile', None)
        if user_profile:
            user_profile.has_business = False
            user_profile.save()

        messages.success(request, "Business deleted successfully.")
        return redirect('business_dashboard')

    return render(request, 'businesses/delete_business_confirm.html', {'business': business, 'page_title': 'Delete Your Business'})


@login_required
@require_GET
def ajax_search_businesses(request):
    """
    AJAX endpoint to search businesses based on filters.

    - Supports search by name, description, category, accessibility features, and map bounds.
    - Returns a JSON response with matching businesses, sorted by membership tier.
    """
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
    # Filter by map viewport bounds, suppress any errors
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
    # make a distinct list, shuffle to randomise order within tiers, then stable-sort by tier
    qs = list(qs.distinct())
    random.shuffle(qs)
    membership_order = {'premium': 1, 'standard': 2, 'free': 3}
    # sort is stable so the random order within each tier is preserved
    qs.sort(key=lambda b: membership_order.get(
        (b.membership_tier.tier if getattr(b, 'membership_tier', None) and getattr(b.membership_tier, 'tier', None) else 'free').lower(),
        4
    ))
    results = []
    for biz in qs:
        # Determine membership tier (default to 'free' if not set)
        membership_tier = biz.membership_tier.tier
        # Determine logo URL (empty string if no logo)
        # only show logo if not on free tier
        logo_url = biz.logo.url if getattr(biz, 'logo', None) and (membership_tier != 'free') else ''
        results.append({
            'id': biz.id,
            'business_name': biz.business_name,
            'categories': list(biz.categories.values_list('name', flat=True)),
            'street_address1': biz.street_address1,
            'street_address2': biz.street_address2,
            'town_or_city': biz.town_or_city,
            'county': biz.county,
            'postcode': biz.postcode,
            'location': {'lat': biz.location.y, 'lng': biz.location.x} if biz.location else None,
            'is_wheeler_verified': getattr(biz, 'verified_by_wheelers', False),
            'accessibility_features': list(biz.accessibility_features.values_list('name', flat=True)),
            'public_phone': biz.public_phone,
            'website': biz.website,
            'opening_hours': biz.opening_hours,
            # only if not on free tier
            'public_email': biz.public_email if membership_tier != 'free' else '',
            'facebook': biz.facebook_url if membership_tier != 'free' else '',
            'twitter': biz.x_twitter_url if membership_tier != 'free' else '',
            'instagram': biz.instagram_url if membership_tier != 'free' else '',
            'description': biz.description if membership_tier != 'free' else '',
            'special_offers': biz.special_offers if membership_tier != 'free' else '',
            'services_offered': biz.services_offered if membership_tier != 'free' else '',
            'logo': logo_url,
            'wheeler_verification_requested': biz.wheeler_verification_requested,
        })
    return JsonResponse({'businesses': results})


@login_required
def accessible_business_search(request):
    """
    Render the accessible business search page.

    - Provides a list of accessibility features for filtering.
    - Ensures the user profile exists.
    """
    user_profile = None
    if request.user.is_authenticated:
        user_profile, _ = UserProfile.objects.get_or_create(user=request.user)

    # Provide full list of accessibility features for the filter dropdown
    accessibility_features = AccessibilityFeature.objects.all()
    return render(
        request,
        'businesses/accessible_business_search.html',
        {
            'is_verified_wheeler': bool(user_profile and user_profile.is_wheeler),
            'accessibility_features': accessibility_features,
            'page_title': 'Accessible Business Search',
        }
    )


@login_required
def cancel_membership(request):
    """
    Downgrade the user's business to the free tier on membership cancellation.

    - Updates the business and notifies the user.
    - Handles missing profile or business gracefully.
    """
    profile = getattr(request.user, 'profile', None)
    if not profile:
        messages.error(request, "Unable to find your business profile.")
        return redirect('business_dashboard')
    try:
        business = Business.objects.get(business_owner=profile)
        free_tier = MembershipTier.objects.filter(tier='free', is_active=True).first()
        if not free_tier:
            try:
                free_tier = MembershipTier.objects.get(pk=1)
            except MembershipTier.DoesNotExist:
                free_tier = None

        if free_tier:
            business.membership_tier = free_tier
            business.billing_frequency = 'monthly'
            business.save()
            messages.success(request, "Membership cancelled; you have been moved to the Free tier.")
        else:
            messages.error(request, "Free tier not available.")
    except Business.DoesNotExist:
        messages.error(request, "No business found to cancel membership for.")
    return redirect('business_dashboard')


@login_required
def view_existing_membership(request):
    """
    Display current membership details for the user's business.

    - Shows membership tier, start date, and end date.
    - Handles missing profile or business gracefully.
    """
    profile = getattr(request.user, 'profile', None)
    if not profile:
        messages.error(request, "Unable to find your business profile.")
        return redirect('business_dashboard')
    try:
        business = Business.objects.get(business_owner=profile)
        current_tier = business.membership_tier
        # get membership tier object
        membership_tier = MembershipTier.objects.get(pk=current_tier.id)
        # get latest purchase with purchase_type='membership'
        membership_purchase = Purchase.objects.filter(business=business, purchase_type='membership').order_by('-created_at').first()
        start_date = membership_purchase.created_at if membership_purchase else None
        end_date = start_date + timedelta(days=366) if start_date else None
        return render(request, 'businesses/view_existing_membership.html', {
            'membership': membership_tier,
            'start_date': start_date,
            'end_date': end_date,
            'page_title': 'Current Membership Information',
        })
    except Business.DoesNotExist:
        messages.error(request, "No business found. Please register your business first.")
        return redirect('register_business')
