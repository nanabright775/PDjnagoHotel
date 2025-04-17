from django.db import models
from django.db import models
from accountss.models import Custom_user

class SpaService(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='media/', blank=True, null=True) 
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

class SpaPackage(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='media/', blank=True, null=True) 
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

class SpaBooking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    )
    user = models.ForeignKey(Custom_user, on_delete=models.CASCADE, null=True, blank=True)
    service = models.ForeignKey(SpaService, null=True, blank=True, on_delete=models.SET_NULL)
    package = models.ForeignKey(SpaPackage, null=True, blank=True, on_delete=models.SET_NULL)
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    tx_ref = models.CharField(max_length=100, unique=True, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    for_first_name = models.CharField(max_length=100, null=True, blank=True)
    for_last_name = models.CharField(max_length=100, null=True, blank=True)
    for_phone_number = models.CharField(max_length=20, null=True, blank=True)
    for_email = models.EmailField(null=True, blank=True)


    def __str__(self):
        user_display = self.user.username if self.user else self.for_first_name
        service_or_package = self.service if self.service else self.package
        return f"{user_display} - {service_or_package} on {self.appointment_date} at {self.appointment_time}"


class SpaPayment(models.Model):
    PAYMENT_METHOD_CHOICES = (
        ('chapa', 'Chapa'),
        ('paypal', 'PayPal'),
        ('cash', 'Cash'),
    )
    spa_booking = models.OneToOneField(SpaBooking, on_delete=models.CASCADE)
    payment_date = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=100)
    receipt_pdf = models.FileField(upload_to='media/receipts/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='chapa')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending')

    def __str__(self):
        user_display = self.spa_booking.user.username if self.spa_booking.user else self.spa_booking.full_name
        service_or_package = self.spa_booking.service.name if self.spa_booking.service else self.spa_booking.package.name
        return f"Payment for {user_display} - {service_or_package}"
