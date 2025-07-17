from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from businesses.models import Business

@login_required
def dashboard_view(request):
    user = request.user
    business = getattr(user.userprofile, 'business', None)
    context = {
            'business': business
        }
    return render(request, 'accounts/dashboard.html', context)
   