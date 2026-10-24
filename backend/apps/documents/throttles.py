from rest_framework.throttling import SimpleRateThrottle, UserRateThrottle

from .rendering import digest


class DocumentWriteThrottle(UserRateThrottle):
    scope = "document_write"
    rate = "30/hour"


class DocumentRenderThrottle(UserRateThrottle):
    scope = "document_render"
    rate = "120/hour"


class SigningIPThrottle(SimpleRateThrottle):
    rate = "150/hour"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": "signing_ip", "ident": self.get_ident(request)}


class SigningLinkThrottle(SimpleRateThrottle):
    rate = "120/hour"

    def allow_request(self, request, view):
        operation = view.kwargs.get("operation", "")
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
