import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from rest_framework.test import APIClient

from .models import BetaApplication, BetaEmail

URL = "/api/v1/marketing/beta-applications/"
ADMIN_URL = "/api/v1/marketing/admin/beta-applications/"
PAYLOAD = {
    "name": "Synthetic applicant",
    "phone": "+260971000000",
    "email": "signup-role@example.com",
    "units": "1-5",
}


@pytest.fixture(autouse=True)
def clear_request_throttles():
    cache.clear()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role", [None, "Landlord", "Agent", "Property manager", "system_admin", "Tenant"]
)
def test_public_signup_always_assigns_property_manager(settings, role):
    settings.BETA_EMAILS_ENABLED = False
    payload = {**PAYLOAD, **({"role": role} if role is not None else {})}
    response = APIClient().post(URL, payload, format="json")
    assert response.status_code == 201
    assert BetaApplication.objects.get().role == "Property manager"
    assert not get_user_model().objects.exists()
    assert not BetaEmail.objects.exists()


@pytest.mark.django_db
def test_admin_create_and_update_cannot_choose_another_signup_role(settings):
    settings.BETA_EMAILS_ENABLED = False
    admin = get_user_model().objects.create_superuser(
        username="role-admin", email="role-admin@example.com", password="StrongerPass123"
    )
    client = APIClient()
    client.force_authenticate(admin)
    response = client.post(
        ADMIN_URL, {**PAYLOAD, "role": "Agent", "send_welcome": False}, format="json"
    )
    assert response.status_code == 201
    application = BetaApplication.objects.get()
    assert response.json()["response_data"]["role"] == "Property manager"
    response = client.patch(
        f"{ADMIN_URL}{application.pk}/",
        {"role": "Landlord", "status": "contacted"},
        format="json",
    )
    assert response.status_code == 200
    application.refresh_from_db()
    assert application.role == "Property manager"
    assert application.status == "contacted"
    assert not BetaEmail.objects.exists()


@pytest.mark.django_db
def test_database_rejects_other_beta_roles():
    with pytest.raises(IntegrityError), transaction.atomic():
        BetaApplication.objects.create(**PAYLOAD, role="Agent")


@pytest.mark.django_db(transaction=True)
def test_role_migration_normalizes_existing_signups_without_changing_follow_up():
    executor = MigrationExecutor(connection)
    latest = executor.loader.graph.leaf_nodes()
    previous = [("marketing", "0003_beta_email_sequence")]
    try:
        executor.migrate(previous)
        state = executor.loader.project_state(previous).apps
        application_model = state.get_model("marketing", "BetaApplication")
        email_model = state.get_model("marketing", "BetaEmail")
        for role in ("Landlord", "Agent", "Property manager"):
            application_model.objects.create(
                **{**PAYLOAD, "email": f"{role.replace(' ', '-')}@example.com"},
                role=role, status="accepted", internal_notes="Keep follow-up",
            )
        application = application_model.objects.order_by("pk").first()
        email_model.objects.create(
            application_id=application.pk, kind="welcome", sent_at=application.created_at
        )
        original = list(application_model.objects.order_by("pk").values(
            "pk", "name", "email", "status", "internal_notes", "created_at", "updated_at"
        ))
        MigrationExecutor(connection).migrate(latest)
        assert set(BetaApplication.objects.values_list("role", flat=True)) == {"Property manager"}
        assert list(BetaApplication.objects.order_by("pk").values(
            "pk", "name", "email", "status", "internal_notes", "created_at", "updated_at"
        )) == original
        assert BetaEmail.objects.filter(application_id=application.pk, kind="welcome").count() == 1
    finally:
        MigrationExecutor(connection).migrate(latest)
