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
    
    path('membershipplans/', MembershipPlanListView.as_view(), name='membershipplan_list'),
    path('membershipplans/<int:pk>/', MembershipPlanDetailView.as_view(), name='membershipplan_detail'),
    path('membershipplans/create/', MembershipPlanCreateView.as_view(), name='membershipplan_create'),
    path('membershipplans/<int:pk>/update/', MembershipPlanUpdateView.as_view(), name='membershipplan_update'),
    path('membershipplans/<int:pk>/delete/', MembershipPlanDeleteView.as_view(), name='membershipplan_delete'),

    # Membership URLs
    path('memberships/create/', MembershipCreateView.as_view(), name='membership_create'),
    path('memberships/', MembershipListView.as_view(), name='membership_list'),
    path('memberships/<int:pk>/', MembershipDetailView.as_view(), name='membership_detail'),
    path('memberships/<int:pk>/update/', MembershipUpdateView.as_view(), name='membership_update'),
    path('verify_membership/<int:membership_id>/', MembershipVerifyView.as_view(), name='booking_verify'),
    # MembershipPayment URLs
    path('membershippayments/', MembershipPaymentListView.as_view(), name='membershippayment_list'),
    path('membershippayments/<int:pk>/', MembershipPaymentDetailView.as_view(), name='membershippayment_detail'),
    path('membershippayments/<int:pk>/delete/', MembershipPaymentDeleteView.as_view(), name='membershippayment_delete'),
    path('membership/payment/<int:pk>/download/', MembershipPaymentDownloadReceiptView.as_view(), name='membershippayment_download_receipt'),
    
    
    
    
    # Hall URLs
    path('hall/create/', HallCreateView.as_view(), name='hall_create'),
    path('hall/<int:pk>/update/', HallUpdateView.as_view(), name='hall_update'),
    path('hall/<int:pk>/delete/', HallDeleteView.as_view(), name='hall_delete'),
    path('hall/<int:pk>/', HallDetailView.as_view(), name='hall_detail'),
    path('hall/', HallListView.as_view(), name='hall_list'),
    
    # Hall Booking URLs
    path('hall/availability/', HallAvailabilityView.as_view(), name='hall_availability'),
    path('hall/booking-create/<int:pk>/', HallBookingCreateView.as_view(), name='hall_booking_create'),
    path('hall_booking/<int:pk>/update/', HallBookingUpdateView.as_view(), name='hall_booking_update'),
    path('hall_booking/', HallBookingListView.as_view(), name='hall_booking_list'),
    path('hall_booking/<int:pk>/', HallBookingDetailView.as_view(), name='hall_booking_detail'),
    path('hall_booking/<int:pk>/download_id_image/', HallDownloadIDImageView.as_view(), name='hall_download_id_image'),
    path('verify_hall_booking/<int:booking_id>/', HallBookingVerifyView.as_view(), name='booking_verify'),
    # Hall Payment URLs
    path('hall_payment/<int:pk>/delete/', HallPaymentDeleteView.as_view(), name='hall_payment_delete'),
    path('hall_payment/', HallPaymentListView.as_view(), name='hall_payment_list'),
    path('hall-payment/<int:pk>/', HallPaymentDetailView.as_view(), name='hall_payment_detail'),
    path('hall/payment/<int:pk>/', HallPaymentCreateView.as_view(), name='hall_payment_create'),
    path('hall/payment/<int:pk>/download/', HallPaymentDownloadReceiptView.as_view(), name='hall_payment_download_receipt'),
    
    # SpaService URLs
    path('spa-services/', SpaServiceListView.as_view(), name='spa_service_list'),
    path('spa-services/<int:pk>/', SpaServiceDetailView.as_view(), name='spa_service_detail'),
    path('spa-services/create/', SpaServiceCreateView.as_view(), name='spa_service_create'),
    path('spa-services/<int:pk>/update/', SpaServiceUpdateView.as_view(), name='spa_service_update'),
    path('spa-services/<int:pk>/delete/', SpaServiceDeleteView.as_view(), name='spa_service_delete'),

    # SpaPackage URLs
    path('spa-packages/', SpaPackageListView.as_view(), name='spa_package_list'),
    path('spa-packages/<int:pk>/', SpaPackageDetailView.as_view(), name='spa_package_detail'),
    path('spa-packages/create/', SpaPackageCreateView.as_view(), name='spa_package_create'),
    path('spa-packages/<int:pk>/update/', SpaPackageUpdateView.as_view(), name='spa_package_update'),
    path('spa-packages/<int:pk>/delete/', SpaPackageDeleteView.as_view(), name='spa_package_delete'),
    path('verify_spa_booking/<int:spa_booking_id>/', SpaBookingVerifyView.as_view(), name='booking_verify'),
    
    # SpaBooking URLs
    # urls.py
    path('spa-booking/create/', SpaBookingCreateView.as_view(), name='spa_booking_create'),
    path('spa-bookings/', SpaBookingListView.as_view(), name='spa_booking_list'),
    path('spa-bookings/<int:pk>/', SpaBookingDetailView.as_view(), name='spa_booking_detail'),
    path('spa-bookings/<int:pk>/update/',SpaBookingUpdateView.as_view(), name='spa_booking_update'),
    # SpaPayment URLs
    path('spa-payments/', SpaPaymentListView.as_view(), name='spa_payment_list'),
    path('spa-payments/<int:pk>/', SpaPaymentDetailView.as_view(), name='spa_payment_detail'),
    path('spa-payments/<int:pk>/delete/', SpaPaymentDeleteView.as_view(), name='spa_payment_delete'),
    path('spa/payment/<int:pk>/download/', SpaPaymentDownloadReceiptView.as_view(), name='spa_payment_download_receipt'),
    # SocialMediaPost URLs
    path('social_media_posts/', SocialMediaPostListView.as_view(), name='social_media_post_list'),
    path('social_media_posts/<int:pk>/', SocialMediaPostDetailView.as_view(), name='social_media_post_detail'),
    path('social_media_posts/add/', SocialMediaPostCreateView.as_view(), name='social_media_post_add'),
    path('social_media_posts/<int:pk>/update/', SocialMediaPostUpdateView.as_view(), name='social_media_post_update'),
    path('social_media_posts/<int:pk>/delete/', SocialMediaPostDeleteView.as_view(), name='social_media_post_delete'),

    # ChatMessage URLs
    path('chat_messages/', ChatMessageListView.as_view(), name='chat_message_list'),
    path('chat_messages/<int:pk>/', ChatMessageDetailView.as_view(), name='chat_message_detail'),
    path('chat_messages/add/', ChatMessageCreateView.as_view(), name='chat_message_add'),
    path('chat_messages/<int:pk>/update/', ChatMessageUpdateView.as_view(), name='chat_message_update'),
    # path('chat_messages/<int:pk>/delete/', ChatMessageDeleteView.as_view(), name='chat_message_delete'),
    
    path('chats/', ChatListView.as_view(), name='chat_list'),
    path('chats/<int:user_id>/', ChatDetailView.as_view(), name='chat_detail'),
    path('chats/<int:user_id>/send/', SendMessageView.as_view(), name='send_message'),
    # path('fetch_new_messages/<int:user_id>/', fetch_new_messages, name='fetch_new_messages'),
    path('spa-report/', SpaReportView.as_view(), name='spa_reports'),
    path('export-spa-report/<str:report_type>/', ExportSpaReportView.as_view(), name='export_spa_report'),
    path('room-reports/', RoomReportView.as_view(), name='room_reports'),
    path('export-room-report/<str:report_type>/', ExportRoomReportView.as_view(), name='export_room_report'),
    path('hall/reports/', HallReportView.as_view(), name='hall_reports'),
    path('hall/reports/export/<str:report_type>/', ExportHallReportView.as_view(), name='export_hall_report'),
    path('membership_reports/', MembershipReportView.as_view(), name='membership_reports'),
    path('export_membership_report/<str:report_type>/', ExportMembershipReportView.as_view(), name='export_membership_report'),
    path('room/<int:pk>/ratings/', RoomRatingListView.as_view(), name='room_ratings')
]


    

