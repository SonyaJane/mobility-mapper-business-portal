from django.shortcuts import render
# Test view to demonstrate toast messages
from django.contrib import messages
from django.shortcuts import redirect

def index(request):
    """ Returns the index page """
    return render(request, 'home/index.html')

def test_toasts(request):
    messages.info(request, "Informational message.")
    messages.success(request, "Success message!")
    messages.warning(request, "Warning message.")
    messages.error(request, "Error message.")
    return redirect('home')  # Or any existing view name