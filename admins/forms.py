from django import forms
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from room.models import *
from django import forms
from gym.models import MembershipPlan
from Spa.models import *
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxLengthValidator, MinLengthValidator, RegexValidator


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = Custom_user
        fields = ('username', 'email', 'first_name', 'last_name', 'country', 'phone_number')

class CustomUserChangeForm(UserChangeForm):
    password = forms.CharField(label="Password", required=False, widget=forms.PasswordInput)
    password_confirmation = forms.CharField(label="Password confirmation", required=False, widget=forms.PasswordInput)

    class Meta:
        model = Custom_user
        fields = ('username', 'email', 'first_name', 'last_name', 'country', 'phone_number')

    def clean_password_confirmation(self):
        password = self.cleaned_data.get("password")
        password_confirmation = self.cleaned_data.get("password_confirmation")
        if password and password_confirmation and password != password_confirmation:
            raise forms.ValidationError("Passwords don't match")
        return password_confirmation

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user

class CategoryForm(forms.ModelForm):
    name_regex = RegexValidator(
        regex=r'^[a-zA-Z]{3,10}$',
        message="Name must be 3 to 10 letters long and contain only letters."
    )
    name = forms.CharField(validators=[name_regex])

    class Meta:
        model = Category
        fields = ['name','rank']


    def clean_name(self):
        name = self.cleaned_data.get('name')
        if Category.objects.filter(name=name).exclude(pk=self.instance.pk).exists():
            raise ValidationError("This category name is already exists.")
        return name
    


class RoomForm(forms.ModelForm):
    room_number_regex = RegexValidator(
        regex=r'^[0-9]+$',
        message="Room number must be a positive number"
    )
    room_number = forms.CharField(validators=[room_number_regex])

    def clean_price_per_night(self):
        price_per_night = self.cleaned_data.get('price_per_night')
        if price_per_night < 1:
            raise ValidationError("Price per night must be at least 1.")
        return price_per_night

    def clean_floor(self):
        floor = self.cleaned_data.get('floor')
        if floor < 1:
            raise ValidationError("Floor must be at least 1.")
        return floor

    def clean_discount(self):
        discount = self.cleaned_data.get('discount')
        if discount < 1:
            raise ValidationError("Discount must be at least 1.")
        return discount

    def clean_capacity(self):
        capacity = self.cleaned_data.get('capacity')
        if not 1 <= capacity <= 6:
            raise ValidationError("Capacity must be between 1 and 6.")
        return capacity

    class Meta:
        model = Room
        fields = ['room_number', 'room_type', 'price_per_night', 'discount', 'room_image', 'capacity', 'description', 'floor']    


class BookingUpdateForm(forms.ModelForm):
    checked_in = forms.BooleanField(required=False, widget=forms.CheckboxInput)
    checked_out = forms.BooleanField(required=False, widget=forms.CheckboxInput)
    status = forms.ChoiceField(choices=Booking.STATUS_CHOICES, widget=forms.Select)  # Assuming STATUS_CHOICES is defined in your Booking model

    class Meta:
        model = Booking
        fields = ['checked_in', 'checked_out', 'status','wants_chef']

    def clean(self):
        cleaned_data = super().clean()
        checked_in = cleaned_data.get("checked_in")
        checked_out = cleaned_data.get("checked_out")
        check_in_date = self.instance.check_in_date  
        today = timezone.now().date()

        if checked_in and checked_out:
            raise ValidationError("Both checked in and checked out cannot be true at the same time.")

        if checked_in and check_in_date != today:
            raise ValidationError("You can only check in on the check-in date.")

        return cleaned_data


from django import forms
from room.models import Booking, Room
import re

class BookingCreateForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['room', 'full_name', 'check_in_date', 'check_out_date', 'guests', 'email2', 'wants_chef']
        widgets = {
            'room': forms.Select(attrs={'class': 'form-control rounded'}),
            'check_in_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control rounded'}),
            'check_out_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control rounded'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control rounded'}),
            'guests': forms.NumberInput(attrs={'class': 'form-control rounded'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['room'].queryset = Room.objects.filter(room_status='vacant')  # Filter available rooms
        self.fields['full_name'].validators.append(self.validate_full_name)
        self.fields['guests'].validators.append(self.validate_guests)

    def clean(self):
        cleaned_data = super().clean()
        check_in_date = cleaned_data.get('check_in_date')
        check_out_date = cleaned_data.get('check_out_date')
        room = cleaned_data.get('room')
        guests = cleaned_data.get('guests')

        if check_in_date and check_out_date and room:
            if check_out_date <= check_in_date:
                raise forms.ValidationError("Check-out date must be after check-in date.")
            if guests > room.capacity:
                self.add_error('guests', f"Number of guests cannot exceed room capacity -> {room.capacity}.")
            existing_bookings = Booking.objects.filter(
                room=room,
                status__in=['pending', 'confirmed'],
                check_in_date__lt=check_out_date,
                check_out_date__gt=check_in_date
            )

            if existing_bookings.exists():
                raise ValidationError('The room is booked for the selected dates. Please choose different dates.')
        
        return cleaned_data

    def validate_full_name(self, full_name):
        if len(full_name) > 100:
            raise ValidationError("Full name must not exceed 100 characters.")
        if not re.match("^[a-zA-Z ]*$", full_name):
            raise ValidationError("Full name must only contain letters.")

    def validate_guests(self, guests):
        if guests < 1:
            raise ValidationError("There must be at least one guest.")


class BookingExtendForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['extended_check_out_date']
        widgets = {
            'extended_check_out_date': forms.DateInput(attrs={'type': 'date'})
        }

    def clean_extended_check_out_date(self):
        extended_check_out_date = self.cleaned_data.get('extended_check_out_date')

        if extended_check_out_date:
            # Ensure the extended checkout date is after the current checkout date
            if extended_check_out_date <= self.instance.check_out_date:
                raise forms.ValidationError("Extended checkout date must be after the current checkout date.")

            # Check for overlapping bookings
            overlapping_bookings = Booking.objects.filter(
                room=self.instance.room,
                status__in=['pending', 'confirmed'],
                check_in_date__range=(self.instance.check_out_date, extended_check_out_date)
            ).exclude(id=self.instance.id)

            if overlapping_bookings.exists():
                raise forms.ValidationError("The selected extended checkout date overlaps with an existing booking for the same room.")

        return extended_check_out_date


class PaymentCreateForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['payment_method']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['payment_method'].widget = forms.Select(choices=Payment.PAYMENT_METHOD_CHOICES)



class PaymentExtendForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['payment_method']  

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        

from django import forms
from gym.models import MembershipPlan, Membership, MembershipPayment

class MembershipPlanForm(forms.ModelForm):
    class Meta:
        model = MembershipPlan
        fields = ['name', 'price', 'duration_months', 'description']

    def __init__(self, *args, **kwargs):
        super(MembershipPlanForm, self).__init__(*args, **kwargs)
        self.fields['name'].validators.append(self.validate_name)
        self.fields['price'].validators.append(self.validate_price)
        self.fields['duration_months'].validators.append(self.validate_duration_months)

    def validate_name(self, value):
        if not 3 <= len(value) <= 50:
            raise ValidationError("Name must be between 3 and 50 characters long.")
        if not re.match("^[a-zA-Z0-9 ]*$", value):
            raise ValidationError("Name must only contain letters and numbers.")

    def validate_price(self, value):
        if value < 1:
            raise ValidationError("Price must be at least 1.")

    def validate_duration_months(self, value):
        if value < 1:
            raise ValidationError("Duration in months must be at least 1.")



class MembershipUpdateForm(forms.ModelForm):
    class Meta:
        model = Membership
        fields = ['status']


class MembershipCreateForm(forms.ModelForm):
    plan = forms.ModelChoiceField(queryset=MembershipPlan.objects.all(), required=True)
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    payment_method = forms.ChoiceField(choices=[('cash', 'Cash'),('paypal','Paypal'),('chapa','Chapa')], required=True)
    for_phone_number = forms.CharField(widget=forms.TextInput(attrs={'placeholder': '+2519xxxxxxxx or +2517xxxxxxxx'}))
    for_email = forms.EmailField(required=False)
    class Meta:
        model = Membership
        fields = ['plan', 'start_date', 'for_first_name', 'for_last_name', 'for_phone_number', 'for_email', 'status']

    def clean_start_date(self):
        start_date = self.cleaned_data['start_date']
        if start_date < date.today():
            raise ValidationError("Start date cannot be in the past.")
        return start_date

    def clean_for_first_name(self):
        first_name = self.cleaned_data['for_first_name']
        if not re.match("^[a-zA-Z]{3,20}$", first_name):
            raise ValidationError("First name must be letters only and between 3 and 20 characters.")
        return first_name

    def clean_for_last_name(self):
        last_name = self.cleaned_data['for_last_name']
        if not re.match("^[a-zA-Z]{3,20}$", last_name):
            raise ValidationError("Last name must be letters only and between 3 and 20 characters.")
        return last_name

    def clean_for_phone_number(self):
        phone_number = self.cleaned_data['for_phone_number']
        if not re.match("^\+2519[0-9]{8}$|^\+2517[0-9]{8}$", phone_number):
            raise ValidationError("Phone number must follow the pattern +2519xxxxxxxx or +2517xxxxxxxx.")
        return phone_number




from django import forms
from Hall.models import Hall, Hall_Booking, Hall_Payment
from datetime import timedelta, datetime

class CheckAvailabilityForm(forms.Form):
    hall = forms.ModelChoiceField(queryset=Hall.objects.all(), widget=forms.Select(attrs={'class': 'form-control'}))
    start_date = forms.DateField(widget=forms.TextInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date'}))
    start_time = forms.TimeField(widget=forms.TextInput(attrs={'type': 'time'}))
    end_time = forms.TimeField(widget=forms.TextInput(attrs={'type': 'time'}))

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        hall = cleaned_data.get('hall')

        # Check if start date is in the past
        if start_date and start_date < timezone.now().date():
            raise ValidationError("Start date cannot be in the past.")

        # Check if end date is in the past
        if end_date and end_date < timezone.now().date():
            raise ValidationError("End date cannot be in the past.")

        # Check if end date is before start date
        if end_date and end_date < start_date:
            raise ValidationError("End date cannot be before start date.")

        # Check if end time is before start time when dates are the same
        if end_date == start_date and end_time < start_time:
            raise ValidationError("End time cannot be before start time when start and end dates are the same.")

        # Check if the gap between start time and end time is at least one hour
        if end_date == start_date:
            start_datetime = datetime.combine(start_date, start_time)
            end_datetime = datetime.combine(end_date, end_time)
            if end_datetime - start_datetime < timedelta(hours=1):
                raise ValidationError("The gap between start time and end time must be at least one hour.")

        return cleaned_data

class HallForm(forms.ModelForm):
    class Meta:
        model = Hall
        fields = ['hall_type','capacity', 'price_per_hour', 'description', 'image', 'floor']

    def clean_capacity(self):
        capacity = self.cleaned_data.get('capacity')
        if capacity < 1:
            raise forms.ValidationError("Capacity must be at least 1.")
        return capacity

    def clean_price_per_hour(self):
        price_per_hour = self.cleaned_data.get('price_per_hour')
        if price_per_hour < 1:
            raise forms.ValidationError("Price per hour must be at least 1.")
        return price_per_hour

class HallBookingUpdateForm(forms.ModelForm):
    occupied = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    status = forms.ChoiceField(choices=Hall_Booking.Booking_STATUS_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = Hall_Booking
        fields = ['occupied', 'status','id_image']

    def clean(self):
        cleaned_data = super().clean()
        occupied = cleaned_data.get("occupied")
        status = cleaned_data.get("status")

        if occupied and status == 'cancelled':
            raise forms.ValidationError("Occupied hall cannot have status 'cancelled'.")

        return cleaned_data



class HallBookingForm(forms.ModelForm):
    class Meta:
        model = Hall_Booking
        fields = ['full_name','email2','id_image']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control rounded'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['hall'].queryset = Hall.objects.all()  # Adjust as necessary
        self.fields['full_name'].validators.append(self.validate_full_name)

    def validate_full_name(self, value):
        if not 3 <= len(value) <= 100:
            raise ValidationError("Full name must be between 3 and 100 characters.")
        if not re.match("^[a-zA-Z\s]*$", value):
            raise ValidationError("Full name must only contain letters and spaces.")

    
class HallPaymentForm(forms.ModelForm):
    class Meta:
        model = Hall_Payment
        fields = ['payment_method']


from social_media.models import ChatBot

class ChatBotForm(forms.ModelForm):
    class Meta:
        model = ChatBot
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Type your message here...'}),
        }



class SpaServiceForm(forms.ModelForm):
    name = forms.CharField(
        validators=[
            MinLengthValidator(3),
            MaxLengthValidator(60),
            RegexValidator(regex='^[a-zA-Z ]*$', message='Name must contain only letters and spaces.')
        ]
    )
    price = forms.DecimalField(
        validators=[MinValueValidator(1)]
    )
    description = forms.CharField(
        validators=[
            MinLengthValidator(25),
            MaxLengthValidator(3000)
        ]
    )

    class Meta:
        model = SpaService
        fields = ['name', 'description', 'image', 'price']

class SpaPackageForm(forms.ModelForm):
    name = forms.CharField(
        validators=[
            MinLengthValidator(3),
            MaxLengthValidator(20),
            RegexValidator(regex='^[a-zA-Z ]*$', message='Name must contain only letters and spaces.')
        ]
    )
    price = forms.DecimalField(
        validators=[MinValueValidator(1)]
    )
    description = forms.CharField(
        validators=[
            MinLengthValidator(25),
            MaxLengthValidator(3000)
        ]
    )

    class Meta:
        model = SpaPackage
        fields = ['name', 'description', 'image', 'price']


# Validator for first_name and last_name
name_validator = RegexValidator(r'^[a-zA-Z]{2,15}$', 'Only letters are allowed. Must be 2 to 15 characters long.')

# Validator for phone_number
phone_validator = RegexValidator(r'^\+251(9|7)\d{8}$', 'Phone number must be in the format +2519xxxxxxxx or +2517xxxxxxxx.')


class SpaBookingForm(forms.ModelForm):
    appointment_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    appointment_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))
    for_first_name = forms.CharField(
        required=True,
        validators=[name_validator],
        min_length=2,
        max_length=15
    )
    for_last_name = forms.CharField(
        required=True,
        validators=[name_validator],
        min_length=2,
        max_length=15
    )
    for_email = forms.EmailField(required=True)
    for_phone_number = forms.CharField(
        required=True,
        validators=[phone_validator],
        widget=forms.TextInput(attrs={'placeholder': '+2519xxxxxxxx or +2517xxxxxxxx', 'pattern': r'^\+251(9|7)\d{8}$'})
    )
    payment_method = forms.ChoiceField(choices=[('chapa', 'Chapa'), ('paypal', 'PayPal'),('cash', 'Cash')])

    class Meta:
        model = SpaBooking
        fields = ['service', 'package', 'appointment_date', 'appointment_time', 'for_first_name', 'for_last_name', 'for_email', 'for_phone_number', 'payment_method']

    def clean_appointment_date(self):
        appointment_date = self.cleaned_data.get('appointment_date')
        if appointment_date < timezone.now().date():
            raise ValidationError('The appointment date cannot be in the past.')
        return appointment_date

    def clean_appointment_time(self):
        appointment_time = self.cleaned_data.get('appointment_time')
        appointment_date = self.cleaned_data.get('appointment_date')

        if appointment_date == timezone.now().date() and appointment_time < timezone.now().time():
            raise ValidationError('The appointment time cannot be in the past for today.')

        if not (timezone.datetime.strptime('07:00', '%H:%M').time() <= appointment_time <= timezone.datetime.strptime('21:00', '%H:%M').time()):
            raise ValidationError('The appointment time must be between 7:00 AM and 9:00 PM.')
        
        return appointment_time

    def clean(self):
        cleaned_data = super().clean()
        service = cleaned_data.get('service')
        package = cleaned_data.get('package')

        if service and package:
            raise ValidationError('You cannot select both a service and a package. Please select only one.')

        return cleaned_data

class SpaBookingUpdateForm(forms.ModelForm):
    class Meta:
        model = SpaBooking
        fields = ['status']
