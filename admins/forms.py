from django import forms
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from room.models import *
from django import forms
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
        

