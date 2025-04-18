from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Room, Booking, Payment, RoomRating,Receipt
from .forms import BookingForm, RoomRatingForm
import requests
import random
from django.core.files.base import ContentFile
from reportlab.pdfgen import canvas
from django.db.models import Q
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.db.models import Min, Max
from django.http import JsonResponse
from django.http import HttpResponseRedirect
import string
from paypalrestsdk import Payment as PayPalPayment
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.dispatch import receiver
import requests
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.generic.edit import FormView
from .models import *
from django.contrib.sites.models import Site
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseBadRequest
from django.utils import timezone
from django.core.mail import send_mail
from django.contrib import messages
from django.views.generic.base import View
from django.db.models.signals import post_save
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .forms import BookingExtendForm
from django.utils.safestring import mark_safe
from django.views import View
from .forms import BookingExtendForm
from .models import Booking
from datetime import timedelta, date
from django.db import transaction
from django.db.models import Q
import json
# from gym.models import *
import logging
from config import BASE_URL
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
from django.http import HttpResponseNotFound
from django.http import HttpResponseServerError
from django.core.mail import EmailMultiAlternatives
from premailer import transform
# from Hall.models import *
from xhtml2pdf import pisa
from io import BytesIO
import qrcode
import base64
# from Spa.models import *
import os
from dotenv import load_dotenv

load_dotenv()

chapa_api_key = os.getenv('CHAPA_API_KEY')
paypal_client_id = os.getenv('PAYPAL_CLIENT_ID')
paypal_client_secret = os.getenv('PAYPAL_CLIENT_SECRET')




def home(request):
    rooms = Room.objects.all().order_by('room_type', 'id').distinct('room_type')
    return render(request, 'room/home.html', {'rooms': rooms})

from django.db.models import Avg

class RoomListView(ListView):
    model = Room
    template_name = 'room/rooms.html'
    context_object_name = 'rooms'

    def get_queryset(self):
        queryset = Room.objects.all()
        price = self.request.GET.get('price')
        room_type = self.request.GET.get('room_type')
        
        if price:
            queryset = queryset.filter(price_per_night__lte=price)
        if room_type:
            queryset = queryset.filter(room_type__id=room_type)
        
        # Annotate each room with the average rating
        queryset = queryset.annotate(average_rating=Avg('roomrating__rating'))
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['today'] = timezone.now().date()
        context['room_types'] = Category.objects.all()  # Assuming Category is your room type model

        min_price = Room.objects.aggregate(Min('price_per_night'))['price_per_night__min']
        max_price = Room.objects.aggregate(Max('price_per_night'))['price_per_night__max']

        if min_price is not None and max_price is not None:
            context['price_range'] = range(int(min_price), int(max_price) + 1, 100)  # Adjust the step as needed
        else:
            context['price_range'] = []

        return context

def about(request):
    return render(request, 'room/about.html')


def restaurant(request):
    return render(request, 'room/restaurant.html')

def agreement(request):
    return render(request, 'room/agreement.html')

def contact(request):
    return render(request, 'room/contact.html')


class RoomDetailView(DetailView):
    model = Room
    template_name = 'room/room_detail.html'
    context_object_name = 'room'


from django.db.models import Case, When, Value, IntegerField

class BookingListView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = 'room/bookings.html'
    context_object_name = 'bookings'

    def get_queryset(self):
        self.cancel_past_bookings() 
        bookings_lists = Booking.objects.filter(user=self.request.user).order_by('-id')
        return bookings_lists
    
    def cancel_past_bookings(self):
        # Cancel past bookings where check_out_date or extended_check_out_date is in the past and status is not already 'cancelled'
        past_bookings = Booking.objects.filter(
            Q(check_out_date__lt=timezone.now().date()) | Q(extended_check_out_date__lt=timezone.now().date())
        ).exclude(status='cancelled')
        for booking in past_bookings:
            booking.status = 'cancelled'
            booking.room.room_status = 'vacant'
            booking.checked_in = False
            booking.checked_out = True
            booking.save()

        # Cancel pending bookings where created_at is more than 2 days ago
        two_days_ago = timezone.now() - timedelta(days=2)
        pending_bookings = Booking.objects.filter(status='pending', created_at__lt=two_days_ago)
        for booking in pending_bookings:
            booking.status = 'cancelled'
            booking.room.room_status = 'vacant'
            booking.save()



