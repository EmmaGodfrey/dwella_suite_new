import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.accounts.access_state import require_new_account_verification
from apps.documents.tests import member
from apps.organizations.models import Organization

pytestmark = pytest.mark.django_db


def queries_on(client, url, table):
    with CaptureQueriesContext(connection) as captured:
        response = client.get(url)
    return response, sum(f'FROM "{table}"' in q["sql"] for q in captured.captured_queries)


def test_access_state_and_membership_are_read_once_per_request():
    org = Organization.objects.create(name="Kafue Ridge Properties")
    _, client = member(org)
    response, states = queries_on(client, "/api/v1/properties/", "accounts_accountaccessstate")
    assert response.status_code == 200
    assert states == 1
    _, memberships = queries_on(
        client, "/api/v1/properties/", "organizations_organizationmembership"
    )
    assert memberships == 1


def test_each_request_still_sees_a_new_verification_requirement():
    org = Organization.objects.create(name="Kafue Ridge Properties")
    user, client = member(org)
    assert client.get("/api/v1/properties/").status_code == 200
    require_new_account_verification(user)
    response = client.get("/api/v1/properties/")
    assert response.status_code == 403
    assert "email_verification_required" in response.content.decode()
