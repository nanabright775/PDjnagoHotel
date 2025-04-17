from django.contrib import admin
from .models import Hall, Hall_Booking, Hall_Category

# Register your models here.
admin.site.register(Hall)
admin.site.register(Hall_Booking)
admin.site.register(Hall_Category)

