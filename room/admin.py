from django.contrib import admin
from .models import Room, Booking, Payment, RoomRating,Category

admin.site.register(Room)
admin.site.register(Booking)
admin.site.register(Payment)
admin.site.register(RoomRating)
admin.site.register(Category)