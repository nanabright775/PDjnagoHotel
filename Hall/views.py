# views.py
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect
from .models import Hall, Hall_Booking
from django.views.generic import DetailView, FormView
from .models import Hall, Hall_Booking, Hall_Payment,Hall_Category
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from .forms import CheckAvailabilityForm, BookingForm
import datetime
import random
from django.core.files.base import ContentFile
import string
import requests
from decimal import Decimal
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseNotFound, HttpResponseServerError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView
from django.contrib import messages
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from premailer import transform
import paypalrestsdk
from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy
from django.db import transaction
import json
from config import BASE_URL
from django.utils import timezone
from django.db.models import Min, Max
from django.db.models import Q
from xhtml2pdf import pisa
from io import BytesIO
import qrcode
from datetime import timedelta
import base64
from django.utils.safestring import mark_safe

import os
from dotenv import load_dotenv

load_dotenv()

chapa_api_key = os.getenv('CHAPA_API_KEY')
paypal_client_id = os.getenv('PAYPAL_CLIENT_ID')
paypal_client_secret = os.getenv('PAYPAL_CLIENT_SECRET')




class HallListView(ListView):
    model = Hall
    template_name = 'hall/hall_list.html'
    context_object_name = 'halls'

    def get_queryset(self):
        queryset = Hall.objects.filter(status='available')  # Adjust the status field as per your model
        price = self.request.GET.get('price')
        hall_type = self.request.GET.get('hall_type')

        if price:
            queryset = queryset.filter(price_per_hour__lte=price)
        if hall_type:
            queryset = queryset.filter(hall_type__id=hall_type)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['today'] = timezone.now().date()
        context['hall_types'] = Hall_Category.objects.all()  

        min_price = Hall.objects.aggregate(Min('price_per_hour'))['price_per_hour__min']
        max_price = Hall.objects.aggregate(Max('price_per_hour'))['price_per_hour__max']

        if min_price is not None and max_price is not None:
            context['price_range'] = range(int(min_price), int(max_price) + 1, 400)  # Adjust the step as needed
        else:
            context['price_range'] = []

        return context
class HallDetailView(DetailView):
    model = Hall
    template_name = 'hall/hall_details.html'
    context_object_name = 'hall'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CheckAvailabilityForm()
        return context
class CheckAvailabilityView(LoginRequiredMixin,FormView):
    form_class = CheckAvailabilityForm
    template_name = 'hall/hall_details.html'

    def form_valid(self, form):
        hall = Hall.objects.get(pk=self.kwargs['pk'])
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date'] if form.cleaned_data['end_date'] else start_date
        start_time = form.cleaned_data['start_time']
        end_time = form.cleaned_data['end_time']

        conflicting_bookings = Hall_Booking.objects.filter(
            hall=hall,
            status='confirmed'
        ).filter(
            Q(start_date__lte=end_date) & Q(end_date__gte=start_date) &
            Q(start_time__lte=end_time) & Q(end_time__gte=start_time)
        )

        if not conflicting_bookings.exists():
            # Store the form data in session
            self.request.session['booking_data'] = {
                'start_date': str(start_date),
                'end_date': str(end_date) if end_date else None,
                'start_time': str(start_time),
                'end_time': str(end_time)
            }
            return redirect(reverse_lazy('book_hall', kwargs={'pk': hall.pk}))
        else:
            context = {
                'form': form,
                'hall': hall,
                'availability': False,
            }
            return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hall'] = Hall.objects.get(pk=self.kwargs['pk'])
        return context

# views.py
from decimal import Decimal

