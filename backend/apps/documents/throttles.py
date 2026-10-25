from django.core.cache import cache
from rest_framework.throttling import SimpleRateThrottle, UserRateThrottle

from .rendering import digest

PAGE_CACHE_SECONDS = 7 * 24 * 60 * 60


def page_cache_key(sha256, page):
    return f"document-page:{sha256}:{page}"


def page_is_cached(request):
    # Only renders cost a PDF worker; serving a saved page image does not.
    sha256, page = request.query_params.get("sha256", ""), request.query_params.get("page", "1")
    return len(sha256) == 64 and page.isdigit() and cache.has_key(page_cache_key(sha256, int(page)))


class DocumentWriteThrottle(UserRateThrottle):
    scope = "document_write"
    rate = "30/hour"


class DocumentRenderThrottle(UserRateThrottle):
    scope = "document_render"
    rate = "120/hour"

    def allow_request(self, request, view):
        return page_is_cached(request) or super().allow_request(request, view)


class SigningIPThrottle(SimpleRateThrottle):
    rate = "150/hour"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": "signing_ip", "ident": self.get_ident(request)}


class SigningLinkThrottle(SimpleRateThrottle):
    rate = "120/hour"

    def allow_request(self, request, view):
        operation = view.kwargs.get("operation", "")
        if operation == "page" and page_is_cached(request):
            return True
        self.rate = {
            "request-code": "5/hour",
            "verify": "12/hour",
            "sign": "10/hour",
            "source-preview": "20/hour",
        }.get(operation, "120/hour")
        self.num_requests, self.duration = self.parse_rate(self.rate)
        return super().allow_request(request, view)

    def get_cache_key(self, request, view):
        key = digest(str(view.kwargs.get("token", "")).encode())
        return self.cache_format % {
            "scope": f"signing_{view.kwargs.get('operation')}",
            "ident": key,
        }
