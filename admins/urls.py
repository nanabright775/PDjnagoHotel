from django.urls import path
from .views import *

app_name = 'admins'

urlpatterns = [
    path('admin_dashboard/', admin_dashboard, name='admin_dashboard'),
    path('customers/', CustomerListView.as_view(), name='customer_list'),
    path('customers/delete/<int:pk>/', CustomerDeleteView.as_view(), name='customer_delete'),
    path('customer/<int:pk>/', CustomerDetailView.as_view(), name='customer_detail'),
    
    
    path('managers/', ManagerListView.as_view(), name='manager_list'),
    path('managers/create/', ManagerCreateView.as_view(), name='manager_create'),
    path('manager/<int:pk>/', ManagerDetailView.as_view(), name='manager_detail'),
    path('managers/update/<int:pk>/', ManagerUpdateView.as_view(), name='manager_update'),
    path('managers/delete/<int:pk>/', ManagerDeleteView.as_view(), name='manager_delete'),

    path('receptionists/', ReceptionistListView.as_view(), name='receptionist_list'),
    path('receptionists/create/', ReceptionistCreateView.as_view(), name='receptionist_create'),
    path('receptionist/<int:pk>/', ReceptionistDetailView.as_view(), name='receptionist_detail'),
    path('receptionists/update/<int:pk>/', ReceptionistUpdateView.as_view(), name='receptionist_update'),
    path('receptionists/delete/<int:pk>/', ReceptionistDeleteView.as_view(), name='receptionist_delete'),

    # Category URLs
    path('categories/', CategoryListView.as_view(), name='category_list'),
    path('categories/<int:pk>/', CategoryDetailView.as_view(), name='category_detail'),
    path('categories/add/', CategoryCreateView.as_view(), name='category_add'),
    path('categories/<int:pk>/update/', CategoryUpdateView.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', CategoryDeleteView.as_view(), name='category_delete'),

    # Room URLs
    path('rooms/', RoomListView.as_view(), name='room_list'),
    path('rooms/<int:pk>/', RoomDetailView.as_view(), name='room_detail'),
    path('rooms/add/', RoomCreateView.as_view(), name='room_add'),
    path('rooms/<int:pk>/update/', RoomUpdateView.as_view(), name='room_update'),
    path('rooms/<int:pk>/delete/', RoomDeleteView.as_view(), name='room_delete'),

    # Booking URLs
    path('bookings/', BookingListView.as_view(), name='booking_list'),
    path('bookings/<int:pk>/', BookingDetailView.as_view(), name='booking_detail'),
    path('bookings/add/', BookingCreateView.as_view(), name='booking_create'),
    path('bookings/<int:pk>/update/', BookingUpdateView.as_view(), name='booking_update'),
    path('booking/<int:pk>/extend/', BookingExtendView.as_view(), name='booking_extend'),
    path('booking/<int:pk>/download_id_image/', DownloadIDImageView.as_view(), name='download_id_image'),
    path('verify/<int:booking_id>/', BookingVerifyView.as_view(), name='booking_verify'),
    
    
    # Payment URLs
    path('payments/', PaymentListView.as_view(), name='payment_list'),
    path('payment/create/<int:booking_id>/', PaymentCreateView.as_view(), name='payment_create'),
    path('payment/<int:booking_id>/extend/<int:pk>/update/', PaymentExtendView.as_view(), name='payment_extend_update'),
    path('payments/<int:pk>/', PaymentDetailView.as_view(), name='payment_detail'),
    path('payments/<int:pk>/delete/', PaymentDeleteView.as_view(), name='payment_delete'),
    path('payment/<int:pk>/download/', PaymentDownloadReceiptView.as_view(), name='payment_download_receipt'),
     
    path('room-reports/', RoomReportView.as_view(), name='room_reports'),
    path('export-room-report/<str:report_type>/', ExportRoomReportView.as_view(), name='export_room_report'),
    path('room/<int:pk>/ratings/', RoomRatingListView.as_view(), name='room_ratings')
]


    