class BookingView(LoginRequiredMixin,TemplateView):
    template_name = 'hall/booking_create.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hall = get_object_or_404(Hall, pk=self.kwargs['pk'])
        booking_data = self.request.session.get('booking_data')

        if not booking_data:
            # Handle case where booking data is missing
            return redirect('hall_detail', pk=hall.pk)

        start_date = booking_data['start_date']
        end_date = booking_data.get('end_date')
        start_time = booking_data['start_time']
        end_time = booking_data['end_time']

        context.update({
            'hall': hall,
            'start_date': start_date,
            'end_date': end_date,
            'start_time':  datetime.datetime.strptime(start_time, '%H:%M:%S').time(),
            'end_time':  datetime.datetime.strptime(end_time, '%H:%M:%S').time(),
        })

        # Calculate total cost
        if isinstance(start_time, str):
            start_time = datetime.datetime.strptime(start_time, '%H:%M:%S').time()
        if isinstance(end_time, str):
            end_time = datetime.datetime.strptime(end_time, '%H:%M:%S').time()

        start_time_dt = datetime.datetime.combine(datetime.date.today(), start_time)
        end_time_dt = datetime.datetime.combine(datetime.date.today(), end_time)
        duration_hours = Decimal((end_time_dt - start_time_dt).seconds) / Decimal(3600)

        # Ensure start_date and end_date are datetime.date objects
        if isinstance(start_date, str):
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()


        if end_date and end_date != start_date:
            days = (end_date - start_date).days + 1
            total_cost = 0
            for i in range(days):
                total_cost += duration_hours * hall.price_per_hour
        else:
            total_cost = duration_hours * hall.price_per_hour

        context['total_cost'] = total_cost
        return context

    def post(self, request, *args, **kwargs):
        hall = get_object_or_404(Hall, pk=self.kwargs['pk'])
        user = request.user
        booking_data = self.request.session.get('booking_data')

        if not booking_data:
            # Handle case where booking data is missing
            return redirect('hall_detail', pk=hall.pk)

        start_date = booking_data['start_date']
        end_date = booking_data.get('end_date')
        start_time = booking_data['start_time']
        end_time = booking_data['end_time']
        total_cost = self.get_context_data(**kwargs)['total_cost']

        # Create the booking
        booking = Hall_Booking.objects.create(
            user=user,
            hall=hall,
            start_date=start_date,
            end_date=end_date,
            start_time=start_time,
            end_time=end_time,
            amount_due=total_cost,
            status='pending'
        )

        # Clear booking data from session
        del request.session['booking_data']
         

        return redirect('payment_page', pk=booking.pk)



    


class PaymentView(LoginRequiredMixin,TemplateView):
    template_name = 'hall/payment_create.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        booking = get_object_or_404(Hall_Booking, pk=self.kwargs['pk'])
        context['booking'] = booking
        return context

    def post(self, request, *args, **kwargs):
        booking = get_object_or_404(Hall_Booking, pk=self.kwargs['pk'])
        payment_method = request.POST.get('payment_method')

        if payment_method == 'chapa':
            return self.process_chapa_payment(booking)
        elif payment_method == 'paypal':
            return self.process_paypal_payment(booking)
        else:
            messages.error(request, 'Invalid payment method selected.')
            return render(request, self.template_name, self.get_context_data())

    def process_chapa_payment(self, booking):
        if booking.is_paid or booking.status != 'pending':
            messages.warning(self.request, 'Payment already completed')
            return redirect('hall_bookings')

        amount = str(booking.amount_due)
        tx_ref = f"hall_booking-{self.request.user.first_name}-tx-{''.join(random.choices(string.ascii_lowercase + string.digits, k=10))}"
        booking.tx_ref = tx_ref  # Store the new tx_ref in booking
        booking.save()

        url = "https://api.chapa.co/v1/transaction/initialize"
        redirect_url = f"{BASE_URL}room/chapa-return/"
        webhook_url = f"{BASE_URL}room/chapa-webhook/"
        payload = {
            "amount": amount,
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

    def process_paypal_payment(self, booking):
        if booking.status != 'pending':
            messages.warning(self.request, 'Payment already completed')
            return render(self.request, self.template_name, self.get_context_data())

        paypalrestsdk.configure({
            "mode": "sandbox",  # sandbox or live
            "client_id": f'{paypal_client_id}',
            "client_secret": f'{paypal_client_secret}'
        })
        amount_in_dollars = "{:.2f}".format(booking.amount_due / 50)
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": f"{BASE_URL}/hall/paypal-return/?booking_id={booking.id}",
                "cancel_url": f"{BASE_URL}/hall/paypal-cancel/?booking_id={booking.id}"
            },
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": "hall booking",
                        "sku": "item",
                        "price": str(amount_in_dollars),
                        "currency": "USD",
                        "quantity": 1
                    }]
                },
                "amount": {
                    "total": str(amount_in_dollars),
                    "currency": "USD"
                },
                "description": "This is the payment for booking hall."
            }]
        })

        if payment.create():
            for link in payment.links:
                if link.rel == "approval_url":
                    approval_url = link.href
                    break
            else:
                return HttpResponse("No approval URL returned by PayPal")
            return HttpResponseRedirect(approval_url)
        else:
            return HttpResponse("Error: " + str(payment.error))
    

