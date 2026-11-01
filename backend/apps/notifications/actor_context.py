"""Request-local actor attribution without retaining users between requests."""

from contextvars import ContextVar

_request = ContextVar("operational_notice_request", default=None)


def current_actor():
    request = _request.get()
    user = getattr(request, "user", None)
    return user if user and user.is_authenticated else None


class NoticeActorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # DRF attaches its authenticated user to this Django request before views
        # write records. Retain the request, rather than an early AnonymousUser.
        token = _request.set(request)
        try:
            return self.get_response(request)
        finally:
            _request.reset(token)
