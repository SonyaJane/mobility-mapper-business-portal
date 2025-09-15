import re
from datetime import timedelta
from decimal import Decimal
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import mail_admins
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_GET
from django import template
from django.contrib import messages

from .forms import WheelerVerificationForm
from .models import WheelerVerification, WheelerVerificationApplication, WheelerVerificationPhoto
from accounts.models import MobilityDevice
from businesses.models import Business, AccessibilityFeature
from businesses.models import Business, MembershipTier
from checkout.models import Purchase

# custom template filter for dictionary access
register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Template filter: safely retrieve dictionary value by key.
    Returns None if dictionary is falsy or key missing.
    """
    if not dictionary:
        return None
    return dictionary.get(key)


@login_required    
@require_GET
def business_detail(request, pk):
    """
    Display a public-facing, verification-aware business detail page.

    Includes:
      - Opening hours parsed from JSON (if present)
      - Basic geo JSON payload for client-side map
      - Flags indicating whether the authenticated wheeler user
        (if any) has a pending or approved verification application

    Parameters:
        request (HttpRequest): Authenticated request (login required).
        pk (int): Business primary key.

    Returns:
        HttpResponse: Rendered business detail template.
    """
    business = get_object_or_404(Business, pk=pk, is_approved=True)
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
    user_has_requested = False
    user_request_approved = False
    profile = getattr(request.user, 'profile', None)
    if request.user.is_authenticated and profile and profile.is_wheeler:
        user_has_requested = WheelerVerificationApplication.objects.filter(
            business=business,
            wheeler=request.user,
            approved=False
        ).exists()
        user_request_approved = WheelerVerificationApplication.objects.filter(
            business=business,
            wheeler=request.user,
            approved=True
        ).exists()
    return render(request, 'verification/business_detail.html', {
        'business': business,
        'opening_hours': opening_hours,
        'page_title': business.business_name,
        'business_json': business_json,
        'user_has_requested': user_has_requested,
        'user_request_approved': user_request_approved,
    })


@login_required
def request_wheeler_verification(request, pk):
    """
    Allow a business owner to request Wheeler accessibility verification for their business.

    Workflow:
      - GET: Render confirmation/request screen.
      - POST: Determine verification price based on membership tier.
              If price is zero, flag business directly; otherwise redirect to checkout.

    Parameters:
        request (HttpRequest): Authenticated request.
        pk (int): Business primary key (must belong to current user).

    Returns:
        HttpResponse: Rendered request page (GET) or redirect to dashboard/checkout (POST).
    """
    business = get_object_or_404(Business, pk=pk, business_owner=getattr(request.user, 'profile', None))
    if request.method == 'POST':
        tier = business.membership_tier
        price = Decimal('0')
        if tier:
            # Prefer an explicit verification_price; otherwise fall back to membership price
            price = tier.verification_price if tier.verification_price is not None else (tier.membership_price if getattr(tier, 'membership_price', None) is not None else Decimal('0'))

        # If price is zero, short-circuit: mark verification requested on the Business and skip checkout
        try:
            price_decimal = Decimal(price)
        except Exception:
            price_decimal = Decimal('0')
        if price_decimal == Decimal('0'):
            business.wheeler_verification_requested = True
            business.save()
            messages.success(request, 'Verification requested — no payment required for your current plan.')
            return redirect('business_dashboard')
        url = reverse('checkout', args=[business.id])
        return redirect(f"{url}?{urlencode({'purchase_type': 'verification'})}")
    return render(request, 'verification/request_wheeler_verification.html', {
        'business': business,
        'page_title': 'Request Wheeler Verification'
    })


@login_required
def accessibility_verification_hub(request):
    """
    Display the Wheeler's verification hub listing their verification applications.

    Provides mappings:
      - verification_status: whether a verification has been submitted for each application
      - verification_approved: approval status if submitted
      - verification_id_map: link to the verification record id (or None)

    Access:
      - Wheeler profiles or superusers only.

    Returns:
        HttpResponse: Rendered hub template or redirect with error.
    """
    profile = getattr(request.user, 'profile', None)
    is_superuser = request.user.is_superuser
    if not profile or (not profile.is_wheeler and not is_superuser):
        messages.error(request, "Only verified Wheelers can view their accessibility verification hub.")
        return redirect('home')
    requests = WheelerVerificationApplication.objects.filter(wheeler=request.user).order_by('-requested_at')
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
    return render(request, 'verification/accessibility_verification_hub.html', {
        'requests': requests,
        'verification_status': verification_status,
        'verification_approved': verification_approved,
        'verification_id_map': verification_id_map,
        'page_title': 'Accessibility Verification Hub',
    })


@login_required
def wheeler_verification_application(request, pk):
    """
    Allow a Wheeler to apply to verify an approved business.

    Validations:
      - Must be a Wheeler profile.
      - Must not have already verified the business.
      - Must not have duplicate pending applications.

    POST:
      - Create WheelerVerificationApplication and notify admins.

    Returns:
        HttpResponse: Form page (GET) or redirect after submission/duplicate detection.
    """
    business = get_object_or_404(Business, pk=pk, is_approved=True)
    profile = getattr(request.user, 'profile', None)
    if not request.user.is_authenticated or not profile or not profile.is_wheeler:
        messages.error(request, "Only verified Wheelers can request to verify a business.")
        return redirect('accessible_business_search')

    # Count current verifications
    verification_count = business.verifications.count()
    required_verifications = 3
    cost_per_verification = 20
    wheeler_share = 10

    # check if the wheeler has already verified this business
    if WheelerVerification.objects.filter(business=business, wheeler=request.user).exists():
        messages.info(request, "You have already verified this business.")
        return redirect('business_detail', pk=pk)
    if request.method == 'POST':
        exists_pending = WheelerVerificationApplication.objects.filter(
            business=business, wheeler=request.user, approved=False
        ).exists()
        if not exists_pending:
            WheelerVerificationApplication.objects.create(business=business, wheeler=request.user)
            mail_admins(
                subject="New Wheeler Verification Application",
                message=(f"A new application to verify the accessibility features has been submitted for "
                         f"{business.business_name} by {request.user.username}. Review in admin.")
            )
            messages.success(request, "Application submitted — we'll review it and contact you.")
            return redirect('application_submitted', pk=pk)
        messages.info(request, "You already have a pending verification request for this business.")
        return redirect('business_detail', pk=pk)
    return render(request, 'verification/wheeler_verification_application.html', {
        'business': business,
        'verification_count': verification_count,
        'required_verifications': required_verifications,
        'cost_per_verification': cost_per_verification,
        'wheeler_share': wheeler_share,
        'page_title': 'Wheeler Verification Application',
    })


@login_required
def application_submitted(request, pk):
    """
    Confirmation page for a Wheeler's submitted verification application.

    Ensures:
      - The user is a Wheeler.
      - The application is still pending for the given business.

    Returns:
        HttpResponse: Confirmation page or redirect if invalid.
    """
    business = get_object_or_404(Business, pk=pk, is_approved=True)
    profile = getattr(request.user, 'profile', None)
    if not request.user.is_authenticated or not profile or not profile.is_wheeler:
        messages.error(request, "Only verified Wheelers can view this page.")
        return redirect('accessible_business_search')
    has_pending = WheelerVerificationApplication.objects.filter(
        business=business, wheeler=request.user, approved=False
    ).exists()
    if not has_pending:
        messages.info(request, "You do not have a pending verification application for this business.")
        return redirect('business_detail', pk=pk)
    return render(request, 'verification/application_submitted.html', {
        'business': business,
        'page_title': 'Verification Request Submitted',
    })


@login_required
def wheeler_verification_form(request, pk):
    """
    Capture a Wheeler's full accessibility verification for a business.

    Features:
      - Prevents duplicate submissions.
      - Associates selected mobility device.
      - Persists confirmed and additional accessibility features.
      - Handles general and feature-specific photo uploads.
      - Marks business as verified if threshold (>=3) reached.

    Parameters:
        request (HttpRequest)
        pk (int): Business primary key.

    Returns:
        HttpResponse: Form page (GET/invalid POST) or redirect to account dashboard (success).
    """
    business = get_object_or_404(Business, pk=pk)
    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.is_wheeler:
        messages.error(request, "You must be a verified Wheeler to submit a verification.")
        return redirect('account_dashboard')
    if WheelerVerification.objects.filter(business=business, wheeler=request.user).exists():
        messages.info(request, "You have already verified this business.")
        return redirect('account_dashboard')
    devices = MobilityDevice.objects.all()
    if request.method == 'POST':
        form = WheelerVerificationForm(request.POST, request.FILES, business=business)
        if form.is_valid():
            verification = form.save(commit=False)
            verification.business = business
            verification.wheeler = request.user
            # Attach mobility device instance (not raw id string)
            mob_dev_id = request.POST.get('mobility_device')
            if mob_dev_id:
                try:
                    verification.mobility_device = MobilityDevice.objects.get(pk=mob_dev_id)
                except MobilityDevice.DoesNotExist:
                    verification.mobility_device = None
            else:
                verification.mobility_device = None
            if 'selfie' in request.FILES:
                verification.selfie = request.FILES['selfie']
            verification.save()
            confirmed = form.cleaned_data.get('confirmed_features') or []
            additional = form.cleaned_data.get('additional_features') or []
            verification.confirmed_features.set(confirmed)
            verification.additional_features.set(additional)
            # Feature-specific photos
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
            # General photos
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
            # Debug statement (optional)
            _ = [(p.id, p.feature_id, p.image.name) for p in verification.photos.all()]
            messages.success(request, "Thank you for verifying this business! Please check your email for confirmation.")
            return redirect('account_dashboard')
    else:
        form = WheelerVerificationForm(business=business)
    return render(request, 'verification/wheeler_verification_form.html', {
        'form': form,
        'business': business,
        'devices': devices,
        'page_title': 'Accessibility Verification Form',
    })


@login_required
def verification_report(request, verification_id):
    """
    Display a single WheelerVerification report with its photos and selected features.

    Access granted to:
      - Business owner of the related business
      - Wheeler who submitted the verification
      - Superusers

    Hides Wheeler identity when viewed by the business owner to preserve privacy.

    Parameters:
        request (HttpRequest)
        verification_id (int): Verification primary key.

    Returns:
        HttpResponse: Rendered report template or redirect if unauthorized.
    """
    verification = get_object_or_404(WheelerVerification, pk=verification_id)
    print(f"Verification ID: {verification.id}, Business: {verification.business.business_name}, Wheeler: {verification.wheeler.username}")
    # Allow business owner or the Wheeler who submitted to view the report
    is_owner = (verification.business.business_owner == getattr(request.user, 'profile', None))
    is_wheeler = (verification.wheeler == request.user)
    # Allow superusers to view any report
    is_superuser = request.user.is_superuser
    if not (is_owner or is_wheeler or is_superuser):
        messages.error(request, "You do not have permission to view this report.")
        return redirect('business_dashboard')

    # Hide wheeler name if business owner is viewing
    show_wheeler_name = not (hasattr(request.user, 'profile') and verification.business.business_owner == getattr(request.user, 'profile', None))
    feature_photos_list = []
    confirmed_features = verification.confirmed_features.all()
    additional_features = verification.additional_features.all()
    # combine confirmed and additional features for photo display
    all_features = confirmed_features.union(additional_features)
    for feature in all_features:
        photo = verification.photos.filter(feature=feature).first()
        if photo:
            try:
                url = photo.image.url
            except Exception:
                url = str(photo.image)
            feature_photos_list.append({'feature': feature, 'url': url})
    # Other photos without a feature
    other_photo_urls = []
    for photo in verification.photos.filter(feature__isnull=True):
        try:
            url = photo.image.url
        except Exception:
            url = str(photo.image)
        other_photo_urls.append(url)
    return render(request, 'verification/wheeler_verification_report.html', {
        'verification': verification,
        'confirmed_features': confirmed_features,
        'feature_photos_list': feature_photos_list,
        'other_photo_urls': other_photo_urls,
        'show_wheeler_name': show_wheeler_name,
        'page_title': 'Accessibility Verification Report',
    })


@login_required
def cancel_wheeler_verification_request(request, business_id):
    """
    Allow a Wheeler to cancel a pending (unapproved) verification application.

    Parameters:
        request (HttpRequest)
        business_id (int): Business primary key for which the request was made.

    Behavior:
        - If pending application exists: delete it and show success.
        - If not: show informational message.
        - Only processed for Wheeler profiles.

    Returns:
        HttpResponseRedirect: Redirect to account dashboard.
    """
    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.is_wheeler:
        messages.error(request, "Only verified Wheelers can cancel verification requests.")
        return redirect('account_dashboard')
    # Find and delete the pending request
    req = WheelerVerificationApplication.objects.filter(
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