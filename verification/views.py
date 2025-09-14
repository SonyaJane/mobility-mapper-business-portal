from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from urllib.parse import urlencode
from decimal import Decimal
from django.views.decorators.http import require_GET
from django import template
from django.contrib import messages
from businesses.models import Business, AccessibilityFeature
from .forms import WheelerVerificationForm
from businesses.models import Business, MembershipTier
from .models import WheelerVerification, WheelerVerificationApplication
from checkout.models import Purchase
from django.core.mail import mail_admins
# custom template filter for dictionary access
from accounts.models import MobilityDevice
register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@login_required    
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
    profile = getattr(request.user, 'profile', None)
    if request.user.is_authenticated and profile and profile.is_wheeler:
        from .models import WheelerVerificationApplication
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
    return render(request, 'businesses/business_detail.html', {
        'business': business,
        'opening_hours': opening_hours,
        'page_title': business.business_name,
        'business_json': business_json,
        'user_has_requested': user_has_requested,
        'user_request_approved': user_request_approved,
    })

 
@login_required
def request_wheeler_verification(request, pk):
    # Allow business owner to request Wheelers to verify their business
    business = get_object_or_404(Business, pk=pk, business_owner=getattr(request.user, 'profile', None))

    if request.method == 'POST':
    # Determine verification price from membership tier (tier.verification_price or tier.membership_price)
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
            # Inform the user and redirect back to dashboard
            messages.success(request, 'Verification requested — no payment required for your current plan.')
            return redirect('business_dashboard')

        # Otherwise, redirect to checkout to collect payment
        url = reverse('checkout', args=[business.id])
        return redirect(f"{url}?{urlencode({'purchase_type': 'verification'})}")

    return render(request,
                  'businesses/request_wheeler_verification.html',
                  {'business': business,
                   'page_title': 'Request Wheeler Verification'})


@login_required
def accessibility_verification_hub(request):
    profile = getattr(request.user, 'profile', None)
    is_superuser = request.user.is_superuser
    if not profile or (not profile.is_wheeler and not is_superuser):
        messages.error(request, "Only verified Wheelers can view their accessibility verification hub.")
        return redirect('home')

    requests = WheelerVerificationApplication.objects.filter(wheeler=request.user).order_by('-requested_at')
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
    return render(request, 'businesses/accessibility_verification_hub.html', {
        'requests': requests,
        'verification_status': verification_status,
        'verification_approved': verification_approved,
        'verification_id_map': verification_id_map,
        'page_title': 'Accessibility Verification Hub',
    })


@login_required
def wheeler_verification_application(request, pk):
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
        # check if the wheeler has already applied to verify this business
        if not WheelerVerificationApplication.objects.filter(business=business, wheeler=request.user, approved=False).exists():
            # create a new verification request
            WheelerVerificationApplication.objects.create(business=business, wheeler=request.user)
            mail_admins(
                subject="New Wheeler Verification Application",
                message=f"A new application to verify the accessibility features has been submitted for {business.business_name} by {request.user.username}. Review and approve in the admin panel.",
            )
            messages.success(request, "Application submitted — we'll review it and contact you.")
            # redirect after successful POST to avoid re-submission / silent reload
            return redirect('application_submitted', pk=pk)
        else:
            messages.info(request, "You already have a pending verification request for this business.")
            return redirect('business_detail', pk=pk)

    return render(request, 'businesses/wheeler_verification_application.html', {
        'business': business,
        'verification_count': verification_count,
        'required_verifications': required_verifications,
        'cost_per_verification': cost_per_verification,
        'wheeler_share': wheeler_share,
        'page_title': 'Wheeler Verification Application',
    })


@login_required
def application_submitted(request, pk):
    business = get_object_or_404(Business, pk=pk, is_approved=True)
    profile = getattr(request.user, 'profile', None)
    if not request.user.is_authenticated or not profile or not profile.is_wheeler:
        messages.error(request, "Only verified Wheelers can view this page.")
        return redirect('accessible_business_search')

    # Check if the user has a pending application for this business
    has_pending_application = WheelerVerificationApplication.objects.filter(business=business, wheeler=request.user, approved=False).exists()
    if not has_pending_application:
        messages.info(request, "You do not have a pending verification application for this business.")
        return redirect('business_detail', pk=pk)

    return render(request, 'businesses/application_submitted.html', {
        'business': business,
        'page_title': 'Verification Request Submitted',
    })
    
    
@login_required
def wheeler_verification_form(request, pk):
    business = get_object_or_404(Business, pk=pk)
    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.is_wheeler:
        messages.error(request, "You must be a verified Wheeler to submit a verification.")
        return redirect('account_dashboard')

    # Prevent double-verifying
    if WheelerVerification.objects.filter(business=business, wheeler=request.user).exists():
        messages.info(request, "You have already verified this business.")
        return redirect('account_dashboard')

    # Load mobility device options for template
    devices = MobilityDevice.objects.all()
    if request.method == 'POST':
        form = WheelerVerificationForm(request.POST, request.FILES, business=business)
        if form.is_valid():
            uploaded = request.FILES.getlist('photos')
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
        'devices': devices,
        'page_title': 'Accessibility Verification Form',
    })


@login_required
def verification_report(request, verification_id):
    verification = get_object_or_404(WheelerVerification, pk=verification_id)
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
        'page_title': 'Accessibility Verification Report',
    })
    
    
@login_required
def cancel_wheeler_verification_request(request, business_id):
    """Allow a wheeler to cancel their pending verification request for a business."""
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


    """Display current membership details."""
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