from django.shortcuts import render

def checkout(request, business_id):
    return render(request, 'checkout/checkout.html', {'business_id': business_id})

def payment_success(request):
    return render(request, 'checkout/payment_success.html')

def payment_failed(request):
    return render(request, 'checkout/payment_failed.html')