class BookingCreateView(CreateView):
    model = Booking
    form_class = BookingForm
    template_name = 'room/booking_create.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['room'] = get_object_or_404(Room, id=self.kwargs['room_id'])
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        room = get_object_or_404(Room, id=self.kwargs['room_id'])
        context['room_image'] = room.room_image
        context['room_number'] = room.room_number  # Assuming 'number' is the field for room number
        context['room_type'] = room.room_type
        context['price_per_night'] = room.price_per_night 

        context['capacity'] = room.capacity  

        return context

    def form_valid(self, form):
        room = get_object_or_404(Room, id=self.kwargs['room_id'])
        form.instance.user = self.request.user
        form.instance.room = room
        form.instance.status = 'pending'
        form.instance.tx_ref = f"booking-tx-{''.join(random.choices(string.ascii_lowercase + string.digits, k=10))}"
        self.object = form.save()

        send_mail(
        subject="New Room Booking",
        message=f"A new booking has been made for Room {room.room_number}.\n\n"
                f"Name: {form.cleaned_data['full_name']}\n"
                f"Email: {form.cleaned_data['email2']}\n"
                f"Check-in: {form.cleaned_data['check_in_date']}\n"
                f"Check-out: {form.cleaned_data['check_out_date']}\n"
                f"Guests: {form.cleaned_data['guests']}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.OWNER_EMAIL],  # Set this in your settings.py
        fail_silently=False,
        )

        return redirect('payment_create', booking_id=self.object.id)

    def form_invalid(self, form):
        print("Form is invalid")
        print(form.errors)  # Print form errors to the console for debugging
        return self.render_to_response(self.get_context_data(form=form))


#creating payment
class PaymentView(View):
    template_name = 'room/payment_create.html'
    success_url = reverse_lazy('bookings')

    def dispatch(self, request, *args, **kwargs):
        self.booking = self.get_booking()
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = {}
        context['booking'] = self.booking
        context['user'] = self.booking.user
        context['amount'] = self.booking.original_booking_amount
        context['data'] = {
            "customization": {
                "title": "Payment for my booking",
                "description": "Confirming my booking"
            }
        }
        return context
    
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())
    
    def post(self, request, *args, **kwargs):
        payment_method = request.POST.get('payment_method')
        if payment_method == 'chapa':
            return self.process_chapa_payment()
        elif payment_method == 'paypal':
            return self.process_paypal_payment()
        else:
            messages.error(request, 'Invalid payment method selected.')
            return render(request, self.template_name, self.get_context_data())

    def get_booking(self):
        booking_id = self.kwargs.get('booking_id')
        return get_object_or_404(Booking, id=booking_id)
    
    def process_chapa_payment(self):
        if self.booking.is_paid or self.booking.status != 'pending':
            messages.warning(self.request, 'Payment already completed')
            return redirect('bookings')
        amount = str(self.booking.original_booking_amount)
        tx_ref = f"booking-{self.request.user.first_name}-tx-{''.join(random.choices(string.ascii_lowercase + string.digits, k=10))}"
        self.booking.tx_ref = tx_ref  # Store the new tx_ref in booking
        self.booking.save()

        url = "https://api.chapa.co/v1/transaction/initialize"
        redirect_url = f"{BASE_URL}"
        webhook_url = f"{BASE_URL}/room/chapa-webhook/"
        payload = {
            "amount": amount,
            "currency": "ETB",
            "email": self.booking.user.email,
            "first_name": self.booking.user.first_name,
            "last_name": self.booking.user.last_name,
            "phone_number": self.booking.user.phone_number,
            "redirect_url": redirect_url,
            "tx_ref": tx_ref,
            "callback_url": webhook_url,
        }
        headers = {
            'Authorization': f'Bearer {chapa_api_key}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        if response.status_code == 200:
            checkout_url = data['data']['checkout_url']
            return redirect(checkout_url)
        else:
            return HttpResponse(response)
    

    def process_paypal_payment(self):
        if self.booking.is_paid or self.booking.status != 'pending':
            messages.warning(self.request, 'Payment already completed')
            return render(self.request, self.template_name, self.get_context_data())
        paypalrestsdk.configure({
            "mode": "sandbox",  # sandbox or live
            "client_id": f'{paypal_client_id}',
            "client_secret": f'{paypal_client_secret}'
        })
        amount_in_dollars= self.booking.original_booking_amount/50
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"},
            "redirect_urls": {
                "return_url": f"{BASE_URL}/room/paypal-return/?booking_id={self.booking.id}",
                "cancel_url": f"{BASE_URL}/room/paypal-cancel/?booking_id={self.booking.id}"},
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": "room booking",
                        "sku": "item",
                        "price": str(amount_in_dollars),
                        "currency": "USD",
                        "quantity": 1}]},
                "amount": {
                    "total": str(amount_in_dollars),
                    "currency": "USD"},
                "description": "This is the payment transaction description."}]})

        if payment.create():
            for link in payment.links:
                if link.rel == "approval_url":
                    approval_url = link.href
                    break
            else:
                return HttpResponse("No approval URL returned by PayPal")
            return HttpResponseRedirect(approval_url)
        else:
            return HttpResponse("Error: " + payment.error)


