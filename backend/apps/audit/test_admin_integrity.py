import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from .admin import AuditEventAdmin, SupportSessionAdmin
from .models import AuditEvent, SupportSession


@pytest.mark.parametrize("model,admin_class", [
    (AuditEvent, AuditEventAdmin), (SupportSession, SupportSessionAdmin),
])
@pytest.mark.parametrize("superuser", [False, True])
def test_audit_admin_is_view_only_for_staff_and_superusers(model, admin_class, superuser):
    request = RequestFactory().get("/admin/")
    request.user = get_user_model()(is_staff=True, is_superuser=superuser)
    model_admin = admin_class(model, admin.site)
    assert model_admin.has_add_permission(request) is False
    assert model_admin.has_change_permission(request) is False
    assert model_admin.has_delete_permission(request) is False
    assert set(model_admin.get_readonly_fields(request)) == {
        field.name for field in model._meta.fields
    }
    if superuser:
        assert model_admin.has_view_permission(request) is True
