from apps.common.managers import OrganizationScopedManager, OrganizationScopedQuerySet


class PropertyQuerySet(OrganizationScopedQuerySet):
    def managed(self):
        return self.filter(management_status="managed")


class PropertyManager(OrganizationScopedManager.from_queryset(PropertyQuerySet)):
    pass