from django.middleware.csrf import get_token

class BookingExtendView(View):
    template_name = 'room/booking_extend.html'

    def get(self, request, *args, **kwargs):
        booking = self.get_booking()
        today = timezone.now().date()

        # # Check if today is the last day of the booking
        # if not (booking.check_out_date == today or (booking.extended_check_out_date and booking.extended_check_out_date == today)):
        #     messages.error(request, "It must be your last day before extending the booking.")
        #     return redirect('my_bookings')  # Redirect to your booking list view

        form = BookingExtendForm(instance=booking)
        context = self.get_context_data(booking, form)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        booking = self.get_booking()
        form = BookingExtendForm(request.POST, instance=booking)
        
        if form.is_valid():
            extended_check_out_date = form.cleaned_data['extended_check_out_date']

            # Check room availability for the new date range
            if not self.is_room_available(booking.room, booking.check_out_date, extended_check_out_date):
                cancel_url = reverse('booking_cancel', kwargs={'pk': booking.id}) + '?next=rooms'
                csrf_token = get_token(request)
                messages.error(request, mark_safe(
                    "The room is booked for the selected dates and the booking cannot be extended. "
                    "You can cancel your existing booking and create a new booking by choosing one of the rooms by clicking "
                    "<a href='#' onclick=\"event.preventDefault(); document.getElementById('cancel-form').submit();\">this link</a>."
                    "<form id='cancel-form' action='{}' method='post' style='display:none;'>"
                    "<input type='hidden' name='csrfmiddlewaretoken' value='{}' /></form>".format(
                        cancel_url, csrf_token
                    )
                ))
                return self.form_invalid(form)

            if extended_check_out_date <= booking.check_out_date:
                form.add_error('extended_check_out_date', 'Extended check-out date must be after the current check-out date.')
                return self.form_invalid(form)
            elif extended_check_out_date <= booking.check_in_date:
                form.add_error('extended_check_out_date', 'Extended check-out date cannot be before the current check-in date.')
                return self.form_invalid(form)
            else:
                booking.extended_check_out_date = extended_check_out_date
                booking.status = 'pending'
                booking.save()
                return redirect('payment_extend', booking_id=booking.id)
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        booking = self.get_booking()
        return render(self.request, self.template_name, self.get_context_data(booking=booking, form=form))

    def get_booking(self):
        booking_id = self.kwargs.get('booking_id')
        return get_object_or_404(Booking, id=booking_id)

    def get_context_data(self, booking, form):
        context = {
            'booking': booking,
            'form': form
        }
        return context

    def is_room_available(self, room, check_out_date, extended_check_out_date):
        # Check if the room is available between the check_out_date and extended_check_out_date
        overlapping_bookings = Booking.objects.filter(
            room=room,
            status__in=['pending', 'confirmed'],
            check_in_date__range=(check_out_date, extended_check_out_date)
        ).exclude(id=self.kwargs.get('booking_id'))
        return not overlapping_bookings.exists()





    



