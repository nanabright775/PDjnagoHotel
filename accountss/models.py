from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils.translation import gettext as _
from django_countries.fields import CountryField

class Custom_user(AbstractUser):
    ROLE_CHOICES = (
        ('owner', 'Owner'),
        ('manager', 'Manager'),
        ('customer', 'Customer'),
        ('admin', 'Admin'),
        ('receptionist', 'Receptionist'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    first_login = models.BooleanField(default=True)
    email = models.EmailField(unique=True)
    last_login = models.DateTimeField(null=True, blank=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    telegram_user_id = models.CharField(max_length=100, null=True, blank=True)
    country = CountryField(blank_label='(select country)', default='ET')
    profile_picture = models.ImageField(upload_to='media',blank=True, null=True)

    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="custom_user_set",  # Add this line
        related_query_name="user",
    )

    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="custom_user_set",  # Add this line
        related_query_name="user",
    )
    
    phone_number = models.CharField(max_length=20, validators=[
        RegexValidator(
            regex=r'^\+251(9|7)\d{8}$',
            message="Phone number must be in the format '+2519xxxxxxxx' or '+2517xxxxxxxx'.",
        ),
    ], help_text="Enter phone number in the format '+2519xxxxxxxx' or '+2517xxxxxxxx'.")

    
    def save(self, *args, **kwargs):
        if self.role == 'owner':
            self.is_superuser = True
            self.is_staff = True
        super().save(*args, **kwargs)
    def __str__(self):
        return self.username    
    class Meta:
        app_label = 'accountss' 


class Language(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)