import requests
from django.http import HttpResponse
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ContactForm
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail


@login_required
def proxy_os_tile(request, z, x, y):
    # Limit the maximum zoom level to 20
    max_zoom = 20
    if z > max_zoom:
        z = min(int(z), max_zoom)

    api_key = settings.OS_MAPS_API_KEY    
    tile_url = f"https://api.os.uk/maps/raster/v1/zxy/Road_3857/{z}/{x}/{y}.png?key={api_key}"

    response = requests.get(tile_url)

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


def contact(request):
    initial = {}
    if request.user.is_authenticated:
        initial['name'] = request.user.get_full_name() or request.user.username
        initial['email'] = request.user.email
    if request.method == "POST":
        form = ContactForm(request.POST, initial=initial)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            message = form.cleaned_data['message']
            subject = f"Contact Form Submission from {name}"
            full_message = f"From: {name} <{email}>\n\n{message}"
            send_mail(
                subject,
                full_message,
                settings.DEFAULT_FROM_EMAIL,
                [settings.DEFAULT_FROM_EMAIL],
                fail_silently=False,
            )
            messages.success(request, "Your message has been sent!")
            return redirect("contact")
    else:
        form = ContactForm(initial=initial)
    return render(request, "core/contact.html", {"form": form, "page_title": "Contact Us"})
