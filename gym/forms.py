# forms.py
from django import forms
from .models import MembershipPlan
from django import forms
from django.core.validators import RegexValidator

# Validator for first_name and last_name
name_validator = RegexValidator(r'^[a-zA-Z]{2,15}$', 'Only letters are allowed. Must be 2 to 15 characters long.')

# Validator for phone_number
phone_validator = RegexValidator(r'^\+251(9|7)\d{8}$', 'Phone number must be in the format +2519xxxxxxxx or +2517xxxxxxxx.')

class MembershipSignupForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    subscription_for = forms.ChoiceField(choices=[('self', 'Self'), ('others', 'Others')], widget=forms.RadioSelect)
    first_name = forms.CharField(
        required=False,
        validators=[name_validator],
        min_length=2,
        max_length=15
    )
    last_name = forms.CharField(
        required=False,
        validators=[name_validator],
        min_length=2,
        max_length=15
    )
    email = forms.EmailField(required=False)
    phone_number = forms.CharField(
        required=False,
        validators=[phone_validator],
        widget=forms.TextInput(attrs={'placeholder': '+2519xxxxxxxx or +2517xxxxxxxx', 'pattern': r'^\+251(9|7)\d{8}$'})
    )
    payment_method = forms.ChoiceField(choices=[('chapa', 'Chapa'), ('paypal', 'PayPal')])