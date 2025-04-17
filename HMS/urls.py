
from django.contrib import admin
from django.urls import path, include
from room.views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls,name='admin'),
    path('account/', include('accountss.urls')),
    path('admins/', include('admins.urls')),
    path('social/', include('social_media.urls') ),
    path('', home, name='home'),
    path('room/', include('room.urls')),
    path('restaurant/', restaurant, name='restaurant'),
    path('agreement/', agreement, name='agreement'),
    path('about', about, name='about'),
    path('contact', contact, name='contact'),
    path('accounts/', include('allauth.urls')),
    path('social/', include('social_django.urls', namespace='social')),
    path('gym/', include('gym.urls')),
    path('', include('paypal.standard.ipn.urls')),
    path('hall/', include('Hall.urls')),
    path('spa/', include('Spa.urls')),
    
    
]


# your existing URL patterns...

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)