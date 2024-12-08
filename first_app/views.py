from django.shortcuts import render
from django.http import JsonResponse,HttpResponseBadRequest
import json

def page(request):
    context = {

    }
    return render(request, "page.html", context)