from django.views.generic import ListView, CreateView, View
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import SpaService, SpaPackage, SpaBooking
from .forms import SpaBookingForm
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import FormView
from config import BASE_URL
import requests
from django.utils import timezone
import random
import string
from paypalrestsdk import Payment, configure 
from .models import SpaService, SpaPackage, SpaBooking
from .forms import SpaBookingForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from io import BytesIO
import qrcode
import base64
from xhtml2pdf import pisa
import paypalrestsdk
from .models import SpaBooking, SpaPayment
from django.utils.safestring import mark_safe
from django.db.models import Q
import os
from dotenv import load_dotenv

load_dotenv()

chapa_api_key = os.getenv('CHAPA_API_KEY')
paypal_client_id = os.getenv('PAYPAL_CLIENT_ID')
paypal_client_secret = os.getenv('PAYPAL_CLIENT_SECRET')


class ServiceListView(ListView):
    model = SpaService
    template_name = 'spa/spa_services_packages.html'
    context_object_name = 'services'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['packages'] = SpaPackage.objects.all()
        return context





from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
import random
import string
import requests
from paypalrestsdk import Payment, configure

class SpaBookingCreateView(LoginRequiredMixin, FormView):
    form_class = SpaBookingForm
    template_name = 'spa/spa_booking_create.html'

    def get_initial(self):
        initial = super().get_initial()
        item_type = self.kwargs.get('item_type')
        item_id = self.kwargs.get('item_id')

        selected_item = None
        if item_type == 'service':
            selected_item = SpaService.objects.filter(id=item_id).first()
        elif item_type == 'package':
            selected_item = SpaPackage.objects.filter(id=item_id).first()

        if selected_item:
            # Find an existing booking with a pending status for the user
            existing_booking = SpaBooking.objects.filter(
                user=self.request.user,
                service=selected_item if item_type == 'service' else None,
                package=selected_item if item_type == 'package' else None,
                status='pending'
            ).first()

            if existing_booking:
                initial.update({
                    'service': existing_booking.service,
                    'package': existing_booking.package,
                    'appointment_date': existing_booking.appointment_date,
                    'appointment_time': existing_booking.appointment_time,
                    'for_first_name': existing_booking.for_first_name,
                    'for_last_name': existing_booking.for_last_name,
                    'for_email': existing_booking.for_email,
                    'for_phone_number': existing_booking.for_phone_number,
                    'payment_method': 'chapa' if existing_booking.tx_ref.startswith('spa-booking') else 'paypal'
                })

                # Determine if the booking is for self or others based on existing data
                if existing_booking.for_first_name or existing_booking.for_last_name or existing_booking.for_email or existing_booking.for_phone_number:
                    initial['booking_for'] = 'others'
                else:
                    initial['booking_for'] = 'self'

        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item_type = self.kwargs.get('item_type')
        item_id = self.kwargs.get('item_id')

        if item_type == 'service':
            context['item'] = SpaService.objects.filter(id=item_id).first()
        elif item_type == 'package':
            context['item'] = SpaPackage.objects.filter(id=item_id).first()

        return context

    def form_valid(self, form):
        item_type = self.kwargs.get('item_type')
        item_id = self.kwargs.get('item_id')

        if item_type == 'service':
            selected_item = SpaService.objects.filter(id=item_id).first()
        elif item_type == 'package':
            selected_item = SpaPackage.objects.filter(id=item_id).first()
        else:
            selected_item = None

        if selected_item is None:
            messages.error(self.request, 'The item you are trying to book does not exist.')
            return redirect('spa:booking_list')

        appointment_date = form.cleaned_data['appointment_date']
        appointment_time = form.cleaned_data['appointment_time']
        booking_for = form.cleaned_data.get('booking_for')

        # Check for existing booking with the same date and time for the selected item
        existing_booking = SpaBooking.objects.filter(
            user=self.request.user,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            service=selected_item if item_type == 'service' else None,
            package=selected_item if item_type == 'package' else None,
            status='pending',
        ).first()

        if existing_booking:
            if existing_booking.for_first_name == form.cleaned_data.get('for_first_name') and \
                existing_booking.for_last_name == form.cleaned_data.get('for_last_name') and \
                existing_booking.for_email == form.cleaned_data.get('for_email') and \
                existing_booking.for_phone_number == form.cleaned_data.get('for_phone_number'):
                # If the existing booking matches the current form data, proceed to payment
                return self.redirect_to_payment(existing_booking, form.cleaned_data['payment_method'])
            else:
                # Otherwise, it is a double booking attempt
                messages.error(self.request, 'You have an identical booking.')
                return self.form_invalid(form)

        # Check if there are already 5 bookings for the same service/package, date, and time
        total_bookings = SpaBooking.objects.filter(
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            service=selected_item if item_type == 'service' else None,
            package=selected_item if item_type == 'package' else None,
            status='pending',
        ).count()

        if total_bookings >= 5:
            # If there are already 5 bookings for the same service/package, date, and time
            messages.error(self.request, 'This time slot is fully booked. Please select a different time.')
            return self.form_invalid(form)
        
        # Create new booking
        spa_booking = self.create_booking(form, selected_item, item_type)

        # Handle payment
        return self.redirect_to_payment(spa_booking, form.cleaned_data['payment_method'])

    def create_booking(self, form, selected_item, item_type):
        booking_for = form.cleaned_data.get('booking_for')

        spa_booking = SpaBooking.objects.create(
            user=self.request.user,
            service=selected_item if item_type == 'service' else None,
            package=selected_item if item_type == 'package' else None,
            appointment_date=form.cleaned_data['appointment_date'],
            appointment_time=form.cleaned_data['appointment_time'],
            amount_due=selected_item.price,
            for_first_name=form.cleaned_data['for_first_name'] if booking_for == 'others' else '',
            for_last_name=form.cleaned_data['for_last_name'] if booking_for == 'others' else '',
            for_phone_number=form.cleaned_data['for_phone_number'] if booking_for == 'others' else '',
            for_email=form.cleaned_data['for_email'] if booking_for == 'others' else '',
            status='pending',
            tx_ref=self.generate_tx_ref(),
        )
        return spa_booking

    def generate_tx_ref(self):
        return f"spa_booking-{self.request.user.username}-tx-{''.join(random.choices(string.ascii_lowercase + string.digits, k=10))}"

    def redirect_to_payment(self, booking, payment_method):
        if payment_method == 'chapa':
            return self.initiate_chapa_payment(booking)
        elif payment_method == 'paypal':
            return self.initiate_paypal_payment(booking)
        else:
            messages.error(self.request, 'Invalid payment method selected.')
            return redirect('spa:booking_list')

    def initiate_chapa_payment(self, spa_booking):
        amount = str(spa_booking.amount_due)
        print(amount)
        tx_ref = self.generate_tx_ref()
        spa_booking.tx_ref=tx_ref
        spa_booking.save()

        url = "https://api.chapa.co/v1/transaction/initialize"
        redirect_url = f'{BASE_URL}/spa/bookings'
        webhook_url = f'{BASE_URL}room/chapa-webhook/'

        payload = {
            "amount": amount,
            "currency": "ETB",
            "email": self.request.user.email,
            "first_name": self.request.user.first_name,
            "last_name": self.request.user.last_name,
            "phone_number": self.request.user.phone_number,
            "redirect_url": self.request.build_absolute_uri(redirect_url),
            "tx_ref": tx_ref,
            "callback_url": webhook_url,
        }
        headers = {
            'Authorization': f'Bearer {chapa_api_key}',
            'Content-Type': 'application/json'
        }
        print(headers)

        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        print(data)
        if response.status_code == 200 and data['status'] == 'success':
            return redirect(data['data']['checkout_url'])
        else:
            messages.error(self.request, 'Error initializing Chapa payment.')
            print(messages.error)
            return redirect('spa:booking_list')

    def initiate_paypal_payment(self, spa_booking):
        configure({
            "mode": "sandbox",
            "client_id": f'{paypal_client_id}',
            "client_secret": f'{paypal_client_secret}'
        })
        amount = spa_booking.amount_due / 50  # Assuming the price is converted to USD
        payment = Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": f"{BASE_URL}/spa/paypal-return/?booking_id={spa_booking.id}",
                "cancel_url": f"{BASE_URL}/spa/paypal-cancel/?booking_id={spa_booking.id}"
            },
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": f"Spa Booking: {spa_booking.service or spa_booking.package}",
                        "sku": "item",
                        "price": str(amount),
                        "currency": "USD",
                        "quantity": 1
                    }]
                },
                "amount": {
                    "total": str(amount),
                    "currency": "USD"
                },
                "description": f"Payment for {spa_booking.service or spa_booking.package}"
            }]
        })
        if payment.create():
            spa_booking.tx_ref = payment.id
            spa_booking.save()
            for link in payment.links:
                if link.method == "REDIRECT":
                    redirect_url = link.href
                    return redirect(redirect_url)
        else:
            messages.error(self.request, 'Error creating PayPal payment.')
            return redirect('spa:booking_list')








