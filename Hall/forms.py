# forms.py

from django import forms
from .models import Hall_Booking
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone


class BookingForm(forms.ModelForm):
    class Meta:
        model = Hall_Booking
        fields = ['start_date', 'end_date', 'start_time', 'end_time', 'amount_due']  # Adjust fields as necessary
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }


from datetime import timedelta, datetime

class CheckAvailabilityForm(forms.Form):
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