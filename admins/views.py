from decimal import Decimal
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView,TemplateView,View, DetailView,FormView, CreateView, UpdateView, DeleteView
from accountss.models import *
from room.models import *
from social_media.models import *
from .mixins import *
from django.shortcuts import render, redirect,get_object_or_404
from django import forms
from gym.models import *
from .forms import *
from Spa.models import *
import random
import string
from django.db.models import Count, Sum, Avg, F, ExpressionWrapper, fields
from django.db.models.functions import TruncMonth,TruncDay
from datetime import timedelta
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from premailer import transform
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.messages.views import SuccessMessageMixin
from django.template.loader import render_to_string
from datetime import datetime
import qrcode
import base64
from xhtml2pdf import pisa
from io import BytesIO
from django.shortcuts import render
from django.db.models import Count, Sum
from django.core.serializers.json import DjangoJSONEncoder
import json
from config import BASE_URL,TELEGRAM_BOT_TOKEN


def admin_dashboard(request):
    # Room Type Popularity
    room_type_popularity = list(Booking.objects.values('room__room_type__name').annotate(count=Count('id')))
    room_type_popularity_data = [{'name': item['room__room_type__name'], 'y': item['count']} for item in room_type_popularity]

    # Revenue by Room Type
    revenue_by_room_type = list(Booking.objects.filter(is_paid=True).values('room__room_type__name').annotate(total_revenue=Sum('total_amount')))
    revenue_by_room_type_data = [{'name': item['room__room_type__name'], 'y': float(item['total_revenue'])} for item in revenue_by_room_type]

    # Membership Plan Popularity
    membership_plan_popularity = list(Membership.objects.values('plan__name').annotate(count=Count('id')))
    membership_plan_popularity_data = [{'name': item['plan__name'], 'y': item['count']} for item in membership_plan_popularity]

    # Revenue by Membership Plan
    revenue_by_membership_plan = list(MembershipPayment.objects.filter(status='completed').values('membership__plan__name').annotate(total_revenue=Sum('amount')))
    revenue_by_membership_plan_data = [{'name': item['membership__plan__name'], 'y': float(item['total_revenue'])} for item in revenue_by_membership_plan]

    # Membership Status Distribution
    membership_status_distribution = list(Membership.objects.values('status').annotate(count=Count('id')))
    membership_status_distribution_data = [{'name': item['status'], 'y': item['count']} for item in membership_status_distribution]

    # Payment Method Usage
    payment_method_usage = list(MembershipPayment.objects.values('payment_method').annotate(count=Count('id')))
    payment_method_usage_data = [{'name': item['payment_method'], 'y': item['count']} for item in payment_method_usage]

    # Hall Category Popularity
    hall_category_popularity = list(Hall_Booking.objects.values('hall__hall_type__name').annotate(count=Count('id')))
    hall_category_popularity_data = [{'name': item['hall__hall_type__name'], 'y': item['count']} for item in hall_category_popularity]

    # Revenue by Hall Category
    revenue_by_hall_category = list(Hall_Booking.objects.filter(is_paid=True).values('hall__hall_type__name').annotate(total_revenue=Sum('amount_due')))
    revenue_by_hall_category_data = [{'name': item['hall__hall_type__name'], 'y': float(item['total_revenue'])} for item in revenue_by_hall_category]

    # Hall Booking Status Distribution
    hall_booking_status_distribution = list(Hall_Booking.objects.values('status').annotate(count=Count('id')))
    hall_booking_status_distribution_data = [{'name': item['status'], 'y': item['count']} for item in hall_booking_status_distribution]

    # Payment Method Usage for Halls
    hall_payment_method_usage = list(Hall_Payment.objects.values('payment_method').annotate(count=Count('id')))
    hall_payment_method_usage_data = [{'name': item['payment_method'], 'y': item['count']} for item in hall_payment_method_usage]

    # User Stats
    user_roles_distribution = list(Custom_user.objects.values('role').annotate(count=Count('id')))
    user_roles_distribution_data = [{'name': item['role'], 'y': item['count']} for item in user_roles_distribution]

    # User Activity Stats
    recent_users = list(Custom_user.objects.filter(last_login__isnull=False).order_by('-last_login')[:10].values('username', 'last_login'))
    recent_users_data = [{'name': item['username'], 'y': item['last_login'].timestamp() * 1000} for item in recent_users]

   # Monthly Revenue
    monthly_revenue = list(
        Booking.objects.filter(is_paid=True)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total_revenue=Sum('total_amount'))
        .order_by('month')
    )
    monthly_revenue_data = [{'name': item['month'].strftime('%B %Y'), 'y': float(item['total_revenue'])} for item in monthly_revenue]
    
    # Extract categories and data values separately
    monthly_revenue_categories = [item['month'].strftime('%B %Y') for item in monthly_revenue]
    monthly_revenue_values = [float(item['total_revenue']) for item in monthly_revenue]

    
    # Extract categories and data values separately
    monthly_revenue_categories = [item['month'].strftime('%B %Y') for item in monthly_revenue]
    monthly_revenue_values = [float(item['total_revenue']) for item in monthly_revenue]
    
   # Spa Service Popularity
    spa_service_popularity = list(
        SpaBooking.objects
        .filter(service__isnull=False)
        .values('service__name')
        .annotate(count=Count('id'))
    )
    spa_service_popularity_data = [{'name': item['service__name'], 'y': item['count']} for item in spa_service_popularity]

    # Revenue by Spa Service
    revenue_by_spa_service = list(
        SpaPayment.objects
        .filter(status='completed', spa_booking__service__isnull=False)
        .values('spa_booking__service__name')
        .annotate(total_revenue=Sum('amount'))
    )
    revenue_by_spa_service_data = [{'name': item['spa_booking__service__name'], 'y': float(item['total_revenue'])} for item in revenue_by_spa_service]

    # Spa Package Popularity
    spa_package_popularity = list(
        SpaBooking.objects
        .filter(package__isnull=False)
        .values('package__name')
        .annotate(count=Count('id'))
    )
    spa_package_popularity_data = [{'name': item['package__name'], 'y': item['count']} for item in spa_package_popularity]

    # Revenue by Spa Package
    revenue_by_spa_package = list(
        SpaPayment.objects
        .filter(status='completed', spa_booking__package__isnull=False)
        .values('spa_booking__package__name')
        .annotate(total_revenue=Sum('amount'))
    )
    revenue_by_spa_package_data = [{'name': item['spa_booking__package__name'], 'y': float(item['total_revenue'])} for item in revenue_by_spa_package]



    # User Registration Trends
    user_registration_trends = list(
        Custom_user.objects.annotate(month=TruncMonth('date_joined')).values('month').annotate(count=Count('id')).order_by('month')
    )
    user_registration_trends_data = [{'name': item['month'].strftime('%B %Y'), 'y': item['count']} for item in user_registration_trends]

    # Extract categories and data values separately
    user_registration_categories = [item['month'].strftime('%B %Y') for item in user_registration_trends]
    user_registration_values = [item['count'] for item in user_registration_trends]


    context = {
        'room_type_popularity_data': json.dumps(room_type_popularity_data, cls=DjangoJSONEncoder),
        'revenue_by_room_type_data': json.dumps(revenue_by_room_type_data, cls=DjangoJSONEncoder),
        'membership_plan_popularity_data': json.dumps(membership_plan_popularity_data, cls=DjangoJSONEncoder),
        'revenue_by_membership_plan_data': json.dumps(revenue_by_membership_plan_data, cls=DjangoJSONEncoder),
        'membership_status_distribution_data': json.dumps(membership_status_distribution_data, cls=DjangoJSONEncoder),
        'payment_method_usage_data': json.dumps(payment_method_usage_data, cls=DjangoJSONEncoder),
        'hall_category_popularity_data': json.dumps(hall_category_popularity_data, cls=DjangoJSONEncoder),
        'revenue_by_hall_category_data': json.dumps(revenue_by_hall_category_data, cls=DjangoJSONEncoder),
        'hall_booking_status_distribution_data': json.dumps(hall_booking_status_distribution_data, cls=DjangoJSONEncoder),
        'hall_payment_method_usage_data': json.dumps(hall_payment_method_usage_data, cls=DjangoJSONEncoder),
        'user_roles_distribution_data': json.dumps(user_roles_distribution_data, cls=DjangoJSONEncoder),
        'recent_users_data': json.dumps(recent_users_data, cls=DjangoJSONEncoder),
        'monthly_revenue_categories': json.dumps(monthly_revenue_categories),
        'monthly_revenue_values': json.dumps(monthly_revenue_values),
        'spa_service_popularity_data': json.dumps(spa_service_popularity_data, cls=DjangoJSONEncoder),
        'revenue_by_spa_service_data': json.dumps(revenue_by_spa_service_data, cls=DjangoJSONEncoder),
        'spa_package_popularity_data': json.dumps(spa_package_popularity_data, cls=DjangoJSONEncoder),
        'revenue_by_spa_package_data': json.dumps(revenue_by_spa_package_data, cls=DjangoJSONEncoder),
        'user_registration_categories': json.dumps(user_registration_categories),
        'user_registration_values': json.dumps(user_registration_values)
    }

    return render(request, 'admins/admin_dashboard.html', context)



    

class CustomerDetailView(OwnerRequiredMixin,DetailView):
    model = Custom_user
    template_name = 'admins/customer_detail.html'
    context_object_name = 'customer'

    def get_queryset(self):
        return Custom_user.objects.filter(role='customer')


# Detail view for Receptionist


class CustomerListView(OwnerRequiredMixin, ListView):
    model = Custom_user
    template_name = 'admins/customer_list.html'
    context_object_name = 'customers'
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get('search')
        if query:
            return Custom_user.objects.filter(role='customer', first_name__icontains=query)
        return Custom_user.objects.filter(role='customer').order_by('-id')


from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import DeleteView

class CustomerDeleteView(OwnerRequiredMixin, DeleteView):
    model = Custom_user
    template_name = 'admins/customer_list.html'
    success_url = reverse_lazy('admins:customer_list')

    def post(self, request, *args, **kwargs):
        customer = self.get_object()  # Get the customer object
        email = customer.email
        full_name = customer.get_full_name()
        print(full_name)
        print(email)
        
        # Call the delete method
        response = super().delete(request, *args, **kwargs)

        # Send deletion confirmation email
        subject = 'Account Deletion Confirmation - ADAR Hotel'
        from_email = 'adarhotel33@gmail.com'

        # Render email content from template
        html_content = render_to_string('admins/customer_deletion_email_template.html', {
            'full_name': full_name,
            'support_email': 'adarhotel33@gmail.com',  # You can set your support email here
        })

        # Create plain text content by stripping HTML tags
        text_content = strip_tags(html_content)

        # Create email
        email_message = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[email]
        )

        # Attach HTML content
        email_message.attach_alternative(html_content, "text/html")
        
        # Send the email
        email_message.send()
        
        # Add the success message
        messages.success(request, f"Customer {full_name} has been deleted successfully.")

        return response

    
        

# owner views for creating manager and receptionsits

class ManagerListView(OwnerRequiredMixin, ListView):
    model = Custom_user
    template_name = 'admins/manager_list.html'
    context_object_name = 'managers'
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get('search')
        if query:
            return Custom_user.objects.filter(role='manager', first_name__icontains=query)
        return Custom_user.objects.filter(role='manager').order_by('-id')


class ManagerDetailView(OwnerRequiredMixin,DetailView):
    model = Custom_user
    template_name = 'admins/manager_detail.html'
    context_object_name = 'manager'

    def get_queryset(self):
        return Custom_user.objects.filter(role='manager')

class ManagerUpdateView(OwnerRequiredMixin, UpdateView):
    model = Custom_user
    form_class = CustomUserChangeForm
    template_name = 'admins/manager_form.html'
    success_url = reverse_lazy('admins:manager_list')

class ManagerDeleteView(OwnerRequiredMixin, DeleteView):
    model = Custom_user
    template_name = 'admins/manager_list.html'
    success_url = reverse_lazy('admins:manager_list')
    def post(self, request, *args, **kwargs):
        manager = self.get_object()
        full_name = manager.get_full_name()
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f"Manager {full_name} has been deleted successfully.")

        return response
  