from django.core.files.base import ContentFile

class SpaPayPalReturnView(View):
    def get(self, request, *args, **kwargs):
        payment_id = request.GET.get('paymentId')
        payer_id = request.GET.get('PayerID')
        spa_booking = get_object_or_404(SpaBooking, tx_ref=payment_id)

        payment = paypalrestsdk.Payment.find(payment_id)
        if payment.execute({"payer_id": payer_id}):
            # Generate receipt PDF
            pdf_response = self.generate_pdf(spa_booking)
            pdf_name = f"spa_booking_receipt_{spa_booking.id}_{spa_booking.for_first_name if spa_booking.for_first_name else spa_booking.user.username}.pdf"
            pdf_file = ContentFile(pdf_response)  # Convert PDF response to ContentFile

            # Save the payment and PDF file to the model
            spa_payment = SpaPayment.objects.create(
                spa_booking=spa_booking,
                transaction_id=payment_id,
                amount=spa_booking.amount_due,
                status='completed',
                payment_method='paypal',
            )
            spa_payment.receipt_pdf.save(pdf_name, pdf_file)  # Save the PDF to the receipt_pdf field

            spa_booking.status = 'confirmed'
            spa_booking.save()

            booking_url = f"{BASE_URL}/spa/my-bookings/"
            html_content = render_to_string('spa/booking_confirmation_template.html', {'spa_booking': spa_booking, 'booking_url': booking_url})

            # Create the email message with only HTML content
            email = EmailMultiAlternatives(
                subject='Spa Booking Confirmation',
                from_email='adarhotel33@gmail.com',
                to=[spa_booking.user.email]
            )
            # Attach the HTML content
            email.attach_alternative(html_content, "text/html")
            # Attach the PDF receipt
            email.attach(pdf_name, pdf_response, 'application/pdf')

            # Send the email
            email.send()
            
            if spa_booking.for_email:
                for_email = EmailMultiAlternatives(
                    subject='Spa Booking Confirmation',
                    from_email='adarhotel33@gmail.com',
                    to=[spa_booking.for_email]
                )
                for_email.attach_alternative(html_content, "text/html")
                for_email.attach(pdf_name, pdf_response, 'application/pdf')
                for_email.send()

            messages.success(request, 'Payment successful and booking confirmed.')
        else:
            messages.error(request, 'Payment failed. Please try again.')

        return redirect('spa:booking_list')

    def generate_pdf(self, spa_booking):
        buffer = BytesIO()
        
        # Generate QR code data
        qr_code_data = self.generate_qr_code(f'{BASE_URL}/admins/verify_booking/{spa_booking.id}')
        
        context = {
            'spa_booking': spa_booking,
            'qr_code_data': qr_code_data,
        }
        
        html_string = render_to_string('spa/booking_confirmation_template_receipt.html', context)
        
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




