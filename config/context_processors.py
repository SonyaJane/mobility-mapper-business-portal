from django.conf import settings

def os_api_key(request):
    return {
        'OS_MAPS_API_KEY': settings.OS_MAPS_API_KEY
    }