class ReceptionistListView(OwnerOrManagerRequiredMixin, ListView):
    model = Custom_user
    template_name = 'admins/receptionist_list.html'
    context_object_name = 'receptionists'
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get('search')
        if query:
            return Custom_user.objects.filter(role='receptionist', first_name__icontains=query)
        return Custom_user.objects.filter(role='receptionist').order_by('-id')


class ManagerCreateView(OwnerRequiredMixin, CreateView):
    model = Custom_user
    form_class = CustomUserCreationForm
    template_name = 'admins/manager_form.html'
    success_url = reverse_lazy('admins:manager_list')

    def form_valid(self, form):
        form.instance.role = 'manager'
        response = super().form_valid(form)

        # Email confirmation logic
        manager = form.instance
        emails = form.cleaned_data.get('email')
        password = form.cleaned_data.get('password1')  # Assuming this is the password field name
        print(password)


        
        # URL for login
        login_url = f"{BASE_URL}/login/"

        # Render email content from template
        html_content = render_to_string('admins/manager_account_creation_confirmation_email_template.html', {
            'manager': manager,
            'password': password,
            'login_url': login_url,
        })
        
        # Inline CSS
        html_content = transform(html_content)
        print(emails)
        # Create the email message
        email = EmailMultiAlternatives(
            subject='Manager Account Created - Please Change Your Password',
            from_email='adarhotel33@gmail.com',
            to=[emails]
        )
        
        # Attach the HTML content
        email.attach_alternative(html_content, "text/html")
        
        # Send the email
        email.send()

        return response


class ReceptionistUpdateView(OwnerOrManagerRequiredMixin, UpdateView):
    model = Custom_user
    form_class = CustomUserChangeForm
    template_name = 'admins/receptionist_form.html'
    success_url = reverse_lazy('admins:receptionist_list')

class ReceptionistDetailView(OwnerOrManagerRequiredMixin,DetailView):
    model = Custom_user
    template_name = 'admins/receptionist_detail.html'
    context_object_name = 'receptionist'

    def get_queryset(self):
        return Custom_user.objects.filter(role='receptionist')



class ReceptionistCreateView(OwnerOrManagerRequiredMixin, CreateView):
    model = Custom_user
    form_class = CustomUserCreationForm
    template_name = 'admins/receptionist_form.html'
    success_url = reverse_lazy('admins:receptionist_list')

    def form_valid(self, form):
        form.instance.role = 'receptionist'
        response = super().form_valid(form)

        # Email confirmation logic
        receptionist = form.instance
        password = form.cleaned_data.get('password1')  # Assuming this is the password field name
        receptionist_email = form.cleaned_data.get('email')  # Assuming this is the password field name
        # URL for login
        login_url = f"{BASE_URL}/login/"

        # Render email content from template
        html_content = render_to_string('admins/receptionist_account_creation_confirmation_email_template.html', {
            'receptionist': receptionist,
            'password': password,
            'login_url': login_url,
        })
        
        # Inline CSS
        html_content = transform(html_content)

        # Create the email message
        email = EmailMultiAlternatives(
            subject='Receptionist Account Created - Please Change Your Password',
            from_email='adarhotel33@gmail.com',
            to=[receptionist_email]
        )
        
        # Attach the HTML content
        email.attach_alternative(html_content, "text/html")
        
        # Send the email
        email.send()

        return response



class ReceptionistDeleteView(OwnerOrManagerRequiredMixin, DeleteView):
    model = Custom_user
    template_name = 'admins/receptionist_list.html'
    success_url = reverse_lazy('admins:receptionist_list')
    def post(self, request, *args, **kwargs):
        receptionist = self.get_object()
        full_name = receptionist.get_full_name()
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f"Receptionist {full_name} has been deleted successfully.")

        return response






# Category Views
class CategoryListView(OwnerManagerOrReceptionistRequiredMixin,ListView):
    model = Category
    template_name = 'admins/category_list.html'
    context_object_name = 'categories'
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get('search')
        if query:
            return Category.objects.filter(name__icontains=query)
        return Category.objects.order_by('name')

class CategoryDetailView(OwnerManagerOrReceptionistRequiredMixin, DetailView):
    model = Category
    template_name = 'admins/category_detail.html'



class CategoryCreateView(OwnerOrManagerRequiredMixin,  CreateView,SuccessMessageMixin):
    model = Category
    template_name = 'admins/category_form.html'
    form_class = CategoryForm
    success_url = reverse_lazy('admins:category_list')
    success_message = "Room category was created successfully."

    
class CategoryUpdateView(OwnerOrManagerRequiredMixin, UpdateView):
    model = Category
    template_name = 'admins/category_form.html'
    form_class = CategoryForm
    success_url = reverse_lazy('admins:category_list')
    success_message = "Room category was updated successfully."


class CategoryDeleteView(OwnerOrManagerRequiredMixin, DeleteView):
    model = Category
    template_name = 'admins/category_confirm_delete.html'
    success_url = reverse_lazy('admins:category_list')

# Room Views
class RoomListView(OwnerManagerOrReceptionistRequiredMixin, ListView):
    model = Room
    template_name = 'admins/room_list.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def get_queryset(self):
        queryset = Room.objects.all().order_by('id')
        
        # Annotate the queryset with the average rating
        queryset = queryset.annotate(average_rating=Avg('roomrating__rating'))
        
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(room_number__icontains=search_query) | 
                Q(room_type__name__icontains=search_query)
            )
        return queryset


class RoomDetailView(OwnerManagerOrReceptionistRequiredMixin, DetailView):
    model = Room
    template_name = 'admins/room_detail.html'

class RoomCreateView(OwnerOrManagerRequiredMixin, CreateView):
    model = Room
    template_name = 'admins/room_form.html'
    form_class = RoomForm
    success_url = reverse_lazy('admins:room_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Room created successfully.')
        return response

class RoomUpdateView(OwnerOrManagerRequiredMixin, UpdateView):
    model = Room
    template_name = 'admins/room_form.html'
    form_class = RoomForm
    success_url = reverse_lazy('admins:room_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Room updated successfully.')
        return response

class RoomDeleteView(OwnerOrManagerRequiredMixin,  DeleteView):
    model = Room
    template_name = 'admins/room_confirm_delete.html'
    success_url = reverse_lazy('admins:room_list')




# Booking Views
from django.views.generic import ListView
from django.db.models import Q
from room.models import Booking
from datetime import timedelta
from django.utils import timezone

class BookingListView(OwnerManagerOrReceptionistRequiredMixin, ListView):
    model = Booking
    template_name = 'admins/booking_list.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def get_queryset(self):
        queryset = Booking.objects.all().order_by('-created_at')

        # Get the current time and two days ago
        now = timezone.now()
        two_days_ago = now - timedelta(days=2)

        # Fetch bookings that have a past checkout date and are either pending or confirmed
        past_bookings = queryset.filter(check_out_date__lt=now, status__in=['pending', 'confirmed'])

        for booking in past_bookings:
            # Update booking status to 'cancelled'
            booking.status = 'cancelled'

            # Update room status and booking details
            booking.room.room_status = 'vacant'
            booking.checked_in = False
            booking.checked_out = True

            # Save the updates to room and booking
            booking.room.save()
            booking.save()

        # Automatically cancel bookings that are pending and created more than two days ago
        queryset.filter(created_at__lt=two_days_ago, status='pending').update(status='cancelled')

        # Reapply ordering by '-created_at'
        queryset = Booking.objects.all().order_by('-created_at')

        # Handle search functionality
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(room__room_number__icontains=search_query) |
                Q(room__room_type__name__icontains=search_query) |
                Q(full_name__icontains=search_query) |
                Q(tx_ref__icontains=search_query) |
                Q(status__icontains=search_query)
            )

        return queryset


class BookingVerifyView(View):
    def get(self, request, booking_id, *args, **kwargs):
        try:
            booking = Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            return render(request, 'admins/booking_not_found.html')
        
        return render(request, 'admins/booking_verify.html', {'booking': booking})
class BookingDetailView(OwnerManagerOrReceptionistRequiredMixin, DetailView):
    model = Booking
    template_name = 'admins/booking_detail.html'

class BookingCreateView(OwnerManagerOrReceptionistRequiredMixin, CreateView):
    model = Booking
    form_class = BookingCreateForm
    template_name = 'admins/booking_form.html'

    def form_valid(self, form):
        booking = form.save(commit=False)
        full_name = form.cleaned_data['full_name']
        booking.tx_ref = f"booking-{full_name.replace(' ', '')}-tx-{''.join(random.choices(string.ascii_lowercase + string.digits, k=10))}"
        booking.status = 'pending'
        
        if booking.check_in_date and booking.check_out_date:
            duration = (booking.check_out_date - booking.check_in_date).days
            booking.original_booking_amount = booking.room.price_per_night * duration
            booking.total_amount = booking.original_booking_amount
        booking.save()
        return redirect('admins:payment_create',booking_id=booking.id)



