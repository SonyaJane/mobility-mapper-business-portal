import requests
from django.http import HttpResponse
from django.conf import settings

def proxy_os_tile(request, z, x, y):
    print(f"Tile request: z={z}, x={x}, y={y}")    
    # Limit the maximum zoom level to 20
    max_zoom = 20
    if z > max_zoom:
        z = min(int(z), max_zoom)
        
    api_key = settings.OS_MAPS_API_KEY    
    tile_url = f"https://api.os.uk/maps/raster/v1/zxy/Road_3857/{z}/{x}/{y}.png?key={api_key}"
    
    response = requests.get(tile_url)

    print(f"Tile response status: {response.status_code}")

    if response.status_code == 200:
        # Return the image content with appropriate content-type
        return HttpResponse(response.content, content_type="image/png")

    # Return a 404 response with caching headers
    return HttpResponse(
        status=404,
        headers={
            "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
        }
    )
