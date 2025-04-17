# urls.py
from django.urls import path
from .views import *

urlpatterns = [
    path('membership-plans/', MembershipPlanListView.as_view(), name='membership_plans'),
    path('membership-signup/<int:plan_id>/', MembershipSignupView.as_view(), name='membership_signup'),
    path('paypal-return/', PayPalReturnView.as_view(), name='paypal_return'),
    path('paypal-cancel/', PayPalCancelView.as_view(), name='paypal_cancel'),
    path('my-memberships/', MyMembershipsView.as_view(), name='my_memberships'),
    path('cancel-membership/<int:membership_id>/', CancelMembershipView.as_view(), name='cancel_membership'),

]