class SpaPayPalCancelView(View):
    def get(self, request, *args, **kwargs):
        messages.warning(request, 'Payment cancelled.')
        return redirect('spa:booking_list')

from datetime import timedelta
from django.utils import timezone
class BookingListView(LoginRequiredMixin, ListView):
    model = SpaBooking
    template_name = 'spa/booking_list.html'
    context_object_name = 'bookings'


    def get_queryset(self):
        # Get all bookings for the logged-in user
        bookings = SpaBooking.objects.filter(user=self.request.user).order_by('-id')

        current_date = timezone.now().date()
        two_days_ago = timezone.now() - timedelta(days=2)
    
        # Get all bookings
        bookings_all = SpaBooking.objects.all()
        
        # Loop through the bookings and cancel those with past appointment dates
        for booking in bookings_all:
            # Cancel bookings with past appointment dates
            if booking.appointment_date < current_date:
                booking.status = 'cancelled'
                booking.save()
            # Cancel pending bookings where created_at date is more than 2 days ago
            elif booking.status == 'pending' and booking.created_at < two_days_ago:
                booking.status = 'cancelled'
                booking.save()

        return bookings


class CancelBookingView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        booking = SpaBooking.objects.get(id=kwargs['booking_id'], user=request.user)
        booking.status = 'cancelled'
        booking.save()
        return redirect('spa:booking_list')