class BookingUpdateView(OwnerManagerOrReceptionistRequiredMixin, UpdateView):
    model = Booking
    template_name = 'admins/booking_update.html'
    form_class = BookingUpdateForm
    success_url = reverse_lazy('admins:booking_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        booking = form.instance
        return response

from django.http import HttpResponse, Http404

class DownloadIDImageView(View):
    def get(self, request, pk):
        try:
            booking = Booking.objects.get(pk=pk)
            if booking.id_image:
                response = HttpResponse(booking.id_image, content_type='image/jpeg')
                response['Content-Disposition'] = f'attachment; filename="{booking.id_image.name}"'
                return response
            else:
                raise Http404("No ID image available for this booking.")
        except Booking.DoesNotExist:
            raise Http404("Booking not found.")





from django.urls import reverse

class BookingExtendView(OwnerManagerOrReceptionistRequiredMixin, UpdateView):
    model = Booking
    form_class = BookingExtendForm
    template_name = 'admins/booking_extend_form.html'

    def form_valid(self, form):
        booking = form.save(commit=False)
        additional_amount = booking.calculate_additional_amount()
        booking.booking_extend_amount = additional_amount
        booking.total_amount += additional_amount
        booking.status = 'pending'
        
        # Save the booking first
        booking.save()
        
        # Create or update the Payment object
        payment, created = Payment.objects.get_or_create(
            booking=booking,
            
        )
        
        if not created:
            # If the payment already exists, update it
            payment.save()
        
        # Generate a new tx_ref for the payment
        full_name = booking.full_name
        booking.tx_ref = f"booking-{full_name.replace(' ', '')}-tx-{''.join(random.choices(string.ascii_lowercase + string.digits, k=10))}"
        booking.save()
        
        # Redirect to the payment extension view with booking and payment IDs
        return redirect(reverse('admins:payment_extend_update', kwargs={'booking_id': booking.id, 'pk': payment.id}))


# Room Payment Views


from django.utils.safestring import mark_safe

class PaymentExtendView(OwnerManagerOrReceptionistRequiredMixin, UpdateView):
    model = Payment
    form_class = PaymentExtendForm
    template_name = 'admins/payment_extend_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        booking_id = self.kwargs.get('booking_id')
        context['booking'] = get_object_or_404(Booking, pk=booking_id)
        return context

    def get_object(self):
        booking_id = self.kwargs.get('booking_id')
        payment_id = self.kwargs.get('pk')
        booking = get_object_or_404(Booking, pk=booking_id)
        return get_object_or_404(Payment, id=payment_id, booking=booking)

    def form_valid(self, form):
        payment = form.save(commit=False)
        booking_id = self.kwargs.get('booking_id')
        booking = get_object_or_404(Booking, pk=booking_id)
        payment.booking = booking
        payment.transaction_id = booking.tx_ref
        payment.payment_date = datetime.now()
        payment.status = 'completed'
        payment.save()
        booking.status = 'confirmed'
        booking.check_out_date = booking.extended_check_out_date
        booking.save()

        # Generate receipt PDF
        pdf_response = self.generate_pdf(booking)
        pdf_name = f"room_booking_extend_receipt_{booking.id}_{booking.full_name if booking.full_name else booking.user.username}.pdf"
        pdf_file = ContentFile(pdf_response) 
        payment.receipt_pdf.save(pdf_name, pdf_file)
        if booking.email2:
                    from_email = 'adarhotel33@gmail.com'
                    subject = 'Room Booking Extend Confirmation'
                    html_content = render_to_string('checkout_date_extenstion_email_template.html', {'booking': booking})
                    # Inline CSS
                    html_content = transform(html_content)

                    # Render email content from template
                    
                    user_email = booking.email2 
                    
                    # Create email
                    email_message = EmailMultiAlternatives(
                        subject=subject,
                        body=html_content,
                        from_email=from_email,
                        to=[user_email]
                    )

                    # Attach HTML content
                    email_message.attach_alternative(html_content, "text/html")
                    email_message.attach(f'receipt_{booking.id}_{booking.full_name}.pdf', pdf_response, 'application/pdf')
                    
                    # Send the email
                    email_message.send()

        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return HttpResponse(pdf_response, content_type='application/pdf')

        # Automatically download the PDF receipt
        response = HttpResponse(pdf_response, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="receipt_{booking.id}_{booking.full_name}.pdf"'

        messages.success(self.request, 'Booking and Payment for Extension completed')
        return response

    def generate_pdf(self, booking):
        buffer = BytesIO()
        
        # Generate QR code data
        qr_code_data = self.generate_qr_code(f'{BASE_URL}/admins/verify/{booking.id}')
        
        context = {
            'booking': booking,
            'qr_code_data': qr_code_data,
        }
        
        html_string = render_to_string('room/checkout_date_extenstion_email_template_receipt.html', context)
        
        pisa_status = pisa.CreatePDF(html_string, dest=buffer)
        buffer.seek(0)
        return buffer.read()

    def generate_qr_code(self, data):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return mark_safe(f'data:image/png;base64,{img_str}')

from django.db import IntegrityError, transaction
class PaymentCreateView(OwnerManagerOrReceptionistRequiredMixin, CreateView):
    model = Payment
    form_class = PaymentCreateForm
    template_name = 'admins/payment_form.html'
    success_url = reverse_lazy('admins:payment_list')

    def get_context_data(self, **kwargs):
        context = super(PaymentCreateView, self).get_context_data(**kwargs)
        booking_id = self.kwargs.get('booking_id')  
        context['booking'] = get_object_or_404(Booking, pk=booking_id)
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        booking_id = self.kwargs.get('booking_id')
        booking = get_object_or_404(Booking, pk=booking_id)
        kwargs.update({'initial': {'booking': booking}})
        return kwargs

    def form_valid(self, form):
        booking_id = self.kwargs.get('booking_id')
        booking = get_object_or_404(Booking, pk=booking_id)

        # Check if a payment already exists
        if Payment.objects.filter(booking=booking).exists():
            messages.error(self.request, 'Payment already exists for this booking.')
            return redirect('admins:payment_list')

        try:
            with transaction.atomic():
                payment = form.save(commit=False)
                payment.booking = booking
                payment.transaction_id = booking.tx_ref
                payment.payment_date = datetime.now()
                payment.status = 'completed'
                payment.save()

                booking.status = 'confirmed'
                booking.save()

                # Generate receipt PDF
                pdf_response = self.generate_pdf(booking)
                pdf_name = f"room_booking_receipt_{booking.id}_{booking.full_name if booking.full_name else booking.user.username}.pdf"
                pdf_file = ContentFile(pdf_response) 
                payment.receipt_pdf.save(pdf_name, pdf_file)
                if booking.email2:
                    from_email = 'adarhotel33@gmail.com'
                    subject = 'Room Booking Confirmation'
                    html_content = render_to_string('room/booking_confirmation_template.html', {'booking': booking})
                    # Inline CSS
                    html_content = transform(html_content)

                    # Render email content from template
                    
                    user_email = booking.email2 
                    
                    # Create email
                    email_message = EmailMultiAlternatives(
                        subject=subject,
                        body=html_content,
                        from_email=from_email,
                        to=[user_email]
                    )

                    # Attach HTML content
                    email_message.attach_alternative(html_content, "text/html")
                    email_message.attach(f'receipt_{booking.id}_{booking.full_name}.pdf', pdf_response, 'application/pdf')
                    
                    # Send the email
                    email_message.send()

                # Handle AJAX request for PDF download
                if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return HttpResponse(pdf_response, content_type='application/pdf')

                # Regular response (fallback)
                response = HttpResponse(pdf_response, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="receipt_{booking.id}_{booking.full_name}.pdf"'
                
            
                
                
                
                messages.success(self.request, 'Booking and Payment completed')
                return response

        except IntegrityError:
            messages.error(self.request, 'A payment for this booking already exists.')
            return redirect('admins:payment_list')


    def generate_pdf(self, booking):
        buffer = BytesIO()
        
        # Generate QR code data
        qr_code_data = self.generate_qr_code(f'{BASE_URL}/admins/verify/{booking.id}')
        
        context = {
            'booking': booking,
            'qr_code_data': qr_code_data,
        }
        
        
        html_string = render_to_string('room/booking_confirmation_template_receipt.html', context)
        
        pisa_status = pisa.CreatePDF(html_string, dest=buffer)
        buffer.seek(0)
        return buffer.read()

    def generate_qr_code(self, data):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return mark_safe(f'data:image/png;base64,{img_str}')



class PaymentListView(OwnerManagerOrReceptionistRequiredMixin, ListView):
    model = Payment
    template_name = 'admins/payment_list.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def get_queryset(self):
        queryset = Payment.objects.all().order_by('-payment_date')
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(booking__room__room_number__icontains=search_query) |
                Q(booking__room__room_type__name__icontains=search_query) |
                Q(booking__user__username__icontains=search_query) |
                Q(transaction_id__icontains=search_query)
            )
        return queryset



class PaymentDetailView(OwnerManagerOrReceptionistRequiredMixin, DetailView):
    model = Payment
    template_name = 'admins/payment_detail.html'


from django.http import HttpResponseRedirect
class PaymentDeleteView(OwnerOrManagerRequiredMixin, DeleteView):
    model = Payment
    template_name = 'admins/payment_confirm_delete.html'
    success_url = reverse_lazy('admins:payment_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        booking = self.object.booking  # Get the associated booking instance

        if booking:
            print(f"Booking found: {booking.id}")  # Debug statement
        else:
            print("No associated booking found.")  # Debug statement
        
        success_url = self.get_success_url()

        # Explicitly delete the associated booking first, then the payment
        if booking:
            booking.delete()
        
        self.object.delete()

        return HttpResponseRedirect(success_url)


class PaymentDownloadReceiptView(View):
    def get(self, request, pk, *args, **kwargs):
        payment = get_object_or_404(Payment, pk=pk)

        # Serve the file for download
        response = HttpResponse(payment.receipt_pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{payment.receipt_pdf.name}"'
        return response





# MembershipPlan Views
class MembershipPlanListView(OwnerManagerOrReceptionistRequiredMixin,ListView):
    model = MembershipPlan
    template_name = 'admins/membershipplan_list.html'
    context_object_name = 'membershipplans'
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get('search')
        if query:
            return MembershipPlan.objects.filter(name__icontains=query)
        return MembershipPlan.objects.order_by('name')

class MembershipPlanDetailView(OwnerManagerOrReceptionistRequiredMixin, DetailView):
    model = MembershipPlan
    template_name = 'admins/membershipplan_detail.html'

class MembershipPlanCreateView(OwnerOrManagerRequiredMixin,  CreateView):
    model = MembershipPlan
    template_name = 'admins/membershipplan_form.html'
    form_class = MembershipPlanForm
    success_url = reverse_lazy('admins:membershipplan_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Membership Plan created successfully.')
        return response

class MembershipPlanUpdateView(OwnerOrManagerRequiredMixin,  UpdateView):
    model = MembershipPlan
    template_name = 'admins/membershipplan_form.html'
    form_class = MembershipPlanForm
    success_url = reverse_lazy('admins:membershipplan_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Membership Plan updated successfully.')
        return response

class MembershipPlanDeleteView(OwnerOrManagerRequiredMixin,  DeleteView):
    model = MembershipPlan
    template_name = 'admins/membershipplan_confirm_delete.html'
    success_url = reverse_lazy('admins:membershipplan_list')

# Membership Views

class MembershipListView(OwnerManagerOrReceptionistRequiredMixin, ListView):
    model = Membership
    template_name = 'admins/membership_list.html'
    context_object_name = 'memberships'
    paginate_by = 10

    def get_queryset(self):
        queryset = Membership.objects.all().order_by('-id')

        # Get the current time and two days ago
        now = timezone.now()
        two_days_ago = now - timedelta(days=2)

        # Automatically update the status of memberships with a past end_date to 'Cancelled'
        queryset.filter(
            end_date__lt=now,
            status__in=['active', 'pending']  # Assuming these are the statuses before 'Cancelled'
        ).update(status='cancelled')

        # Automatically update the status of memberships that are pending and created more than two days ago to 'Cancelled'
        queryset.filter(created_at__lt=two_days_ago, status='pending').update(status='cancelled')

        # Reapply ordering by '-id'
        queryset = Membership.objects.all().order_by('-id')

        # Search logic
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(user__username__icontains=search_query) |
                Q(plan__name__icontains=search_query) |
                Q(tx_ref__icontains=search_query)
            )

        return queryset

class MembershipDetailView(OwnerManagerOrReceptionistRequiredMixin, DetailView):
    model = Membership
    template_name = 'admins/membership_detail.html'






from django.http import JsonResponse

class MembershipCreateView(OwnerManagerOrReceptionistRequiredMixin, View):
    form_class = MembershipCreateForm
    template_name = 'admins/membership_form.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            plan = form.cleaned_data['plan']
            payment_method = form.cleaned_data['payment_method']
            first_name = form.cleaned_data['for_first_name']
            last_name = form.cleaned_data['for_last_name']
            phone_number = form.cleaned_data['for_phone_number']
            email = form.cleaned_data['for_email']
            status = form.cleaned_data['status']

            # Create membership
            membership = Membership.objects.create(
                plan=plan,
                for_first_name=first_name,
                for_last_name=last_name,
                for_phone_number=phone_number,
                for_email=email,
                tx_ref = self.generate_tx_ref(),
                start_date=form.cleaned_data['start_date'],
                end_date=form.cleaned_data['start_date'] + relativedelta(months=plan.duration_months),
                status=status
            )

            # Create payment instance
            payment = MembershipPayment.objects.create(
                membership=membership,
                transaction_id= membership.tx_ref,
                payment_method=payment_method,
                amount=plan.price,
                status='completed'
            )

            # Generate receipt PDF
            pdf_response = self.generate_pdf(membership)
            pdf_name = f"membership_receipt_{membership.id}_{membership.for_first_name if membership.for_first_name else membership.user.username}.pdf"
            pdf_file = ContentFile(pdf_response) 
            payment.receipt_pdf.save(pdf_name, pdf_file)

            if membership.for_email:
                from_email = 'adarhotel33@gmail.com'
                subject = 'Gym Membership Confirmation'
                html_content = render_to_string('gym/membership_confirmation_template.html', {'membership': membership})

                # Inline CSS
                html_content = transform(html_content)

                # Render email content from template
                
                user_email = membership.for_email 
                
                # Create email
                email_message = EmailMultiAlternatives(
                    subject=subject,
                    body=html_content,
                    from_email=from_email,
                    to=[user_email]
                )

                # Attach HTML content
                email_message.attach_alternative(html_content, "text/html")
                email_message.attach(f'receipt_{membership.id}_{membership.for_first_name}.pdf', pdf_response, 'application/pdf')
                
                # Send the email
                email_message.send()

            # Save and send the PDF response
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return HttpResponse(pdf_response, content_type='application/pdf')
            
            # Automatically download the PDF receipt
            response = HttpResponse(pdf_response, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="membership_receipt_{membership.id}_{membership.for_first_name}.pdf"'

            messages.success(request, 'Membership and Payment created successfully.')
            return response

        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Return form errors as JSON for AJAX requests
            return JsonResponse({'errors': form.errors}, status=400)

        return render(request, self.template_name, {'form': form})

    def generate_pdf(self, membership):
        buffer = BytesIO()

        # Generate QR code data
        qr_code_data = self.generate_qr_code(f'{BASE_URL}/admins/verify_membership/{membership.id}')
        
        context = {
            'membership': membership,
            'qr_code_data': qr_code_data,
        }

        html_string = render_to_string('gym/membership_confirmation_template_receipt.html', context)
        
        pisa_status = pisa.CreatePDF(html_string, dest=buffer)
        buffer.seek(0)
        return buffer.read()

    def generate_qr_code(self, data):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return mark_safe(f'data:image/png;base64,{img_str}')

    def generate_tx_ref(self):
        return f"membership-admin-tx-{''.join(random.choices(string.ascii_lowercase + string.digits, k=10))}"




class MembershipUpdateView(OwnerManagerOrReceptionistRequiredMixin, UpdateView):
    model = Membership
    template_name = 'admins/membership_update_form.html'
    form_class = MembershipUpdateForm
    success_url = reverse_lazy('admins:membership_list')
    success_message = "Membership was updated successfully."


class MembershipPaymentDownloadReceiptView(View):
    def get(self, request, pk, *args, **kwargs):
        payment = get_object_or_404(MembershipPayment, pk=pk)

        # Serve the file for download
        response = HttpResponse(payment.receipt_pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{payment.receipt_pdf.name}"'
        return response

class MembershipVerifyView(View):
    def get(self, request, membership_id, *args, **kwargs):
        try:
            membership = Membership.objects.get(id=membership_id)
        except Booking.DoesNotExist:
            return render(request, 'admins/membership_not_found.html')
        
        return render(request, 'admins/membership_verify.html', {'membership': membership})


# MembershipPayment Views
class MembershipPaymentListView(OwnerManagerOrReceptionistRequiredMixin, ListView):
    model = MembershipPayment
    template_name = 'admins/membershippayment_list.html'
    context_object_name = 'membershippayments'
    paginate_by = 10

    def get_queryset(self):
        queryset = MembershipPayment.objects.all().order_by('-id')
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(membership__user__username__icontains=search_query) |
                Q(membership__plan__name__icontains=search_query) |
                Q(transaction_id__icontains=search_query)
            )
        return queryset

class MembershipPaymentDetailView(OwnerOrManagerRequiredMixin, OwnerManagerOrReceptionistRequiredMixin, DetailView):
    model = MembershipPayment
    template_name = 'admins/membershippayment_detail.html'



class MembershipPaymentDeleteView(OwnerOrManagerRequiredMixin, DeleteView):
    model = MembershipPayment
    success_url = reverse_lazy('admins:membershippayment_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        membership = self.object.membership  # Get the associated membership instance
        success_url = self.get_success_url()
        try:
            self.object.delete()
            membership.delete()  # Delete the associated membership instance
            messages.success(self.request, 'Membership Payment and associated Membership successfully deleted.')
        except Exception as e:
            messages.error(self.request, f'Failed to delete membership payment: {str(e)}')
        return HttpResponseRedirect(success_url)













from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from Hall.models import Hall, Hall_Booking, Hall_Payment
from .forms import HallForm, HallBookingForm, HallPaymentForm

# Hall Views
class HallCreateView(OwnerOrManagerRequiredMixin, CreateView):
    model = Hall
    form_class = HallForm
    template_name = 'admins/hall_form.html'
    success_url = reverse_lazy('admins:hall_list')

class HallDetailView(OwnerManagerOrReceptionistRequiredMixin,DetailView):
    model = Hall
    template_name = 'admins/hall_detail.html'
class HallUpdateView(OwnerOrManagerRequiredMixin, UpdateView):
    model = Hall
    form_class = HallForm
    template_name = 'admins/hall_form.html'
    success_url = reverse_lazy('admins:hall_list')

class HallDeleteView(OwnerOrManagerRequiredMixin, DeleteView):
    model = Hall
    template_name = 'admins/hall_confirm_delete.html'
    success_url = reverse_lazy('admins:hall_list')

class HallListView(OwnerManagerOrReceptionistRequiredMixin,ListView):
    model = Hall
    template_name = 'admins/hall_list.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def get_queryset(self):
        queryset = Hall.objects.all().order_by('hall_number')  # Adjust ordering as needed
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(hall_number__icontains=search_query) |
                Q(hall_type__name__icontains=search_query)  # Assuming hall_type is a CharField or similar
            )
        return queryset

# Hall Booking Views
class HallAvailabilityView(OwnerManagerOrReceptionistRequiredMixin,FormView):
    form_class = CheckAvailabilityForm
    template_name = 'admins/hall_availability.html'

    def form_valid(self, form):
        hall = form.cleaned_data['hall']
        start_date = form.cleaned_data['start_date'].strftime('%Y-%m-%d')
        end_date = form.cleaned_data['end_date'].strftime('%Y-%m-%d') if form.cleaned_data['end_date'] else start_date
        start_time = form.cleaned_data['start_time'].strftime('%H:%M:%S')
        end_time = form.cleaned_data['end_time'].strftime('%H:%M:%S')

        conflicting_bookings = Hall_Booking.objects.filter(
            hall=hall,
            status='confirmed'
        ).filter(
            Q(start_date__lte=end_date) & Q(end_date__gte=start_date) &
            Q(start_time__lte=end_time) & Q(end_time__gte=start_time)
        )

        availability = not conflicting_bookings.exists()
        context = {
            'form': form,
            'hall': hall,
            'availability': availability,
        }

        if availability:
            # Store booking data in session with string conversion
            self.request.session['booking_data'] = {
                'start_date': start_date,
                'end_date': end_date,
                'start_time': start_time,
                'end_time': end_time,
            }
            return redirect('admins:hall_booking_create', pk=hall.pk)  # Redirect to booking create view

        return self.render_to_response(context)

class HallBookingCreateView(OwnerManagerOrReceptionistRequiredMixin,TemplateView):
    template_name = 'admins/hall_booking_form.html'
    form_class = HallBookingForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hall = get_object_or_404(Hall, pk=self.kwargs['pk'])
        booking_data = self.request.session.get('booking_data')

        if not booking_data:
            # Handle case where booking data is missing
            return redirect('admins:hall_availability')

        start_date = booking_data['start_date']
        end_date = booking_data.get('end_date')
        start_time = booking_data['start_time']
        end_time = booking_data['end_time']

        # Calculate total cost
        start_time_dt = datetime.strptime(start_time, '%H:%M:%S').time()
        end_time_dt = datetime.strptime(end_time, '%H:%M:%S').time()
        today = date.today()

        duration_hours = Decimal((datetime.combine(today, end_time_dt) - datetime.combine(today, start_time_dt)).seconds) / Decimal(3600)

        if end_date:
            days = (datetime.strptime(end_date, '%Y-%m-%d').date() - datetime.strptime(start_date, '%Y-%m-%d').date()).days + 1
            total_cost = duration_hours * hall.price_per_hour * Decimal(days)
        else:
            total_cost = duration_hours * hall.price_per_hour

        context.update({
            'hall': hall,
            'start_date': start_date,
            'end_date': end_date,
            'start_time': start_time_dt,
            'end_time': end_time_dt,
            'total_cost': total_cost,
        })

        return context

    def post(self, request, *args, **kwargs):
        hall = get_object_or_404(Hall, pk=self.kwargs['pk'])
        booking_data = self.request.session.get('booking_data')

        if not booking_data:
            # Handle case where booking data is missing
            return redirect('admins:hall_availability')


        start_date = booking_data['start_date']
        end_date = booking_data.get('end_date')
        start_time = booking_data['start_time']
        end_time = booking_data['end_time']
        total_cost = self.get_context_data(**kwargs)['total_cost']
        full_name = request.POST.get('full_name')
        email = request.POST.get('email2')
        id_image = request.FILES.get('id_image')
        tx_ref = f"booking-{full_name.replace(' ', '')}-tx-{''.join(random.choices(string.ascii_lowercase + string.digits, k=10))}"
        # Create the booking
        booking = Hall_Booking.objects.create(
            hall=hall,
            start_date=start_date,
            end_date=end_date,
            start_time=start_time,
            end_time=end_time,
            amount_due=total_cost,
            status='pending',
            full_name=full_name,
            email2=email,
            id_image=id_image,
            tx_ref=tx_ref    # Save the full name to the booking
        )

        # Clear booking data from session
        del request.session['booking_data']
        print(booking.id)
        print(booking.pk)


        return redirect('admins:hall_payment_create', pk=booking.pk)

class HallPaymentCreateView(OwnerManagerOrReceptionistRequiredMixin, TemplateView):
    template_name = 'admins/hall_payment_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        booking = get_object_or_404(Hall_Booking, pk=self.kwargs['pk'])
        context['hall_booking'] = booking
        context['form'] = HallPaymentForm()
        return context

    def post(self, request, *args, **kwargs):
        booking = get_object_or_404(Hall_Booking, pk=self.kwargs['pk'])
        form = HallPaymentForm(request.POST)
        
        if form.is_valid():
            payment_method = form.cleaned_data['payment_method']

            # Create the payment instance
            payment = Hall_Payment.objects.create(
                booking=booking,
                payment_method=payment_method,
                transaction_id=booking.tx_ref,
                status='completed'
            )
            
            payment.save()
            booking.status = 'confirmed'
            booking.save()

            # Generate receipt PDF
            pdf_response = self.generate_pdf(booking)
            pdf_name = f"hall_booking_receipt_{booking.id}_{booking.full_name if booking.full_name else booking.user.username}.pdf"
            pdf_file = ContentFile(pdf_response) 
            payment.receipt_pdf.save(pdf_name, pdf_file)
            if booking.email2:
                from_email = 'adarhotel33@gmail.com'
                subject = 'Hall Booking Confirmation'
                html_content = render_to_string('hall/booking_confirmation_template.html', {'booking': booking})
                # Inline CSS
                html_content = transform(html_content)

                # Render email content from template
                
                user_email = booking.email2 
                
                # Create email
                email_message = EmailMultiAlternatives(
                    subject=subject,
                    body=html_content,
                    from_email=from_email,
                    to=[user_email]
                )

                # Attach HTML content
                email_message.attach_alternative(html_content, "text/html")
                email_message.attach(f'receipt_{booking.id}_{booking.full_name}.pdf', pdf_response, 'application/pdf')
                
                # Send the email
                email_message.send()

            
            

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return HttpResponse(pdf_response, content_type='application/pdf')
            
            # Automatically download the PDF receipt
            response = HttpResponse(pdf_response, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="receipt_{booking.id}_{booking.full_name}.pdf"'

            messages.success(request, f'{payment_method.capitalize()} payment method selected.')
            return response
        else:
            context = self.get_context_data(**kwargs)
            context['form'] = form
            return self.render_to_response(context)

    def generate_pdf(self, booking):
        buffer = BytesIO()
        
        # Generate QR code data
        qr_code_data = self.generate_qr_code(f'{BASE_URL}/admins/verify_hall_booking/{booking.id}')
        
        context = {
            'booking': booking,
            'qr_code_data': qr_code_data,
        }
        
        html_string = render_to_string('hall/booking_confirmation_template_receipt.html', context)
        
        pisa_status = pisa.CreatePDF(html_string, dest=buffer)
        buffer.seek(0)
        return buffer.read()

    def generate_qr_code(self, data):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return mark_safe(f'data:image/png;base64,{img_str}')



class HallPaymentDownloadReceiptView(View):
    def get(self, request, pk, *args, **kwargs):
        payment = get_object_or_404(Hall_Payment, pk=pk)
        response = HttpResponse(payment.receipt_pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{payment.receipt_pdf.name}"'
        return response

class HallBookingVerifyView(View):
    def get(self, request, booking_id, *args, **kwargs):
        try:
            booking = Hall_Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            return render(request, 'admins/hall_booking_not_found.html')
        
        return render(request, 'admins/hall_booking_verify.html', {'booking': booking})
class HallBookingDetailView(OwnerManagerOrReceptionistRequiredMixin,DetailView):
    model = Hall_Booking
    template_name = 'admins/hall_booking_detail.html'
    context_object_name = 'object'

class HallBookingUpdateView(OwnerManagerOrReceptionistRequiredMixin,UpdateView):
    model = Hall_Booking
    form_class = HallBookingUpdateForm
    template_name = 'admins/hall_booking_update_form.html'
    success_url = reverse_lazy('admins:hall_booking_list')

class HallDownloadIDImageView(View):
    def get(self, request, pk):
        try:
            booking = Hall_Booking.objects.get(pk=pk)
            if booking.id_image:
                response = HttpResponse(booking.id_image, content_type='image/jpeg')
                response['Content-Disposition'] = f'attachment; filename="{booking.id_image.name}"'
                return response
            else:
                raise Http404("No ID image available for this booking.")
        except Booking.DoesNotExist:
            raise Http404("Booking not found.")


class HallBookingListView(OwnerManagerOrReceptionistRequiredMixin, ListView):
    model = Hall_Booking
    template_name = 'admins/hall_booking_list.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def get_queryset(self):
        queryset = Hall_Booking.objects.all().order_by('-created_at')

        # Get the current time and two days ago
        now = timezone.now()
        two_days_ago = now - timedelta(days=2)

        # Fetch hall bookings that have a past end_date and are either pending or confirmed
        past_hall_bookings = queryset.filter(end_date__lt=now, status__in=['pending', 'confirmed'])

        for booking in past_hall_bookings:
            # Update booking status to 'cancelled'
            booking.status = 'cancelled'

            # Set hall status to 'available'
            booking.hall.status = 'available'

            # Save the changes to the booking and hall
            booking.hall.save()
            booking.save()

        # Automatically cancel hall bookings that are pending and created more than two days ago
        pending_old_hall_bookings = queryset.filter(created_at__lt=two_days_ago, status='pending')
        
        for booking in pending_old_hall_bookings:
            # Update booking status to 'cancelled'
            booking.status = 'cancelled'

            # Set hall status to 'available'
            booking.hall.status = 'available'

            # Save the changes to the booking and hall
            booking.hall.save()
            booking.save()

        # Reapply ordering by '-created_at'
        queryset = Hall_Booking.objects.all().order_by('-created_at')

        # Search logic
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(user__username__icontains=search_query) |
                Q(hall__hall_number__icontains=search_query) |
                Q(hall__hall_type__name__icontains=search_query) |
                Q(tx_ref__icontains=search_query)
            )

        return queryset



class HallPaymentDeleteView(OwnerOrManagerRequiredMixin, DeleteView):
    model = Hall_Payment
    success_url = reverse_lazy('admins:hall_payment_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        hall_booking = self.object.booking  # Get the associated hall booking instance
        success_url = self.get_success_url()
        try:
            self.object.delete()
            hall_booking.delete()  # Delete the associated hall booking instance
            messages.success(self.request, 'Hall Payment and associated Hall Booking successfully deleted.')
        except Exception as e:
            messages.error(self.request, f'Failed to delete hall payment: {str(e)}')
        return HttpResponseRedirect(success_url)

class HallPaymentDetailView(OwnerManagerOrReceptionistRequiredMixin,DetailView):
    model = Hall_Payment
    template_name = 'admins/hall_payment_detail.html'
    context_object_name = 'payment'

class HallPaymentListView(OwnerManagerOrReceptionistRequiredMixin,ListView):
    model = Hall_Payment
    template_name = 'admins/hall_payment_list.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def get_queryset(self):
        queryset = Hall_Payment.objects.all().order_by('-payment_date')
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(transaction_id__icontains=search_query) |
                Q(status__icontains=search_query)
            )
        return queryset


from Spa.models import SpaService, SpaPackage
from .forms import SpaServiceForm, SpaPackageForm

# SpaService Views
class SpaServiceListView(OwnerManagerOrReceptionistRequiredMixin, ListView):
    model = SpaService
    template_name = 'admins/spa_service_list.html'
    context_object_name = 'spa_services'
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get('search')
        if query:
            return SpaService.objects.filter(name__icontains=query)
        return SpaService.objects.order_by('name')

class SpaServiceDetailView(OwnerManagerOrReceptionistRequiredMixin, DetailView):
    model = SpaService
    template_name = 'admins/spa_service_detail.html'

class SpaServiceCreateView(OwnerOrManagerRequiredMixin, CreateView):
    model = SpaService
    form_class = SpaServiceForm
    template_name = 'admins/spa_service_form.html'
    success_url = reverse_lazy('admins:spa_service_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Spa Service created successfully.')
        return response

class SpaServiceUpdateView(OwnerOrManagerRequiredMixin, UpdateView):
    model = SpaService
    form_class = SpaServiceForm
    template_name = 'admins/spa_service_form.html'
    success_url = reverse_lazy('admins:spa_service_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Spa Service updated successfully.')
        return response

class SpaServiceDeleteView(OwnerOrManagerRequiredMixin, DeleteView):
    model = SpaService
    template_name = 'admins/spa_service_confirm_delete.html'
    success_url = reverse_lazy('admins:spa_service_list')

# SpaPackage Views
class SpaPackageListView(OwnerManagerOrReceptionistRequiredMixin, ListView):
    model = SpaPackage
    template_name = 'admins/spa_package_list.html'
    context_object_name = 'spapackages'
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get('search')
        if query:
            return SpaPackage.objects.filter(name__icontains=query)
        return SpaPackage.objects.order_by('name')

class SpaPackageDetailView(OwnerManagerOrReceptionistRequiredMixin, DetailView):
    model = SpaPackage
    template_name = 'admins/spa_package_detail.html'

class SpaPackageCreateView(OwnerOrManagerRequiredMixin, CreateView):
    model = SpaPackage
    form_class = SpaPackageForm
    template_name = 'admins/spa_package_form.html'
    success_url = reverse_lazy('admins:spa_package_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Spa Package created successfully.')
        return response

class SpaPackageUpdateView(OwnerOrManagerRequiredMixin, UpdateView):
    model = SpaPackage
    form_class = SpaPackageForm
    template_name = 'admins/spa_package_form.html'
    success_url = reverse_lazy('admins:spa_package_list')

    def get_object(self, queryset=None):
        return super().get_object(queryset)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        return form
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Spa Package updated successfully.')
        return response

    def form_invalid(self, form):
        # Print form errors to the console
        print(form.errors)
        # Optionally, you can log the errors or handle them as needed
        messages.error(self.request, 'There was an error updating the Spa Package.')
        return super().form_invalid(form)
class SpaPackageDeleteView(OwnerOrManagerRequiredMixin, DeleteView):
    model = SpaPackage
    template_name = 'admins/spa_package_confirm_delete.html'
    success_url = reverse_lazy('admins:spa_package_list')

class SpaPaymentDownloadReceiptView(View):
    def get(self, request, pk, *args, **kwargs):
        payment = get_object_or_404(SpaPayment, pk=pk)

        # Serve the file for download
        response = HttpResponse(payment.receipt_pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{payment.receipt_pdf.name}"'
        return response

class SpaBookingVerifyView(View):
    def get(self, request, spa_booking_id, *args, **kwargs):
        try:
            booking = SpaBooking.objects.get(id=spa_booking_id)
        except SpaBooking.DoesNotExist:
            return render(request, 'admins/spa_booking_not_found.html')
        
        return render(request, 'admins/spa_booking_verify.html', {'booking': booking})



from django.core.files.base import ContentFile
from admins.forms import SpaBookingForm

class SpaBookingCreateView(LoginRequiredMixin, FormView):
    form_class = SpaBookingForm
    template_name = 'admins/spa_booking_form.html'
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            # Form is valid, handle it
            return self.form_valid(form)
        else:
            # Form is invalid, return errors
            return self.form_invalid(form)


    def form_valid(self, form):
        service = form.cleaned_data.get('service')
        package = form.cleaned_data.get('package')

        if service:
            selected_item = service
            item_type = 'service'
        elif package:
            selected_item = package
            item_type = 'package'
        else:
            return self.form_invalid(form)

        appointment_date = form.cleaned_data['appointment_date']
        appointment_time = form.cleaned_data['appointment_time']

        existing_booking = SpaBooking.objects.filter(
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            service=selected_item if item_type == 'service' else None,
            package=selected_item if item_type == 'package' else None,
            status='pending',
        ).first()

        if existing_booking:
            form.add_error(None, 'You have an identical booking.')
            return self.form_invalid(form)

        total_bookings = SpaBooking.objects.filter(
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            service=selected_item if item_type == 'service' else None,
            package=selected_item if item_type == 'package' else None,
            status='pending',
        ).count()

        if total_bookings >= 5:
            form.add_error(None, 'This time slot is fully booked. Please select a different time.')
            return self.form_invalid(form)

        spa_booking = self.create_booking(form, selected_item, item_type)
        pdf_data = self.generate_pdf(spa_booking)
        payment = self.create_payment(spa_booking, form, pdf_data)

        if spa_booking.for_email:
                from_email = 'adarhotel33@gmail.com'
                subject = 'Spa Booking Confirmation'
                html_content = render_to_string('spa/booking_confirmation_template.html', {'spa_booking': spa_booking})


                # Inline CSS
                html_content = transform(html_content)

                # Render email content from template
                
                user_email = spa_booking.for_email 
                
                # Create email
                email_message = EmailMultiAlternatives(
                    subject=subject,
                    body=html_content,
                    from_email=from_email,
                    to=[user_email]
                )

                # Attach HTML content
                email_message.attach_alternative(html_content, "text/html")
                email_message.attach(f'receipt_{spa_booking.id}_{spa_booking.for_first_name}.pdf', pdf_data, 'application/pdf')
                
                # Send the email
                email_message.send()

        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return HttpResponse(pdf_data, content_type='application/pdf')


        response = HttpResponse(pdf_data, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="spa_booking_receipt_{spa_booking.id}_{spa_booking.for_first_name}.pdf"'
        messages.success(self.request, 'Booking and payment created successfully.')
        return response

    def form_invalid(self, form):
        print('form', form.errors)
        
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'errors': form.errors}, status=400)
        
        # For non-AJAX requests, fallback to the default behavior
        return super().form_invalid(form)  

    def create_booking(self, form, selected_item, item_type):
        spa_booking = SpaBooking.objects.create(
            service=selected_item if item_type == 'service' else None,
            package=selected_item if item_type == 'package' else None,
            appointment_date=form.cleaned_data['appointment_date'],
            appointment_time=form.cleaned_data['appointment_time'],
            amount_due=selected_item.price,
            for_first_name=form.cleaned_data['for_first_name'],
            for_last_name=form.cleaned_data['for_last_name'],
            for_phone_number=form.cleaned_data['for_phone_number'],
            for_email=form.cleaned_data['for_email'],
            status='confirmed',
            tx_ref=self.generate_tx_ref(),
        )
        return spa_booking

    def create_payment(self, spa_booking, form, pdf_data):
        payment_method = form.cleaned_data['payment_method']
        payment = SpaPayment.objects.create(
            spa_booking=spa_booking,
            transaction_id=spa_booking.tx_ref,
            payment_method=payment_method,
            amount=spa_booking.amount_due,
            status='completed',
        )

        # Save the PDF receipt to the 'receipt' field
        pdf_name = f"spa_booking_receipt_{spa_booking.id}_{spa_booking.for_first_name}.pdf"
        payment.receipt_pdf.save(pdf_name, ContentFile(pdf_data))
        payment.save()

        return payment

    def generate_pdf(self, spa_booking):
        buffer = BytesIO()

        # Generate QR code data
        qr_code_data = self.generate_qr_code(f'{BASE_URL}/admins/verify_booking/{spa_booking.id}')

        context = {
            'spa_booking': spa_booking,
            'qr_code_data': qr_code_data,
        }

        html_string = render_to_string('spa/booking_confirmation_template_receipt.html', context)
        print("Generated HTML for PDF:", html_string)
        pisa_status = pisa.CreatePDF(html_string, dest=buffer)
        if pisa_status.err:
            raise Exception("PDF generation failed")

        buffer.seek(0)
        return buffer.read()

    def generate_qr_code(self, data):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return mark_safe(f'data:image/png;base64,{img_str}')

    def generate_tx_ref(self):
        return f"spa_booking-admin-tx-{''.join(random.choices(string.ascii_lowercase + string.digits, k=10))}"

class SpaBookingUpdateView(OwnerManagerOrReceptionistRequiredMixin, UpdateView):
    model = SpaBooking
    template_name = 'admins/spa_booking_update_form.html'
    form_class = SpaBookingUpdateForm
    success_url = reverse_lazy('admins:spa_booking_list')
    success_message = "Spa Booking status was updated successfully."



class SpaBookingListView(OwnerManagerOrReceptionistRequiredMixin, ListView):
    model = SpaBooking
    template_name = 'admins/spa_booking_list.html'
    context_object_name = 'spabookings'
    paginate_by = 10

    def get_queryset(self):
        queryset = SpaBooking.objects.all().order_by('-id')

        # Get the current time and two days ago
        now = timezone.now()
        two_days_ago = now - timedelta(days=2)

        # Automatically update the status of spa bookings with a past appointment_date to 'Cancelled'
        queryset.filter(
            appointment_date__lt=now,
            status__in=['pending', 'confirmed']  # Assuming 'pending' and 'confirmed' are valid statuses
        ).update(status='cancelled')

        # Automatically update the status of spa bookings that are pending and created more than two days ago to 'Cancelled'
        queryset.filter(created_at__lt=two_days_ago, status='pending').update(status='cancelled')

        # Reapply ordering by '-id'
        queryset = SpaBooking.objects.all().order_by('-id')

        # Search logic
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(user__username__icontains=search_query) |
                Q(service__name__icontains=search_query) |
                Q(package__name__icontains=search_query) |
                Q(tx_ref__icontains=search_query)
            )

        return queryset

class SpaBookingDetailView(OwnerManagerOrReceptionistRequiredMixin, DetailView):
    model = SpaBooking
    template_name = 'admins/spa_booking_detail.html'


class SpaPaymentListView(OwnerManagerOrReceptionistRequiredMixin, ListView):
    model = SpaPayment
    template_name = 'admins/spa_payment_list.html'
    context_object_name = 'spapayments'
    paginate_by = 10

    def get_queryset(self):
        queryset = SpaPayment.objects.all().order_by('-id')
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(spa_booking__user__username__icontains=search_query) |
                Q(spa_booking__service__name__icontains=search_query) |
                Q(spa_booking__package__name__icontains=search_query) |
                Q(transaction_id__icontains=search_query)
            )
        return queryset

class SpaPaymentDetailView(OwnerManagerOrReceptionistRequiredMixin, DetailView):
    model = SpaPayment
    template_name = 'admins/spa_payment_detail.html'

class SpaPaymentDeleteView(OwnerOrManagerRequiredMixin, DeleteView):
    model = SpaPayment
    success_url = reverse_lazy('admins:spa_payment_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        spa_booking = self.object.spa_booking  # Get the associated spa booking instance
        success_url = self.get_success_url()
        try:
            self.object.delete()
            spa_booking.delete()  # Delete the associated spa booking instance
            messages.success(self.request, 'Spa Payment and associated Spa Booking successfully deleted.')
        except Exception as e:
            messages.error(self.request, f'Failed to delete spa payment: {str(e)}')
        return HttpResponseRedirect(success_url)



from django.http import JsonResponse
from django.utils.dateparse import parse_datetime
from django.db.models import Q
from django.db.models import Q

class ChatListView(ListView):
    model = Custom_user
    template_name = 'admins/chat_list.html'
    context_object_name = 'users'

    def get_queryset(self):
        logged_in_user = self.request.user.role
        return Custom_user.objects.exclude(role=logged_in_user).filter(chatmessage__isnull=False).distinct()




import logging

logger = logging.getLogger(__name__)

class ChatDetailView(DetailView):
    model = Custom_user
    template_name = 'admins/chat_detail.html'
    context_object_name = 'user'
    pk_url_kwarg = 'user_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recipient = self.get_object()
        messages = ChatMessage.objects.filter(
            models.Q(user=self.request.user) | models.Q(user=recipient)
        ).order_by('timestamp')
        context['messages'] = messages
        context['logged_in_user'] = self.request.user
        return context





import asyncio
from django.conf import settings
from telegram import Bot

# Create a Bot instance with your token
bot = Bot(token=TELEGRAM_BOT_TOKEN)

async def send_telegram_message_async(telegram_user_id, message):
    try:
        await bot.send_message(chat_id=telegram_user_id, text=message)
    except Exception as e:
        print(f"An error occurred: {e}")

def send_telegram_message(telegram_user_id, message):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    try:
        asyncio.run(bot.send_message(chat_id=telegram_user_id, text=message))
    except Exception as e:
        print(f"An error occurred: {e}")
class SendMessageView(View):
    def post(self, request, user_id):
        recipient = get_object_or_404(Custom_user, pk=user_id)
        message_text = request.POST.get('message')
        success_url = reverse('admins:chat_detail', kwargs={'user_id': user_id})


        # Create the message with the sender being the logged-in user
        new_message = ChatMessage.objects.create(user=request.user, message=message_text)

        # Send the message to the recipient via Telegram bot if the sender is staff
        if request.user.role != 'customer':
            send_telegram_message(recipient.telegram_user_id, message_text)

        return HttpResponseRedirect(success_url)












# SocialMediaPost Views
class SocialMediaPostListView(OwnerOrManagerRequiredMixin, ListView):
    model = SocialMediaPost
    template_name = 'admins/social_media_post_list.html'
    context_object_name = 'social_media_posts'
    def get_queryset(self):
        return Category.objects.order_by('name')


class SocialMediaPostDetailView(OwnerOrManagerRequiredMixin, DetailView):
    model = SocialMediaPost
    template_name = 'admins/social_media_post_detail.html'

class SocialMediaPostCreateView(OwnerOrManagerRequiredMixin, CreateView):
    model = SocialMediaPost
    template_name = 'admins/social_media_post_form.html'
    fields = '__all__'
    success_url = reverse_lazy('admins:social_media_post_list')

class SocialMediaPostUpdateView(OwnerOrManagerRequiredMixin, UpdateView):
    model = SocialMediaPost
    template_name = 'admins/social_media_post_form.html'
    fields = '__all__'
    success_url = reverse_lazy('admins:social_media_post_list')

class SocialMediaPostDeleteView(OwnerOrManagerRequiredMixin, DeleteView):
    model = SocialMediaPost
    template_name = 'admins/social_media_post_confirm_delete.html'
    success_url = reverse_lazy('admins:social_media_post_list')

# ChatMessage Views
class ChatMessageListView(OwnerOrManagerRequiredMixin, ListView):
    model = ChatMessage
    template_name = 'admins/chat_message_list.html'
    context_object_name = 'chat_messages'
    def get_queryset(self):
        return Category.objects.order_by('name')


class ChatMessageDetailView(OwnerOrManagerRequiredMixin, DetailView):
    model = ChatMessage
    template_name = 'admins/chat_message_detail.html'

class ChatMessageCreateView(OwnerOrManagerRequiredMixin, CreateView):
    model = ChatMessage
    template_name = 'admins/chat_message_form.html'
    fields = '__all__'
    success_url = reverse_lazy('admins:chat_message_list')

class ChatMessageUpdateView(OwnerOrManagerRequiredMixin, UpdateView):
    model = ChatMessage
    template_name = 'admins/chat_message_form.html'
    fields = '__all__'
    success_url = reverse_lazy('admins:chat_message_list')




from django.shortcuts import render
from django.http import HttpResponse
from django.views import View
from django.utils.timezone import now
import datetime
import openpyxl
from django.db.models import Count, Sum
from Spa.models import SpaBooking, SpaService, SpaPackage, SpaPayment

class SpaReportView(View):
    def get(self, request):
        # Data for all models
        bookings = SpaBooking.objects.all()
        services = SpaService.objects.all()
        packages = SpaPackage.objects.all()
        payments = SpaPayment.objects.all()

        # Calculated reports
        current_month = now().month
        current_year = now().year
        
        monthly_bookings = bookings.filter(created_at__year=current_year, created_at__month=current_month).count()
        monthly_revenue = payments.filter(payment_date__year=current_year, payment_date__month=current_month).aggregate(total=Sum('amount'))['total'] or 0
        
        # Filter out bookings where service is None
        bookings_with_service = bookings.exclude(service__isnull=True)
        bookings_by_service = bookings_with_service.values('service__name').annotate(total=Count('id'))

        # Filter out bookings where package is None
        bookings_with_package = bookings.exclude(package__isnull=True)
        bookings_by_package = bookings_with_package.values('package__name').annotate(total=Count('id'))
        
        context = {
            'bookings': bookings,
            'services': services,
            'packages': packages,
            'payments': payments,
            'monthly_bookings': monthly_bookings,
            'monthly_revenue': monthly_revenue,
            'bookings_by_service': bookings_by_service,
            'bookings_by_package': bookings_by_package,
        }
        
        return render(request, 'admins/spa_reports.html', context)

class ExportSpaReportView(View):
    
    def post(self, request, report_type):
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename={report_type}_report.xlsx'

        wb = Workbook()
        ws = wb.active
        ws.title = f'{report_type.capitalize()} Report'

        # Parse the dates from the POST request
        start_month = request.POST.get('start_month')
        end_month = request.POST.get('end_month')

        if start_month and end_month:
            try:
                start_date = datetime.strptime(start_month, '%Y-%m').date()
                end_date = datetime.strptime(end_month, '%Y-%m').date()
            except ValueError:
                return HttpResponse("Invalid date format", status=400)

        # Handle various report types
        if report_type == 'bookings':
            bookings = SpaBooking.objects.all()
            ws.append(['Booking ID', 'User', 'Service', 'Package', 'Booking Date', 'Appointment Date', 'Appointment Time'])
            for booking in bookings:
                ws.append([
                    booking.id,
                    booking.user.username if booking.user else f"{booking.for_first_name} {booking.for_last_name}",
                    booking.service.name if booking.service else 'N/A',
                    booking.package.name if booking.package else 'N/A',
                    booking.created_at.strftime('%Y-%m-%d'),
                    booking.appointment_date.strftime('%Y-%m-%d') if booking.appointment_date else 'N/A',
                    booking.appointment_time.strftime('%H:%M:%S') if booking.appointment_time else 'N/A'
                ])

        elif report_type == 'services':
            services = SpaService.objects.all()
            ws.append(['Service ID', 'Name', 'Description', 'Price'])
            for service in services:
                ws.append([service.id, service.name, service.description, service.price])

        elif report_type == 'packages':
            packages = SpaPackage.objects.all()
            ws.append(['Package ID', 'Name', 'Description', 'Price'])
            for package in packages:
                ws.append([package.id, package.name, package.description, package.price])

        elif report_type == 'payments':
            payments = SpaPayment.objects.all()
            ws.append(['Payment ID', 'Booking ID', 'Booked By', 'Amount', 'Payment Date', 'Payment Method'])
            for payment in payments:
                person = payment.spa_booking.user.username if payment.spa_booking.user else f"{payment.spa_booking.for_first_name} {payment.spa_booking.for_last_name}"
                ws.append([
                    payment.id,
                    payment.spa_booking.id,
                    person,
                    payment.amount,
                    payment.payment_date.strftime('%Y-%m-%d'),
                    payment.payment_method if payment.payment_method else 'N/A'
                ])

        # Monthly Bookings Report
        elif report_type == 'monthly_bookings':
            current_date = start_date
            bookings_data = []
            month_totals = {}

            while current_date <= end_date:
                next_month = current_date.replace(day=28) + timedelta(days=4)
                next_month_start = next_month - timedelta(days=next_month.day - 1)

                bookings = SpaBooking.objects.filter(
                    created_at__gte=current_date,
                    created_at__lt=next_month_start
                )

                monthly_count = bookings.count()
                month_totals[current_date.strftime('%Y-%m')] = monthly_count

                for booking in bookings:
                    bookings_data.append([
                        booking.id,
                        booking.user.username if booking.user else f"{booking.for_first_name} {booking.for_last_name}",
                        booking.service.name if booking.service else 'N/A',
                        booking.package.name if booking.package else 'N/A',
                        booking.created_at.strftime('%Y-%m-%d')
                    ])

                current_date = next_month_start

            ws.append(['Booking ID', 'User', 'Service', 'Package', 'Booking Date'])
            for row in bookings_data:
                ws.append(row)

            ws.append([])
            ws.append(['Month', 'Total Bookings'])
            for month, total in month_totals.items():
                ws.append([month, total])

        # Monthly Revenue Report
        elif report_type == 'monthly_revenue':
            current_date = start_date
            revenue_data = []
            month_totals = {}

            while current_date <= end_date:
                next_month = current_date.replace(day=28) + timedelta(days=4)
                next_month_start = next_month - timedelta(days=next_month.day - 1)

                payments = SpaPayment.objects.filter(
                    payment_date__gte=current_date,
                    payment_date__lt=next_month_start
                )

                monthly_total = payments.aggregate(total=Sum('amount'))['total'] or 0
                month_totals[current_date.strftime('%Y-%m')] = monthly_total

                for payment in payments:
                    revenue_data.append([
                        payment.id,
                        payment.spa_booking.id,
                        payment.amount,
                        payment.payment_date.strftime('%Y-%m-%d'),
                        payment.payment_method
                    ])

                current_date = next_month_start

            ws.append(['Payment ID', 'Booking ID', 'Amount', 'Payment Date', 'Payment Method'])
            for row in revenue_data:
                ws.append(row)

            ws.append([])
            ws.append(['Month', 'Total Revenue'])
            for month, total in month_totals.items():
                ws.append([month, total])

        # Monthly Services Report
        elif report_type == 'monthly_services':
            current_date = start_date
            services_data = []
            month_totals = {}
            month_revenue = {}

            while current_date <= end_date:
                next_month = current_date.replace(day=28) + timedelta(days=4)
                next_month_start = next_month - timedelta(days=next_month.day - 1)

                # Get all bookings for services within the month
                service_bookings = SpaBooking.objects.filter(
                    appointment_date__gte=current_date,
                    appointment_date__lt=next_month_start,
                    service__isnull=False
                )

                monthly_count = service_bookings.count()
                total_revenue = service_bookings.aggregate(revenue=Sum('amount_due'))['revenue'] or 0

                month_totals[current_date.strftime('%Y-%m')] = monthly_count
                month_revenue[current_date.strftime('%Y-%m')] = total_revenue

                for booking in service_bookings:
                    services_data.append([
                        booking.service.id,
                        booking.service.name,
                        booking.service.description,
                        booking.service.price
                    ])

                current_date = next_month_start

            # Append service booking details to the worksheet
            ws.append(['Service ID', 'Name', 'Description', 'Price'])
            for row in services_data:
                ws.append(row)

            # Append the monthly totals and revenue to the worksheet
            ws.append([])
            ws.append(['Month', 'Total Service Bookings', 'Revenue (ETB)'])
            for month, total in month_totals.items():
                ws.append([month, total, month_revenue.get(month, 0)])

        # Monthly Packages Report
        elif report_type == 'monthly_packages':
            current_date = start_date
            packages_data = []
            month_totals = {}
            month_revenue = {}

            while current_date <= end_date:
                next_month = current_date.replace(day=28) + timedelta(days=4)
                next_month_start = next_month - timedelta(days=next_month.day - 1)

                # Get all bookings for packages within the month
                package_bookings = SpaBooking.objects.filter(
                    appointment_date__gte=current_date,
                    appointment_date__lt=next_month_start,
                    package__isnull=False
                )

                monthly_count = package_bookings.count()
                total_revenue = package_bookings.aggregate(revenue=Sum('amount_due'))['revenue'] or 0

                month_totals[current_date.strftime('%Y-%m')] = monthly_count
                month_revenue[current_date.strftime('%Y-%m')] = total_revenue

                for booking in package_bookings:
                    packages_data.append([
                        booking.package.id,
                        booking.package.name,
                        booking.package.description,
                        booking.package.price
                    ])

                current_date = next_month_start

            # Append package booking details to the worksheet
            ws.append(['Package ID', 'Name', 'Description', 'Price'])
            for row in packages_data:
                ws.append(row)

            # Append the monthly totals and revenue to the worksheet
            ws.append([])
            ws.append(['Month', 'Total Package Bookings', 'Revenue (ETB)'])
            for month, total in month_totals.items():
                ws.append([month, total, month_revenue.get(month, 0)])

        wb.save(response)
        return response




class RoomReportView(View):
    def get(self, request):
        current_month = now().month
        current_year = now().year

        # Monthly room bookings
        monthly_room_bookings = Booking.objects.filter(
            created_at__year=current_year, created_at__month=current_month
        ).count()

        # Monthly room revenue
        monthly_room_revenue = Payment.objects.filter(
            payment_date__year=current_year, payment_date__month=current_month
        ).aggregate(total=Sum('booking__total_amount'))['total'] or 0

        # Room popularity
        popular_rooms = Booking.objects.values('room__room_number').annotate(total=Count('id')).order_by('-total')

        # Guest satisfaction
        room_ratings = RoomRating.objects.values('room__room_number').annotate(avg_rating=Avg('rating')).order_by('-avg_rating')

        context = {
            'monthly_room_bookings': monthly_room_bookings,
            'monthly_room_revenue': monthly_room_revenue,
            'popular_rooms': popular_rooms,
            'room_ratings': room_ratings,
        }
        
        return render(request, 'admins/room_reports.html', context)

from openpyxl import Workbook
from datetime import datetime


from datetime import datetime, timedelta



class ExportRoomReportView(View):

    def post(self, request, report_type):
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename={report_type}_report.xlsx'

        wb = Workbook()
        ws = wb.active
        ws.title = f'{report_type.capitalize()} Report'

        start_month = request.POST.get('start_month')
        end_month = request.POST.get('end_month')

        if report_type == 'bookings':
            bookings = Booking.objects.all()
            ws.append(['Booking ID', 'Room Number', 'User', 'Check-in Date', 'Check-out Date', 'Total Amount', 'Status'])
            for booking in bookings:
                user_display = booking.full_name #.user.username if booking.user else booking.full_name
                ws.append([
                    booking.id,
                    booking.room.room_number,
                    user_display,
                    booking.check_in_date,
                    booking.check_out_date,
                    booking.total_amount,
                    booking.status,
                ])

        elif report_type == 'monthly_revenue':
            current_month = now().month
            current_year = now().year
            payments = Payment.objects.filter(payment_date__year=current_year, payment_date__month=current_month)
            ws.append(['Payment ID', 'Booking ID', 'Total Amount', 'Payment Date', 'Payment Method'])

            total_amount = 0
            for payment in payments:
                total_amount += payment.booking.toal_amount
                ws.append([
                    payment.id,
                    payment.booking.id,
                    payment.booking.toal_amount,
                    payment.payment_date,
                    payment.payment_method,
                ])
            ws.append(['', '', 'Total', total_amount])

        elif report_type == 'popularity':
            popular_rooms = Booking.objects.values('room__room_number').annotate(total=Count('id')).order_by('-total')
            ws.append(['Room Number', 'Total Bookings'])
            for room in popular_rooms:
                ws.append([room['room__room_number'], room['total']])

        elif report_type == 'satisfaction':
            room_ratings = RoomRating.objects.values('room__room_number').annotate(avg_rating=Avg('rating')).order_by('-avg_rating')
            ws.append(['Room Number', 'Average Rating'])
            for rating in room_ratings:
                ws.append([rating['room__room_number'], rating['avg_rating']])

        elif report_type == 'all_payments':
            payments = Payment.objects.all()
            ws.append(['Payment ID', 'Booking ID', 'Total Amount', 'Payment Date', 'Payment Method'])
            for payment in payments:
                # Convert payment_date to naive datetime
                payment_date_naive = payment.payment_date.replace(tzinfo=None)
                ws.append([
                    payment.id,
                    payment.booking.id,
                    payment.booking.toal_amount,
                    payment_date_naive,
                    payment.payment_method,
                ])

        # POST request with date range (monthly reports)
        if start_month and end_month:
            try:
                start_date = datetime.strptime(start_month, '%Y-%m').date()
                end_date = datetime.strptime(end_month, '%Y-%m').date()
            except ValueError:
                return HttpResponse("Invalid date format", status=400)

            if report_type == 'monthly_bookings':
                current_date = start_date
                bookings_data = []
                month_totals = {}

                while current_date <= end_date:
                    next_month = current_date.replace(day=28) + timedelta(days=4)  # this will get to the next month
                    next_month_start = next_month - timedelta(days=next_month.day - 1)

                    bookings = Booking.objects.filter(
                        check_in_date__gte=current_date,
                        check_in_date__lt=next_month_start
                    )

                    monthly_count = bookings.count()
                    month_totals[current_date.strftime('%Y-%m')] = monthly_count

                    for booking in bookings:
                        user_display = booking.user.username if booking.user else booking.full_name
                        bookings_data.append([
                            booking.id,
                            booking.created_at.replace(tzinfo=None) if booking.created_at else None,
                            booking.room.room_number,
                            user_display,
                            booking.check_in_date,
                            booking.check_out_date,
                            booking.total_amount,
                            booking.status
                        ])

                    current_date = next_month_start  # move to the next month

                # Write booking details
                ws.append(['Booking ID','Booking Date', 'Room Number', 'User', 'Check-in Date', 'Check-out Date', 'Total Amount', 'Status'])
                for row in bookings_data:
                    ws.append(row)

                # Write summary of monthly bookings
                ws.append([])
                ws.append(['Month', 'Total Bookings'])
                for month, total in month_totals.items():
                    ws.append([month, total])

            elif report_type == 'monthly_revenue':
                current_date = start_date
                revenue_data = []
                month_totals = {}

                while current_date <= end_date:
                    next_month = current_date.replace(day=28) + timedelta(days=4)  # this will get to the next month
                    next_month_start = next_month - timedelta(days=next_month.day - 1)

                    payments = Payment.objects.filter(
                        payment_date__gte=current_date,
                        payment_date__lt=next_month_start
                    )

                    monthly_total = payments.aggregate(total=Sum('booking__total_amount'))['total'] or 0
                    month_totals[current_date.strftime('%Y-%m')] = monthly_total

                    for payment in payments:
                        payment_date_naive = payment.payment_date.replace(tzinfo=None)  # Convert to naive datetime
                        revenue_data.append([
                            payment.id,
                            payment.booking.id,
                            payment.booking.total_amount,
                            payment_date_naive,
                            payment.payment_method
                        ])

                    current_date = next_month_start  # move to the next month

                # Write payment details
                ws.append(['Payment ID', 'Booking ID', 'Total Amount', 'Payment Date', 'Payment Method'])
                for row in revenue_data:
                    ws.append(row)

                # Write summary of monthly revenue
                ws.append([])
                ws.append(['Month', 'Total Revenue'])
                for month, total in month_totals.items():
                    ws.append([month, total])

        wb.save(response)
        return response





class HallReportView(View):
    def get(self, request):
        current_month = now().month
        current_year = now().year

        # Monthly hall bookings
        monthly_hall_bookings = Hall_Booking.objects.filter(
            created_at__year=current_year, created_at__month=current_month
        ).count()

        # Monthly hall revenue
        monthly_hall_revenue = Hall_Booking.objects.filter(
            created_at__year=current_year, created_at__month=current_month
        ).aggregate(total=Sum('amount_due'))['total'] or 0

        # Hall popularity (number of bookings)
        popular_halls = Hall_Booking.objects.values('hall__hall_number').annotate(total=Count('id')).order_by('-total')

        # Guest satisfaction (average rating - assuming there's a HallRating model similar to RoomRating)
        # hall_ratings = HallRating.objects.values('hall__hall_number').annotate(avg_rating=Avg('rating')).order_by('-avg_rating')

        context = {
            'monthly_hall_bookings': monthly_hall_bookings,
            'monthly_hall_revenue': monthly_hall_revenue,
            'popular_halls': popular_halls,
            # 'hall_ratings': hall_ratings,  # Uncomment if ratings are implemented
        }
        
        return render(request, 'admins/hall_reports.html', context)


class ExportHallReportView(View):
    def post(self, request, report_type):
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename={report_type}_report.xlsx'

        wb = Workbook()
        ws = wb.active
        ws.title = f'{report_type.capitalize()} Report'

        start_month = request.POST.get('start_month')
        end_month = request.POST.get('end_month')

        if start_month and end_month:
            start_date = datetime.strptime(start_month, '%Y-%m')
            end_date = datetime.strptime(end_month, '%Y-%m')

        if report_type == 'bookings':
            bookings = Hall_Booking.objects.all()
            ws.append(['Booking ID', 'Hall Number', 'User', 'Start Date', 'End Date','Start Time','End Time', 'Total Amount', 'Status'])
            for booking in bookings:
                user_display = booking.user.username if booking.user else booking.full_name
                ws.append([
                    booking.id,
                    booking.hall.hall_number,
                    user_display,
                    booking.start_date,
                    booking.end_date,
                    booking.start_time,
                    booking.end_time,
                    booking.amount_due,
                    booking.status,
                ])

        elif report_type == 'all_payments':
            payments = Hall_Payment.objects.all()
            ws.append(['Payment ID', 'Booking ID', 'Payment Method', 'Transaction ID', 'Payment Date', 'Status'])
            for payment in payments:
                payment_date_naive = payment.payment_date.replace(tzinfo=None)
                ws.append([
                    payment.id,
                    payment.booking.id,
                    payment.payment_method,
                    payment.transaction_id,
                    payment_date_naive,
                    payment.status,
                ])

        # Monthly Payments Report
        elif report_type == 'monthly_payments':
            current_date = start_date
            payment_data = []
            month_totals = {}

            # Loop through each month in the date range
            while current_date <= end_date:
                next_month = current_date.replace(day=28) + timedelta(days=4)
                next_month_start = next_month - timedelta(days=next_month.day - 1)

                # Get payments for the current month
                payments = Hall_Payment.objects.filter(
                    payment_date__gte=current_date,
                    payment_date__lt=next_month_start
                )

                # Calculate the total for the current month
                monthly_total = payments.aggregate(total=Sum('booking__amount_due'))['total'] or 0
                month_totals[current_date.strftime('%Y-%m')] = monthly_total

                # Collect payment details
                for payment in payments:
                    payment_date_naive = payment.payment_date.replace(tzinfo=None)  # Convert to naive datetime
                    payment_data.append([
                        payment.id,
                        payment.booking.id,
                        payment.booking.amount_due,
                        payment_date_naive,
                        payment.payment_method
                    ])

                current_date = next_month_start  # Move to the next month

            # Write payment details to Excel
            ws.append(['Payment ID', 'Booking ID', 'Total Amount', 'Payment Date', 'Payment Method'])
            for row in payment_data:
                ws.append(row)

            # Add a space before the summary section
            ws.append([])
            ws.append([])

            # Write monthly totals to Excel
            ws.append(['Month', 'Total Payments'])
            for month, total in month_totals.items():
                ws.append([month, total])

        # Monthly Revenue Report
        elif report_type == 'monthly_revenue':
            current_date = start_date
            revenue_data = []
            month_totals = {}

            while current_date <= end_date:
                next_month = current_date.replace(day=28) + timedelta(days=4)
                next_month_start = next_month - timedelta(days=next_month.day - 1)

                payments = Hall_Payment.objects.filter(
                    payment_date__gte=current_date,
                    payment_date__lt=next_month_start
                )

                monthly_total = payments.aggregate(total=Sum('booking__amount_due'))['total'] or 0
                month_totals[current_date.strftime('%Y-%m')] = monthly_total

                for payment in payments:
                    payment_date_naive = payment.payment_date.replace(tzinfo=None)
                    revenue_data.append([
                        payment.id,
                        payment.booking.id,
                        payment.booking.amount_due,
                        payment_date_naive,
                        payment.payment_method
                    ])

                current_date = next_month_start

            # Write payment details
            ws.append(['Payment ID', 'Booking ID', 'Total Amount', 'Payment Date', 'Payment Method'])
            for row in revenue_data:
                ws.append(row)

            # Write summary of monthly revenue
            ws.append([])
            ws.append(['Month', 'Total Revenue'])
            for month, total in month_totals.items():
                ws.append([month, total])

        elif report_type == 'monthly_bookings':
            current_date = start_date
            bookings_data = []
            month_totals = {}

            while current_date <= end_date:
                next_month = current_date.replace(day=28) + timedelta(days=4)
                next_month_start = next_month - timedelta(days=next_month.day - 1)

                bookings = Hall_Booking.objects.filter(
                    start_date__gte=current_date,
                    start_date__lt=next_month_start
                )

                monthly_total = bookings.aggregate(total=Count('id'))['total'] or 0
                month_totals[current_date.strftime('%Y-%m')] = monthly_total
                
                for booking in bookings:
                    created_date_naive = booking.created_at.replace(tzinfo=None)
                    user_display = booking.user.username if booking.user else booking.full_name
                    bookings_data.append([
                        booking.id,
                        created_date_naive,
                        booking.hall.hall_number,
                        user_display,
                        booking.start_date,
                        booking.end_date,
                        booking.start_time,
                        booking.end_time,
                        booking.amount_due,
                        booking.status
                    ])

                current_date = next_month_start

            # Write booking details
            ws.append(['Booking ID','Created', 'Hall Number', 'User', 'Start Date', 'End Date','Start Time','End Time', 'Total Amount', 'Status'])
            for row in bookings_data:
                ws.append(row)

            # Write summary of monthly bookings
            ws.append([])
            ws.append(['Month', 'Total Bookings'])
            for month, total in month_totals.items():
                ws.append([month, total])
        # Hall Popularity Report
        elif report_type == 'popularity':
            hall_popularity = Hall_Booking.objects.values('hall__hall_number').annotate(total=Count('id')).order_by('-total')
            ws.append(['Hall Number', 'Total Bookings'])
            for hall in hall_popularity:
                ws.append([hall['hall__hall_number'], hall['total']])

        
        wb.save(response)
        return response



class MembershipReportView(View):
    def get(self, request):
        memberships = Membership.objects.all()
        membership_plans = MembershipPlan.objects.all()
        payments = MembershipPayment.objects.all()

        current_month = now().month
        current_year = now().year

        # Calculated reports
        monthly_memberships = memberships.filter(created_at__year=current_year, created_at__month=current_month).count()
        monthly_revenue = payments.filter(payment_date__year=current_year, payment_date__month=current_month).aggregate(total=Sum('amount'))['total'] or 0

        # Popularity of plans
        memberships_by_plan = memberships.values('plan__name').annotate(total=Count('id')).order_by('-total')

        context = {
            'memberships': memberships,
            'membership_plans': membership_plans,
            'payments': payments,
            'monthly_memberships': monthly_memberships,
            'monthly_revenue': monthly_revenue,
            'memberships_by_plan': memberships_by_plan,
        }

        return render(request, 'admins/membership_reports.html', context)

class ExportMembershipReportView(View):
    
    def post(self, request, report_type):
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename={report_type}_report.xlsx'

        wb = Workbook()
        ws = wb.active
        ws.title = f'{report_type.capitalize()} Report'

        start_month = request.POST.get('start_month')
        end_month = request.POST.get('end_month')

        if start_month and end_month:
            try:
                start_date = datetime.strptime(start_month, '%Y-%m').date()
                end_date = datetime.strptime(end_month, '%Y-%m').date()
            except ValueError:
                return HttpResponse("Invalid date format", status=400)

        if report_type == 'memberships':
            memberships = Membership.objects.all()
            ws.append(['Membership ID', 'User', 'Plan', 'Start Date', 'End Date', 'Status', 'Created At'])
            for membership in memberships:
                ws.append([
                    membership.id,
                    membership.user.username if membership.user else f"{membership.for_first_name} {membership.for_last_name}",
                    membership.plan.name,
                    membership.start_date.strftime('%Y-%m-%d'),
                    membership.end_date.strftime('%Y-%m-%d'),
                    membership.status,
                    membership.created_at.strftime('%Y-%m-%d %H:%M:%S')
                ])

        elif report_type == 'plans':
            plans = MembershipPlan.objects.all()
            ws.append(['Plan ID', 'Name', 'Price', 'Duration (Months)', 'Description'])
            for plan in plans:
                ws.append([plan.id, plan.name, plan.price, plan.duration_months, plan.description])

        elif report_type == 'payments':
            payments = MembershipPayment.objects.all()
            ws.append(['Payment ID', 'Membership ID', 'User', 'Amount', 'Payment Date', 'Payment Method', 'Status'])
            for payment in payments:
                user_display = payment.membership.user.username if payment.membership.user else f"{payment.membership.for_first_name} {payment.membership.for_last_name}"
                ws.append([
                    payment.id,
                    payment.membership.id,
                    user_display,
                    payment.amount,
                    payment.payment_date.strftime('%Y-%m-%d %H:%M:%S'),
                    payment.payment_method,
                    payment.status
                ])

        elif report_type == 'monthly_memberships':
            current_date = start_date
            memberships_data = []
            month_totals = {}

            while current_date <= end_date:
                next_month = current_date.replace(day=28) + timedelta(days=4)
                next_month_start = next_month - timedelta(days=next_month.day - 1)

                monthly_memberships = Membership.objects.filter(
                    created_at__gte=current_date,
                    created_at__lt=next_month_start
                )

                monthly_count = monthly_memberships.count()
                month_totals[current_date.strftime('%Y-%m')] = monthly_count

                for membership in monthly_memberships:
                    memberships_data.append([
                        membership.id,
                        membership.user.username if membership.user else f"{membership.for_first_name} {membership.for_last_name}",
                        membership.plan.name,
                        membership.start_date.strftime('%Y-%m-%d'),
                        membership.created_at.strftime('%Y-%m-%d')
                    ])

                current_date = next_month_start

            ws.append(['Membership ID', 'User', 'Plan', 'Start Date', 'Created At'])
            for row in memberships_data:
                ws.append(row)

            ws.append([])
            ws.append(['Month', 'Total Memberships'])
            for month, total in month_totals.items():
                ws.append([month, total])

        elif report_type == 'monthly_revenue':
            current_date = start_date
            revenue_data = []
            month_totals = {}

            while current_date <= end_date:
                next_month = current_date.replace(day=28) + timedelta(days=4)
                next_month_start = next_month - timedelta(days=next_month.day - 1)

                monthly_payments = MembershipPayment.objects.filter(
                    payment_date__gte=current_date,
                    payment_date__lt=next_month_start
                )

                monthly_total = monthly_payments.aggregate(total=Sum('amount'))['total'] or 0
                month_totals[current_date.strftime('%Y-%m')] = monthly_total

                for payment in monthly_payments:
                    revenue_data.append([
                        payment.id,
                        payment.membership.id,
                        payment.amount,
                        payment.payment_date.strftime('%Y-%m-%d %H:%M:%S'),
                        payment.payment_method
                    ])

                current_date = next_month_start

            ws.append(['Payment ID', 'Membership ID', 'Amount', 'Payment Date', 'Payment Method'])
            for row in revenue_data:
                ws.append(row)

            ws.append([])
            ws.append(['Month', 'Total Revenue'])
            for month, total in month_totals.items():
                ws.append([month, total])

        wb.save(response)
        return response


class RoomRatingListView(ListView):
    model = RoomRating
    template_name = 'admins/room_ratings.html'
    context_object_name = 'ratings'
    paginate_by = 5
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['room'] = get_object_or_404(Room, pk=self.kwargs['pk'])
        return context
