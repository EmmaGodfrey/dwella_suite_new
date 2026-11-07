from django.conf import settings
from django.http import HttpResponseNotFound


class NativeAdminBoundaryMiddleware:
    """Native Django admin is an explicit local/operator tool, separate from the SPA."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not settings.NATIVE_ADMIN_ENABLED and (
            request.path_info == '/admin' or request.path_info.startswith('/admin/')
        ):
            return HttpResponseNotFound()
        return self.get_response(request)


class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault("Content-Security-Policy", settings.CONTENT_SECURITY_POLICY)
        response.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        return response
