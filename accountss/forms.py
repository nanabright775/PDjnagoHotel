from django import forms
from django.forms import ModelForm  # Import the ModelForm class
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from accountss.models import Custom_user
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

from django.core.validators import RegexValidator


class CustomUserCreationForm(UserCreationForm):
    username_regex = RegexValidator(
        regex=r'^.{2,10}$',
        message="Username must be 2 to 10 characters long."
    )
    username = forms.CharField(validators=[username_regex])
    name_regex = RegexValidator(
        regex=r'^[a-zA-Z]{2,15}$',
        message="Name must be at least 2 letters and atmost 15 letters long and contain only letters."
    )
    first_name = forms.CharField(validators=[name_regex])
    last_name = forms.CharField(validators=[name_regex])

    class Meta:
        model = Custom_user
        fields = ['username', 'first_name', 'last_name', 'email', 'country', 'profile_picture', 'phone_number']

    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        self.fields['phone_number'].widget = forms.TextInput(attrs={'placeholder': '+2519xxxxxxxx or +2517xxxxxxxx'})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Custom_user.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already in use.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if Custom_user.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already in use.")
        return username
    



class CustomUserUpdateForm(forms.ModelForm):
    username_regex = RegexValidator(
        regex=r'^.{2,15}$',
        message="Username must be 2 to 10 characters long."
    )
    username = forms.CharField(validators=[username_regex])
    name_regex = RegexValidator(
        regex=r'^[a-zA-Z]{2,10}$',
        message="Name must be at least 2 letters and atmost 10 letters long and contain only letters."
    )
    first_name = forms.CharField(validators=[name_regex])
    last_name = forms.CharField(validators=[name_regex])

    class Meta:
        model = Custom_user
        fields = ['username', 'first_name', 'last_name', 'email', 'country',  'profile_picture', 'phone_number']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Custom_user.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("This email address is already in use.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if Custom_user.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise ValidationError("This username is already in use.")
        return username