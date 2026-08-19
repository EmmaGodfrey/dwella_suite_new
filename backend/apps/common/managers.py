from django.db import models


class ActiveQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)


class OrganizationScopedQuerySet(ActiveQuerySet):
    def for_organization(self, organization):
        if organization is None:
            return self.none()
        return self.filter(organization=organization)


class ActiveManager(models.Manager.from_queryset(ActiveQuerySet)):
    pass


class OrganizationScopedManager(models.Manager.from_queryset(OrganizationScopedQuerySet)):
    pass
