from django.contrib.auth.views import LoginView
from django.urls import reverse
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import DetailView, UpdateView
from django.views.generic.edit import CreateView
from accountss.forms import *

from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate, login
from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth import login
from django.contrib import messages
from django.urls import reverse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str,DjangoUnicodeDecodeError
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model, login
from config import BASE_URL
from django.contrib.auth import update_session_auth_hash
from django.http import HttpResponse
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash, logout


from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.hashers import make_password
from .models import Custom_user

# class CustomUserAdmin(UserAdmin):
#     model = Custom_user

#     def save_model(self, request, obj, form, change):
#         if form.cleaned_data['password']:
#             obj.password = make_password(form.cleaned_data['password'])
#         super().save_model(request, obj, form, change)

# # Modify this instead of registering again
# admin.site.unregister(Custom_user)  # If needed, to clear the existing registration
# admin.site.register(Custom_user, CustomUserAdmin)





from django.utils import timezone  

class CustomLoginView(LoginView):
    template_name = 'accountss/login.html'
    
    def get_success_url(self):
        user = self.request.user
        if not user.is_active:
            messages.error(self.request, 'Please verify your email address to complete the login.')
            return redirect('login')
        if user.first_login and user.role == 'customer':
            user.first_login = False
            user.save()
            update_session_auth_hash(self.request, user)  # Update the session, because the backend hashes some of the user session data.
            messages.info(self.request, 'Please complete your profile.')
            return reverse_lazy('profile_update', kwargs={'pk': user.pk})
        elif user.role == 'owner' or user.role == 'manager' or user.role == 'receptionist':
            return reverse_lazy('admins:admin_dashboard')
        elif user.role == 'admin':
            return reverse_lazy('admin:index')
        else:  
            return reverse_lazy('home')

    def form_invalid(self, form):
        messages.error(self.request, "Invalid username or password")
        return super().form_invalid(form)

    def form_valid(self, form):
        user = form.get_user()
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        return super().form_valid(form)



        
from .tokens import account_activation_token

class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'accountss/signup.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        user = form.save(commit=False)
        if user.role == 'customer':  # Assuming 'customer' is the role name
            user.is_active = False
            user.save()
            self.send_verification_email(user)
            messages.success(self.request, 'Please verify your email address to complete the registration.')
        else:
            user.is_active = True
            user.save()
        return super().form_valid(form)

    def send_verification_email(self, user):
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        activate_url = f"{BASE_URL}{reverse_lazy('activate', kwargs={'uidb64': uidb64, 'token': account_activation_token.make_token(user)})}"
        subject = 'Activate your account'
        html_content = render_to_string('accountss/acc_active_email.html', {
            'user': user,
            'activate_url': activate_url,
        })

        email = EmailMultiAlternatives(
            subject=subject,
            body='Activation link',
            from_email='adarhotel33@gmail.com',
            to=[user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Custom_user.objects.get(pk=uid)
    except (DjangoUnicodeDecodeError, TypeError, ValueError, OverflowError, Custom_user.DoesNotExist) as e:
        user = None
        print(f"Error decoding UID: {e}")
    
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Your account has been activated successfully.')
        return redirect('login')
    else:
        return HttpResponse('Activation link is invalid!')


def home(request):
    return render(request, 'room/home.html')


from django.contrib.auth.views import LogoutView

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('login')
    template_name = None



class ProfileDetailView(LoginRequiredMixin,DetailView):
    model = Custom_user
    template_name = 'accountss/profile_detail.html'
    context_object_name = 'profile'
    

class ProfileUpdateView(LoginRequiredMixin,UpdateView):
    model = Custom_user
    form_class = CustomUserUpdateForm
    template_name = 'accountss/profile_update.html'
    

    def get_success_url(self):
        user = self.request.user
        user.first_login = False
        return reverse_lazy('profile_detail', kwargs={'pk': self.object.pk})
    



class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = 'accountss/change_password.html'
    form_class = PasswordChangeForm
    
    def get_success_url(self):
        return reverse_lazy('login')

    def form_valid(self, form):
        user = form.save()
        update_session_auth_hash(self.request, user)  # Important, to update the session with the new password
        logout(self.request)
        return super().form_valid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.user = self.request.user
        return form
