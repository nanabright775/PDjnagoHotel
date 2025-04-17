class TemplateMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if request.user.role == 'customer':
                request.template_name = 'accountss/base.html'
            elif request.user.role == 'owner':
                request.template_name = 'admins/base.html'
        
        response = self.get_response(request)
        return response