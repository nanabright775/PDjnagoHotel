from django.urls import path
from .views import *

app_name = 'spa'

urlpatterns = [
    path('', ServiceListView.as_view(), name='service_list'),
    path('booking/create/', SpaBookingCreateView.as_view(), name='create_booking'),
    path('bookings/', BookingListView.as_view(), name='booking_list'),
    path('booking/cancel/<int:booking_id>/', CancelBookingView.as_view(), name='cancel_booking'),
    path('book/<str:item_type>/<int:item_id>/', SpaBookingCreateView.as_view(), name='spa_booking_create'),
    path('paypal-return/', SpaPayPalReturnView.as_view(), name='spa_paypal_return'),
    path('paypal-cancel/', SpaPayPalCancelView.as_view(), name='spa_paypal_cancel'),
]

