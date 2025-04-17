from django.contrib import admin
from .models import SpaService, SpaPackage, SpaBooking, SpaPayment

# Register your models here.
admin.site.register(SpaService) 
admin.site.register(SpaPackage)
admin.site.register(SpaBooking)
admin.site.register(SpaPayment)