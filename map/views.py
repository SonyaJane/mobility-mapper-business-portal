from django.http import JsonResponse
from django.views.decorators.http import require_GET
# AJAX endpoint for business search
@require_GET
def ajax_search_businesses(request):
    term = request.GET.get('q', '').strip()
    cat_id = request.GET.get('category')
    access = request.GET.get('accessibility')
    from businesses.models import Business
    qs = Business.objects.all()
    if term:
        qs = qs.filter(business_name__icontains=term)
    if cat_id:
        qs = qs.filter(categories__id=cat_id)
    if access:
        qs = qs.filter(accessibility_features__name=access)
    results = []
    for biz in qs.distinct():
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
            'logo': biz.logo.url if biz.logo else '',
        })
    return JsonResponse({'businesses': results})
from django.shortcuts import render
from businesses.models import Business, Category

def route_finder(request):
    businesses = Business.objects.all()
    categories = Category.objects.all()
    from businesses.models import AccessibilityFeature
    accessibility_features = AccessibilityFeature.objects.all()
    business_list = []
    for biz in businesses:
        business_list.append({
            'id': biz.id,
            'business_name': biz.business_name,
            'address': biz.address,
            'location': {'lat': biz.location.y, 'lng': biz.location.x} if biz.location else None,
            'categories': list(biz.categories.values_list('id', flat=True)),
        })
    return render(request, 'map/route_finder.html', {
        'categories': categories,
        'accessibility_features': accessibility_features,
        'routeFinderBusinesses': business_list,
    })