class PaymentExtendView(View):
    template_name = 'room/payment_extend.html'

    def get(self, request, *args, **kwargs):
        booking = self.get_booking()
        context = self.get_context_data(booking)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        booking = self.get_booking()
        payment_method = request.POST.get('payment_method')
        
        if booking.is_paid or booking.status != 'confirmed':
            booking.status = 'pending'
            if booking.extended_check_out_date == booking.check_out_date:
                messages.warning(request, 'Payment Already Completed')
                return redirect('bookings')
            booking.booking_extend_amount = booking.calculate_additional_amount()
            booking.save()
            amount = booking.booking_extend_amount
            tx_ref = f"booking-{self.request.user.first_name}-tx-{''.join(random.choices(string.ascii_lowercase + string.digits, k=10))}"
            booking.tx_ref = tx_ref
            booking.save()

            if payment_method == 'chapa':
                amount=str(amount)
                return self.process_chapa_payment(booking, amount, tx_ref)
            elif payment_method == 'paypal':
                return self.process_paypal_payment(booking, amount)
            else:
                messages.error(request, 'Invalid payment method selected.')
                return render(request, self.template_name, self.get_context_data(booking=booking))
        else:
            messages.warning(request, 'Booking cannot be extended.')
            return redirect('bookings')

    def get_booking(self):
        booking_id = self.kwargs.get('booking_id')
        return get_object_or_404(Booking, id=booking_id)

    def get_context_data(self, booking):
        context = {
            'booking': booking,
            'amount': booking.calculate_additional_amount()
        }
        return context

    def process_chapa_payment(self, booking, amount, tx_ref):
        url = "https://api.chapa.co/v1/transaction/initialize"
        redirect_url = f"{BASE_URL}"
        webhook_url = f"{BASE_URL}/room/chapa-webhook/"
        print(webhook_url)

        payload = {
            "amount": str(amount),
            "currency": "ETB",
            "email": booking.user.email,
            "first_name": booking.user.first_name,
            "last_name": booking.user.last_name,
            "phone_number": booking.user.phone_number,
            "redirect_url": redirect_url,
            "tx_ref": tx_ref,
            "callback_url": webhook_url,
        }
        headers = {
            'Authorization': f'Bearer {chapa_api_key}',
            'Content-Type': 'application/json'
        }

        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        if response.status_code == 200:
            checkout_url = data['data']['checkout_url']
            return redirect(checkout_url)
        else:
            return HttpResponse(response)

    def process_paypal_payment(self, booking, amount):
        paypalrestsdk.configure({
            "mode": "sandbox",  # sandbox or live
            "client_id": f'{paypal_client_id}',
            "client_secret": f'{paypal_client_secret}'
        })
        amount_in_dollars = amount/50
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"},
            "redirect_urls": {
                "return_url": f"{BASE_URL}/room/paypal-return/?booking_id={booking.id}",
                "cancel_url": f"{BASE_URL}/room/paypal-cancel/?booking_id={booking.id}"},
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": "room booking",
                        "sku": "item",
                        "price": str(amount_in_dollars),
                        "currency": "USD",
                        "quantity": 1}]},
                "amount": {
                    "total": str(amount_in_dollars),
                    "currency": "USD"},
                "description": "This is the payment transaction description."}]})

        if payment.create():
            for link in payment.links:
                if link.rel == "approval_url":
                    approval_url = link.href
                    break
            else:
                return HttpResponse("No approval URL returned by PayPal")
            return HttpResponseRedirect(approval_url)
        else:
            return HttpResponse("Error: " + payment.error)



# Set up logging
logger = logging.getLogger(__name__)
import paypalrestsdk

from django.http import JsonResponse
    
    



class PayPalReturnView(View):
    def get(self, request, *args, **kwargs):
        payment_id = request.GET.get('paymentId')
        payer_id = request.GET.get('PayerID')
        booking_id = request.GET.get('booking_id')
        booking = get_object_or_404(Booking, id=booking_id)

        # Execute the payment
        payment = paypalrestsdk.Payment.find(payment_id)
        if payment.execute({"payer_id": payer_id}):
            if payment.state == "approved":
                booking.is_paid = True
                booking.status = 'confirmed'
                booking.tx_ref = f"booking-{self.request.user.first_name}-tx-{''.join(random.choices(string.ascii_lowercase + string.digits, k=10))}"

                if booking.booking_extend_amount is None:
                    booking.total_amount = booking.original_booking_amount
                booking.save()


                payment, created = Payment.objects.get_or_create(
                    booking=booking,
                    defaults={
                        'status': 'completed',
                        'transaction_id': booking.tx_ref,
                        'payment_method': 'paypal'
                    }
                )

                messages.success(request, 'Payment completed successfully.')

                # Generate receipt PDF
                pdf_response = self.generate_pdf(booking)
                pdf_name = f"room_booking_receipt_{booking.id}_{booking.full_name if booking.full_name else booking.user.username}.pdf"
                pdf_file = ContentFile(pdf_response) 
                payment.receipt_pdf.save(pdf_name, pdf_file)
                booking_url = f"{BASE_URL}/room/my-bookings/"
                if booking.extended_check_out_date:
                    subject = 'Room Booking Extension Confirmation'
                    html_content = render_to_string('room/checkout_date_extenstion_email_template.html', {'booking': booking, 'booking_url': booking_url})
                else:
                    subject = 'Room Booking Confirmation'
                    html_content = render_to_string('room/booking_confirmation_template.html', {'booking': booking, 'booking_url': booking_url})

                # Inline CSS
                html_content = transform(html_content)

                # Create the email message
                email = EmailMultiAlternatives(
                    subject=subject,
                    from_email='olikshomes@gmail.com',
                    to=[booking.user.email]
                )
                # Attach the HTML content
                email.attach_alternative(html_content, "text/html")
                # Attach the PDF receipt
                email.attach(f'receipt_{booking.id}_{booking.user.username}.pdf', pdf_response, 'application/pdf')

                # Send the email
                email.send()

                return redirect('bookings')
            else:
                messages.error(request, 'Payment was not successful.')
                return redirect('payment_create', booking_id=booking.id)
        else:
            messages.error(request, 'There was an issue with your PayPal payment.')
            return redirect('payment_create', booking_id=booking.id)

    def generate_pdf(self, booking):
        buffer = BytesIO()
        
        # Generate QR code data
        qr_code_data = self.generate_qr_code(f'{BASE_URL}/admins/verify/{booking.id}')
        
        context = {
            'booking': booking,
            'qr_code_data': qr_code_data,
        }
        
        if booking.extended_check_out_date:
            html_string = render_to_string('room/checkout_date_extenstion_email_template_receipt.html', context)
        else:
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


