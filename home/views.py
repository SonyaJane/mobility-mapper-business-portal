from django.shortcuts import render


def index(request):
    """ Returns the index page """
    return render(request, 'home/index.html', {'page_title': 'Home'})
