from django.db import models


class ActiveQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)


class OrganizationScopedQuerySet(ActiveQuerySet):
    def for_organization(self, organization):
        if organization is None:
            return self.none()
        return self.filter(organization=organization)

    def for_request(self, request):
        """Rows in the request's workspace that its property scope allows."""
        from .property_scope import scoped

        return scoped(request, self)


class ActiveManager(models.Manager.from_queryset(ActiveQuerySet)):
    pass


class OrganizationScopedManager(models.Manager.from_queryset(OrganizationScopedQuerySet)):
    pass