class PayPalCancelView(View):
    def get(self, request, *args, **kwargs):
        booking_id = request.GET.get('booking_id')
        messages.warning(request, 'Payment was cancelled.')
        return redirect('payment_page', booking_id=booking_id)



from django.http import HttpResponse, HttpResponseBadRequest

@method_decorator(csrf_exempt, name='dispatch')
class ChapaWebhookView(View):

    def get(self, request, *args, **kwargs):
        print("Webhook received via GET")
        
        try:
            # Parse JSON data from the request body
            payload = json.loads(request.body)
            print("Payload:", payload)
        except json.JSONDecodeError:
            print("Invalid JSON data")
            return HttpResponseBadRequest("Invalid JSON data")

        # Extract the transaction reference
        tx_ref = payload.get('trx_ref')
        print("Transaction reference:", tx_ref)

        if not tx_ref:
            print("Invalid tx_ref")
            return HttpResponseBadRequest("Invalid tx_ref")

        # Process the transaction based on tx_ref prefix
        if tx_ref.startswith('booking'):
            return self.process_booking_payment(tx_ref, payload)
        elif tx_ref.startswith('hall_booking'):
            return self.process_hall_booking_payment(tx_ref, payload)
        elif tx_ref.startswith('spa_booking'):
            return self.process_spa_booking_payment(tx_ref, payload)
        elif tx_ref.startswith('membership'):
            return self.process_membership_payment(tx_ref, payload)
        else:
            print("Invalid tx_ref prefix")
            return HttpResponseBadRequest("Invalid tx_ref prefix")

    # Existing payment processing methods remain the same


    def process_booking_payment(self, tx_ref, payload):
        try:
            booking = Booking.objects.get(tx_ref=tx_ref)
        except Booking.DoesNotExist:
            print("Booking not found")
            return HttpResponseNotFound("Booking not found")
        except Booking.MultipleObjectsReturned:
            print("Multiple bookings found")
            return HttpResponseServerError("Multiple bookings found")

        print("Booking found:", booking)

        payment, created = Payment.objects.get_or_create(
            booking=booking,
            defaults={
                'status': 'completed',
                'transaction_id': tx_ref,
                'payment_method': 'chapa'
            }
        )

        if not created:
            print("Payment already exists for this booking.")
            payment.status = 'completed'
            payment.transaction_id = tx_ref
            payment.save()

        print("Payment record created or updated:", payment)

        booking.is_paid = True
        booking.status = 'confirmed'
        booking.room.room_status = 'occupied'
        booking.room.save()
        booking.save()
        print('hh', booking.booking_extend_amount)
        if booking.booking_extend_amount is None:
            booking.total_amount = booking.original_booking_amount
            print("", booking.total_amount)
            booking.save()
        if booking.extended_check_out_date:
            booking.check_out_date = booking.extended_check_out_date
            if booking.booking_extend_amount is not None:
                print("", booking.total_amount)
                print("", booking.booking_extend_amount)
                booking.total_amount += booking.booking_extend_amount
            
            booking.save()

        
        booking_url = f"{BASE_URL}/room/my-bookings/"
        if booking.extended_check_out_date:
            subject = 'Room Booking Extension Confirmation'
            html_content = render_to_string('room/checkout_date_extenstion_email_template.html', {'booking': booking, 'booking_url': booking_url})
        else:
            subject = 'Room Booking Confirmation'
            bot_url = f"https://t.me/ADAR_HMS_bot"
            html_content = render_to_string('room/booking_confirmation_template.html', {'booking': booking, 'booking_url': booking_url,'bot_url':bot_url})

        # Inline CSS
        html_content = transform(html_content)

        # Create the email message
        email = EmailMultiAlternatives(
            subject=subject,
            from_email='olikshomes@gmail.com',
            to=[booking.user.email]
        )
        # Attach the HTML content
        email.attach_alternative(html_content, "text/html")

        # Generate receipt PDF
        pdf_response = self.generate_pdf(booking)
        pdf_name = f"room_booking_receipt_{booking.id}_{booking.full_name if booking.full_name else booking.user.username}.pdf"
        pdf_file = ContentFile(pdf_response) 
        payment.receipt_pdf.save(pdf_name, pdf_file)
        # Attach the PDF receipt
        email.attach(f'receipt_{booking.id}_{booking.user.username}.pdf', pdf_response, 'application/pdf')

        # Send the email
        email.send()
            
        print("Booking and room updated")
        booking.status = 'confirmed'
        booking.save()
        return HttpResponse("Booking webhook processed successfully")

    def generate_pdf(self, booking):
        buffer = BytesIO()
        
        # Generate QR code data
        qr_code_data = self.generate_qr_code(f'{BASE_URL}/admins/verify/{booking.id}')
        
        context = {
            'booking': booking,
            'qr_code_data': qr_code_data,
        }
        
        if booking.extended_check_out_date:
            html_string = render_to_string('room/checkout_date_extenstion_email_template_receipt.html', context)
        else:
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

    def process_hall_booking_payment(self, tx_ref, payload):
        try:
            booking = Hall_Booking.objects.get(tx_ref=tx_ref)
        except Hall_Booking.DoesNotExist:
            print("Hall Booking not found")
            return HttpResponseNotFound("Hall Booking not found")
        except Hall_Booking.MultipleObjectsReturned:
            print("Multiple hall bookings found")
            return HttpResponseServerError("Multiple hall bookings found")

        print("Hall Booking found:", booking)

        payment, created = Hall_Payment.objects.get_or_create(
            booking=booking,
            defaults={
                'status': 'completed',
                'transaction_id': tx_ref,
                'payment_method': 'chapa'
            }
        )

        if not created:
            print("Payment already exists for this booking.")
            payment.status = 'completed'
            payment.transaction_id = tx_ref
            payment.save()

        print("Payment record created or updated:", payment)

        booking.status = 'confirmed'
        booking.is_paid = True
        booking.save()

        booking_url = f"{BASE_URL}/hall/my-bookings/"
        html_content = render_to_string('hall/booking_confirmation_template.html', {'booking': booking})

        # Inline CSS
        html_content = transform(html_content)

        # Create the email message
        email = EmailMultiAlternatives(
            subject='Hall Booking Confirmation',
            from_email='olikshomes@gmail.com',
            to=[booking.user.email]
        )
        # Attach the HTML content
        email.attach_alternative(html_content, "text/html")

        # Generate receipt PDF
        pdf_response = self.generate_hall_pdf(booking)
        pdf_name = f"hall_booking_receipt_{booking.id}_{booking.full_name if booking.full_name else booking.user.username}.pdf"
        pdf_file = ContentFile(pdf_response) 
        payment.receipt_pdf.save(pdf_name, pdf_file)
        # Attach the PDF receipt
        email.attach(f'receipt_{booking.id}_{booking.user.username}.pdf', pdf_response, 'application/pdf')

        # Send the email
        email.send()

        print("Hall booking updated")
        return HttpResponse("Hall booking webhook processed successfully")
    
    def generate_hall_pdf(self, booking):
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

    def process_membership_payment(self, tx_ref, payload):
        try:
            membership = Membership.objects.get(tx_ref=tx_ref)
        except Membership.DoesNotExist:
            print("Membership not found")
            return HttpResponseNotFound("Membership not found")
        except Membership.MultipleObjectsReturned:
            print("Multiple memberships found")
            return HttpResponseServerError("Multiple memberships found")

        print("Membership found:", membership)
        amount = membership.plan.price
        print("Amount due:", amount)

        membership_payment, created = MembershipPayment.objects.get_or_create(
            membership=membership,
            defaults={
                'status': 'completed',
                'transaction_id': tx_ref,
                'amount': amount,
                'payment_method' : 'chapa'
            }
        )

        if not created:
            print("Payment already exists for this membership.")
            membership_payment.status = 'completed'
            membership_payment.transaction_id = tx_ref
            membership_payment.payment_method = 'chapa'
            membership_payment.save()

        print("Payment record created or updated:", membership_payment)

        membership.status = 'active'
        membership.save()

        membership_url = f"{BASE_URL}/gym/my-memberships/"
        html_content = render_to_string('gym/membership_confirmation_template.html', {'membership': membership, 'membership_url': membership_url})

        # Inline CSS
        html_content = transform(html_content)

        # Create the email message
        email = EmailMultiAlternatives(
            subject='Gym Membership Confirmation',
            from_email='olikshomes@gmail.com',
            to=[membership.user.email]
        )
        # Attach the HTML content
        email.attach_alternative(html_content, "text/html")

        # Generate receipt PDF
        pdf_response = self.generate_membership_pdf(membership)
        pdf_name = f"membership_booking_receipt_{membership.id}_{membership.for_first_name if membership.for_first_name else membership.user.username}.pdf"
        pdf_file = ContentFile(pdf_response) 
        membership_payment.receipt_pdf.save(pdf_name, pdf_file)
        # Attach the PDF receipt
        email.attach(f'receipt_{membership.id}_{membership.user.username}.pdf', pdf_response, 'application/pdf')

        # Send the email
        email.send()
        # Send the email to the "for" email if it exists
        if membership.for_email:
            for_email = EmailMultiAlternatives(
                subject='Gym Membership Confirmation',
                from_email='olikshomes@gmail.com',
                to=[membership.for_email]
            )
            for_email.attach_alternative(html_content, "text/html")
            # Generate receipt PDF
            pdf_response = self.generate_membership_pdf(membership)
            for_email.attach(f'receipt_{membership.id}_{membership.user.username}.pdf', pdf_response, 'application/pdf')
            for_email.send()
        print("Membership updated")

        return HttpResponse("Membership webhook processed successfully")
    
    def generate_membership_pdf(self, membership):
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
    def process_spa_booking_payment(self, tx_ref, payload):
        try:
            spa_booking = SpaBooking.objects.get(tx_ref=tx_ref)
        except SpaBooking.DoesNotExist:
            print("Spa booking not found")
            return HttpResponseNotFound("Spa booking not found")
        except SpaBooking.MultipleObjectsReturned:
            print("Multiple spa bookings found")
            return HttpResponseServerError("Multiple spa bookings found")

        print("Spa booking found:", spa_booking)
        amount  = spa_booking.amount_due
        print("Amount due:", amount)

        payment, created = SpaPayment.objects.get_or_create(
            spa_booking=spa_booking,
            defaults={
                'status': 'completed',
                'transaction_id': tx_ref,
                'amount': amount,
                'payment_method': 'chapa'
            }
        )

        if not created:
            print("Payment already exists for this spa booking.")
            payment.status = 'completed'
            payment.transaction_id = tx_ref
            payment.save()

        print("Payment record created or updated:", payment)

        spa_booking.status = 'confirmed'
        spa_booking.save()

        # Generate receipt PDF
        pdf_response = self.generate_spa_pdf(spa_booking)
        pdf_name = f"spa_booking_receipt_{spa_booking.id}_{spa_booking.for_first_name if spa_booking.for_first_name else spa_booking.user.username}.pdf"
        pdf_file = ContentFile(pdf_response)
        payment.receipt_pdf.save(pdf_name, pdf_file)

        booking_url = f"{BASE_URL}/spa/my-bookings/"
        html_content = render_to_string('spa/booking_confirmation_template.html', {'spa_booking': spa_booking, 'booking_url': booking_url})

        # Create the email message
        email = EmailMultiAlternatives(
            subject='Spa Booking Confirmation',
            from_email='olikshomes@gmail.com',
            to=[spa_booking.user.email]
        )
        # Attach the HTML content
        email.attach_alternative(html_content, "text/html")
        # Attach the PDF receipt
        email.attach(f'receipt_{spa_booking.id}_{spa_booking.user.username}.pdf', pdf_response, 'application/pdf')

        # Send the email
        email.send()
        
        if spa_booking.for_email not in [None, '']:
            for_email = EmailMultiAlternatives(
                subject='Spa Booking Confirmation',
                from_email='olikshomes@gmail.com',
                to=[spa_booking.for_email]
            )
            for_email.attach_alternative(html_content, "text/html")
            for_email.attach(f'receipt_{spa_booking.id}_{spa_booking.user.username}.pdf', pdf_response, 'application/pdf')
            for_email.send()

        print("Spa booking updated")
        return HttpResponse("Spa booking webhook processed successfully")

    def generate_spa_pdf(self, spa_booking):
        buffer = BytesIO()
        
        # Generate QR code data
        qr_code_data = self.generate_qr_code(f'{BASE_URL}/admins/verify_spa_booking/{spa_booking.id}')
        
        context = {
            'spa_booking': spa_booking,
            'qr_code_data': qr_code_data,
        }
        
        html_string = render_to_string('spa/booking_confirmation_template_receipt.html', context)
        
        pisa_status = pisa.CreatePDF(html_string, dest=buffer)
        buffer.seek(0)
        return buffer.read()



        

