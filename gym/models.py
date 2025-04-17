from django.db import models
from dateutil.relativedelta import relativedelta
from django.db import models
from accountss.models import *
from django.urls import reverse

# Create your models here.
class MembershipPlan(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_months = models.PositiveIntegerField()  # Duration of the plan in months
    description = models.TextField()

    def __str__(self):
        return self.name

class Membership(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
    ]
    user = models.ForeignKey(Custom_user, on_delete=models.CASCADE,null=True, blank=True)
    plan = models.ForeignKey(MembershipPlan, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    tx_ref = models.CharField(max_length=100, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Additional field to track when the membership was created
    for_first_name = models.CharField(max_length=100, null=True, blank=True)
    for_last_name = models.CharField(max_length=100, null=True, blank=True)
    for_phone_number = models.CharField(max_length=20, null=True, blank=True)
    for_email = models.EmailField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.end_date:
            self.end_date = self.start_date + relativedelta(months=self.plan.duration_months)
        super().save(*args, **kwargs)

    def __str__(self):
        if self.user:
            user_display = self.user.username
        else:
            user_display = f"{self.for_first_name} {self.for_last_name}"
        return f"{user_display} - {self.plan.name}"

class MembershipPayment(models.Model):
    PAYMENT_METHOD_CHOICES = (
        ('chapa', 'Chapa'),
        ('paypal', 'PayPal'),
        ('cash', 'Cash'),
    )
    membership = models.OneToOneField(Membership, on_delete=models.CASCADE)
    payment_date = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=100)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='chapa')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    receipt_pdf = models.FileField(upload_to='media/receipts/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending')

    def __str__(self):
        if self.membership.user:
            user_display = self.membership.user.username
        else:
            user_display = f"{self.membership.for_first_name} {self.membership.for_last_name}"
        return f"Payment for {user_display} - {self.membership.plan.name}"
    

    