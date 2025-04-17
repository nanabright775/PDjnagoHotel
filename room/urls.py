from django.urls import path
from .views import *

urlpatterns = [
    path('', RoomListView.as_view(), name='rooms'),
    path('<int:pk>/', RoomDetailView.as_view(), name='room_detail'),
    path('my-bookings/', BookingListView.as_view(), name='bookings'),
    path('<int:room_id>/book/', BookingCreateView.as_view(), name='booking_create'),
    # path('booking/<int:booking_id>/pay/', PaymentView.as_view(), name='payment_create'),
    path('booking/extend/<int:booking_id>/', BookingExtendView.as_view(), name='booking_extend'),
    # path('payment/extend/<int:booking_id>/', PaymentExtendView.as_view(), name='payment_extend'),
    path('booking/<int:pk>/cancel/', BookingCancelView.as_view(), name='booking_cancel'),
    path('chapa-webhook/', ChapaWebhookView.as_view(), name='chapa_webhook'),
    path('booking/<int:booking_id>/upload_receipt/', ReceiptUploadView.as_view(), name='upload_receipt'),
    path('paypal-return/', PayPalReturnView.as_view(), name='paypal_return'),
    path('paypal-cancel/', PayPalCancelView.as_view(), name='paypal_cancel'),
    path('rating/<int:pk>/ratings/', RoomRatingListView.as_view(), name='room_ratings'),
    path('rating/<int:pk>/add_rating/', AddRoomRatingView.as_view(), name='add_room_rating'),
    path('rating/edit/<int:rating_id>/', EditRoomRatingView.as_view(), name='edit_room_rating'),
    path('rating/delete/<int:rating_id>/', DeleteRoomRatingView.as_view(), name='delete_room_rating'),
    path('my-ratings/', UserRoomRatingsListView.as_view(), name='my_room_ratings'),
    path('rating/test/ratings/<int:pk>/', test_view, name='test_view'),

]
