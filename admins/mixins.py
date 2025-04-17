from django.http import HttpResponse
from django.shortcuts import redirect
from django.contrib.auth.mixins import AccessMixin

class OwnerRequiredMixin(AccessMixin):

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not hasattr(request.user, 'role') or request.user.role != 'owner':
            return self.handle_no_permission_with_redirect(request)
        return super().dispatch(request, *args, **kwargs)

    def handle_no_permission_with_redirect(self, request):
        response = HttpResponse(
            f"Permission denied. <a href='{request.META.get('HTTP_REFERER', '/')}'>Go back</a>"
        )
        response.status_code = 403
        return response

class CustomerRequiredMixin(AccessMixin):

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not hasattr(request.user, 'role') or request.user.role != 'customer':
            return self.handle_no_permission_with_redirect(request)
        return super().dispatch(request, *args, **kwargs)

    def handle_no_permission_with_redirect(self, request):
        response = HttpResponse(
            f"Permission denied. <a href='{request.META.get('HTTP_REFERER', '/')}'>Go back</a>"
        )
        response.status_code = 403
        return response


class OwnerOrManagerRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if hasattr(request.user, 'role') and (request.user.role == 'owner' or request.user.role == 'manager'):
            return super().dispatch(request, *args, **kwargs)
        else:
            return self.handle_no_permission_with_redirect(request)

    def handle_no_permission_with_redirect(self, request):
        response = HttpResponse(
            f"Permission denied. <a href='{request.META.get('HTTP_REFERER', '/')}'>Go back</a>"
        )
        response.status_code = 403
        return response
    
class OwnerManagerOrReceptionistRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if hasattr(request.user, 'role') and request.user.role in ['owner', 'manager', 'receptionist']:
            return super().dispatch(request, *args, **kwargs)
        else:
            return self.handle_no_permission_with_redirect(request)

    def handle_no_permission_with_redirect(self, request):
        response = HttpResponse(
            f"Permission denied. <a href='{request.META.get('HTTP_REFERER', '/')}'>Go back</a>"
        )
        response.status_code = 403
        return response    