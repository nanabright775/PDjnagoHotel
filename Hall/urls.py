# urls.py

from django.urls import path
from .views import *

urlpatterns = [
    path('', HallListView.as_view(), name='hall_list'),
    path('hall/<int:pk>/', HallDetailView.as_view(), name='hall_detail'),
    path('my-bookings/', BookingListView.as_view(), name='hall_bookings'),
    path('halls/<int:pk>/check-availability/', CheckAvailabilityView.as_view(), name='check_availability'),
    path('halls/<int:pk>/book/', BookingView.as_view(), name='book_hall'),
    path('paypal-return/', PayPalReturnView.as_view(), name='paypal_return'),
    path('paypal-cancel/', PayPalCancelView.as_view(), name='paypal_cancel'),
    path('payment/<int:pk>/', PaymentView.as_view(), name='payment_page'),
    path('hall/bookings/<int:pk>/cancel/', HallBookingCancelView.as_view(), name='hall_booking_cancel'),
]