logger = logging.getLogger(__name__)



class BookingCancelView(LoginRequiredMixin, View):
    fields = []  # No fields to update through the form

    def get_queryset(self):
        owner_queryset = super().get_queryset()
        return owner_queryset.filter(user=self.request.user)


    def get_success_url(self):
        next_url = self.request.GET.get('next', 'bookings')  # Default to 'bookings' if 'next' is not provided
        if 'next' in self.request.GET:
            messages.success(self.request, 'You have successfully cancelled your previous booking, please create a new booking with the new date you want. ')
        return reverse(next_url)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        try:
            booking_id = kwargs.get('pk')
            booking = get_object_or_404(Booking, id=booking_id)
            booking.status = 'cancelled'
            booking.save()
            booking_url = f"{BASE_URL}/room/my-bookings/"
            html_content = render_to_string('room/cancellation_email_template.html', {'booking': booking, 'booking_url': booking_url})
            
            # Inline CSS
            html_content = transform(html_content)
            
            # Create the email message with only HTML content
            email = EmailMultiAlternatives(
                subject='Booking Cancellation Confirmation',
                from_email='olikshomes@gmail.com',
                to=[booking.user.email]
            )
            # Attach the HTML content
            email.attach_alternative(html_content, "text/html")
            
            # Send the email
            email.send()
            return HttpResponseRedirect(self.get_success_url())
        except Exception as e:
            print(f"Exception when canceling booking: {e}")
            return HttpResponseBadRequest("Error occurred while canceling the booking.")


