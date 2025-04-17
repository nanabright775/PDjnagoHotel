# myapp/middleware.py

from django.utils.cache import add_never_cache_headers
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse



class NoCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        add_never_cache_headers(response)
        return response
