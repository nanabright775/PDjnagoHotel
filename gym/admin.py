from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(MembershipPlan)
admin.site.register(Membership)
admin.site.register(MembershipPayment)