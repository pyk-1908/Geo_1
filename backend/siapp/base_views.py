from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect


@csrf_protect
def uploaddb_view(request):
    return render(request, "uploaddb.html")


@csrf_protect
def uploadspendcube_view(request):
    return render(request, "uploadspendcube.html")
