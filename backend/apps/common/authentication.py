from rest_framework.authentication import SessionAuthentication, TokenAuthentication

from .workspaces import resolve_workspace


class WorkspaceAuthenticationMixin:
    def authenticate(self, request):
        result = super().authenticate(request)
        if result:
            resolve_workspace(request, user=result[0], required=False)
        return result


class WorkspaceSessionAuthentication(WorkspaceAuthenticationMixin, SessionAuthentication):
    pass


class WorkspaceTokenAuthentication(WorkspaceAuthenticationMixin, TokenAuthentication):
    pass
