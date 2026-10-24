from .services import require_feature


class FeatureAccessMixin:
    """Supplement existing authentication/role checks; never replace them."""

    required_feature = None
    feature_actions = {}

    def check_permissions(self, request):
        super().check_permissions(request)
        feature = self.feature_actions.get(getattr(self, "action", None), self.required_feature)
        if feature:
            require_feature(self.get_organization(), feature)