class PayPalReturnView(View):
    def get(self, request, *args, **kwargs):
        payment_id = request.GET.get('paymentId')
        payer_id = request.GET.get('PayerID')
        booking_id = request.GET.get('booking_id')
        booking = get_object_or_404(Hall_Booking, id=booking_id)

        # Execute the payment
        payment = paypalrestsdk.Payment.find(payment_id)
        if payment.execute({"payer_id": payer_id}):
            if payment.state == "approved":
                booking.status = 'confirmed'
                booking.is_paid = True
                booking.tx_ref = f"hall_booking-{self.request.user.first_name}-tx-{''.join(random.choices(string.ascii_lowercase + string.digits, k=10))}"
                booking.save()

                payment_record, created = Hall_Payment.objects.get_or_create(
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
                pdf_name = f"hall_booking_receipt_{booking.id}_{booking.full_name if booking.full_name else booking.user.username}.pdf"
                pdf_file = ContentFile(pdf_response) 
                payment_record.receipt_pdf.save(pdf_name, pdf_file)

                # Prepare the booking URL and render the confirmation email template
                booking_url = f"{BASE_URL}/hall/my-bookings/"
                html_content = render_to_string('hall/booking_confirmation_template.html', {'booking': booking, 'booking_url': booking_url})
                
                # Create the email message with only HTML content
                email = EmailMultiAlternatives(
                    subject='Hall Booking Confirmation',
                    from_email='adarhotel33@gmail.com',
                    to=[booking.user.email]
                )
                # Attach the HTML content
                email.attach_alternative(html_content, "text/html")
                # Attach the PDF receipt
                email.attach(f'receipt_{booking.id}_{booking.user.username}.pdf', pdf_response, 'application/pdf')

                # Send the email
                email.send()

                return redirect('hall_bookings')
            else:
                messages.error(request, 'Payment was not successful.')
                return redirect('payment_page', booking_id=booking.id)
        else:
            messages.error(request, 'There was an issue with your PayPal payment.')
            return redirect('payment_page', booking_id=booking.id)

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


class PayPalCancelView(View):
    def get(self, request, *args, **kwargs):
        booking_id = request.GET.get('booking_id')
        messages.warning(request, 'Payment was cancelled.')
        return redirect('payment_page', booking_id=booking_id)


class BookingListView(LoginRequiredMixin,ListView):
    model = Hall_Booking
    template_name = 'hall/my_bookings.html'
    context_object_name = 'bookings'

    def get_queryset(self):
        self.cancel_past_bookings()  
        return Hall_Booking.objects.filter(user=self.request.user).order_by('-id')

    
    def cancel_past_bookings(self):
        # Cancel past bookings where end_date is in the past and status is not already 'cancelled'
        past_bookings = Hall_Booking.objects.filter(end_date__lt=timezone.now().date()).exclude(status='cancelled')
        for booking in past_bookings:
            booking.status = 'cancelled'
            booking.hall.status = 'available'
            booking.save()
        
        # Cancel pending bookings where created_at is more than 2 days ago
        two_days_ago = timezone.now() - timedelta(days=2)
        pending_bookings = Hall_Booking.objects.filter(status='pending', created_at__lt=two_days_ago)
        for booking in pending_bookings:
            booking.status = 'cancelled'
            booking.hall.status = 'available'
            booking.save()




class HallBookingCancelView(LoginRequiredMixin, UpdateView):
    model = Hall_Booking
    fields = []  # No fields to update through the form
    success_url = reverse_lazy('hall_bookings')  # Replace with your actual URL name for the hall bookings list

    def get_queryset(self):
        owner_queryset = super().get_queryset()
        return owner_queryset.filter(user=self.request.user)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        try:
            booking = self.get_object()
            booking.status = 'cancelled'
            booking.save()

            
            # # Prepare the booking URL and render the cancellation email template
            booking_url = f"{BASE_URL}/hall/my-bookings/"
            html_content = render_to_string('hall/cancellation_email_template.html', {'booking': booking, 'booking_url': booking_url})

            
            # Create the email message with only HTML content
            email = EmailMultiAlternatives(
                subject='Hall Booking Cancellation',
                from_email='adarhotel33@gmail.com',
                to=[booking.user.email]
            )
            # Attach the HTML content
            email.attach_alternative(html_content, "text/html")

            # Send the email
            email.send()

            return HttpResponseRedirect(self.success_url)
        except Exception as e:
            print(f"Exception when canceling hall booking: {e}")
            return HttpResponseBadRequest("Error occurred while canceling the hall booking.")


    def form_invalid(self, form):
        return HttpResponseRedirect(self.success_url)
