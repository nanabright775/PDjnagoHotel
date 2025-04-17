from django import forms
from .models import Booking, Payment, RoomRating
from datetime import date
from django import forms
from .models import Booking
from django.utils import timezone
from django.core.exceptions import ValidationError

class BookingExtendForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['extended_check_out_date']
        widgets = {
            'extended_check_out_date': forms.DateInput(attrs={'type': 'date'}),
        }


class BookingForm(forms.ModelForm):

    MEAL_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('supper', 'Supper'),
    ]

    meal_preferences = forms.MultipleChoiceField(
        choices=MEAL_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )


    def __init__(self, *args, **kwargs):
        self.room = kwargs.pop('room', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = Booking
        fields = ['full_name', 'phone_number', 'check_in_date', 'email2', 'wants_chef','check_out_date', 'guests', 'wants_cooking_service', 'meal_preferences', 'wants_cleaning_service']
        widgets = {
            'check_in_date': forms.DateInput(attrs={'type': 'date'}),
            'check_out_date': forms.DateInput(attrs={'type': 'date'}),
        }

    #cleaning the data preferences
    def clean_meal_preferences(self):
        return ','.join(self.cleaned_data['meal_preferences'])

    def clean_guests(self):
        guests = self.cleaned_data.get('guests')
        room_capacity = self.room.capacity

        if guests < 1:
            raise ValidationError('The number of guests must be at least 1.')
        elif guests > room_capacity:
            raise ValidationError(f'The number of guests cannot exceed the room capacity which is {self.room.capacity} for this room.')

        return guests

    def clean_check_in_date(self):
        check_in_date = self.cleaned_data.get('check_in_date')
        if check_in_date < timezone.now().date():
            raise ValidationError('Check-in date cannot be in the past.')
        return check_in_date

    def clean(self):
        cleaned_data = super().clean()
        check_in_date = cleaned_data.get('check_in_date')
        check_out_date = cleaned_data.get('check_out_date')

        if check_in_date and check_out_date:
            if check_out_date <= check_in_date:
                raise ValidationError('Check-out date must be after the check-in date.')

            # Check for room availability
            existing_bookings = Booking.objects.filter(
                room=self.room,
                status__in=['pending', 'confirmed'],
                check_in_date__lt=check_out_date,
                check_out_date__gt=check_in_date
            )

            if existing_bookings.exists():
                raise ValidationError('The room is booked for the selected dates. Please choose different dates.')

        return cleaned_data

        

class RoomRatingForm(forms.ModelForm):
    class Meta:
        model = RoomRating
        fields = ['rating', 'review']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'review': forms.Textarea(attrs={'rows': 4}),
        }