def test_view(request, pk):
    room = get_object_or_404(Room, pk=pk)
    ratings = list(RoomRating.objects.filter(room=room).order_by('-rating_date'))
    return HttpResponse(f"Ratings fetched: {ratings}")

class RoomRatingListView(ListView):
    model = RoomRating
    template_name = 'room/room_ratings.html'
    context_object_name = 'ratings'
    paginate_by = 10  # Adjust the number of items per page as needed

    def get_queryset(self):
        self.room = get_object_or_404(Room, pk=self.kwargs['pk'])
        ratings = RoomRating.objects.filter(room=self.room).order_by('-rating_date')
        print(f"Ratings fetched: {ratings}")  # Add this line to check the fetched ratings
        return ratings
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['room'] = self.room
        return context

class AddRoomRatingView(CreateView):
    model = RoomRating
    form_class = RoomRatingForm
    template_name = 'room/add_room_rating.html'

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.room = get_object_or_404(Room, pk=self.kwargs['pk'])
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['room'] = get_object_or_404(Room, pk=self.kwargs['pk'])
        return context

    def get_success_url(self):
        return reverse_lazy('room_ratings', kwargs={'pk': self.kwargs['pk']})


class EditRoomRatingView(UpdateView):
    model = RoomRating
    form_class = RoomRatingForm
    template_name = 'room/edit_room_rating.html'
    pk_url_kwarg = 'rating_id'

    def get_success_url(self):
        return reverse_lazy('room_ratings', kwargs={'pk': self.object.room.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['room'] = self.object.room  # Add the room to the context
        return context
class DeleteRoomRatingView(DeleteView):
    model = RoomRating
    pk_url_kwarg = 'rating_id'

    def get_success_url(self):
        return reverse_lazy('room_ratings', kwargs={'pk': self.object.room.pk})



class ReceiptUploadView(CreateView):
    model = Receipt
    fields = ['file']
    template_name = 'room/upload_receipt.html'

    def form_valid(self, form):
        booking = Booking.objects.get(id=self.kwargs['booking_id'])
        form.instance.booking = booking

        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('bookings')


class UserRoomRatingsListView(LoginRequiredMixin, ListView):
    model = RoomRating
    template_name = 'room/my_room_ratings.html'
    context_object_name = 'ratings'

    def get_queryset(self):
        return RoomRating.objects.filter(user=self.request.user)









