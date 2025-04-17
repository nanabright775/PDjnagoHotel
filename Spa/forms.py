from django import forms
from django.core.validators import RegexValidator
from .models import SpaBooking
from django.core.exceptions import ValidationError
from django.utils import timezone

# Validator for first_name and last_name
name_validator = RegexValidator(r'^[a-zA-Z]{2,15}$', 'Only letters are allowed. Must be 2 to 15 characters long.')

# Validator for phone_number
phone_validator = RegexValidator(r'^\+251(9|7)\d{8}$', 'Phone number must be in the format +2519xxxxxxxx or +2517xxxxxxxx.')

from django.utils import timezone
from django.core.exceptions import ValidationError

class SpaBookingForm(forms.ModelForm):
    appointment_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    appointment_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))
    for_first_name = forms.CharField(
        required=False,
        validators=[name_validator],
        min_length=2,
        max_length=15
    )
    for_last_name = forms.CharField(
        required=False,
        validators=[name_validator],
        min_length=2,
        max_length=15
    )
    for_email = forms.EmailField(required=False)
    for_phone_number = forms.CharField(
        required=False,
        validators=[phone_validator],
        widget=forms.TextInput(attrs={'placeholder': '+2519xxxxxxxx or +2517xxxxxxxx', 'pattern': r'^\+251(9|7)\d{8}$'})
    )
    booking_for = forms.ChoiceField(choices=[('self', 'For Self'), ('others', 'For Others')], widget=forms.RadioSelect)
    payment_method = forms.ChoiceField(choices=[('chapa', 'Chapa'), ('paypal', 'PayPal')])

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
        booking_for = self.data.get('booking_for')
        
        if not booking_for:
            self.add_error('booking_for', 'This field is required.')
        
        if booking_for == 'others':
            if not cleaned_data.get('for_first_name'):
                self.add_error('for_first_name', 'This field is required for booking for others.')
            if not cleaned_data.get('for_last_name'):
                self.add_error('for_last_name', 'This field is required for booking for others.')
            if not cleaned_data.get('for_email'):
                self.add_error('for_email', 'This field is required for booking for others.')
            if not cleaned_data.get('for_phone_number'):
                self.add_error('for_phone_number', 'This field is required for booking for others.')

        return cleaned_data