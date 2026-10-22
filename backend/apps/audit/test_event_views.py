import csv
from io import StringIO
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model

from .models import AuditEvent

pytestmark = pytest.mark.django_db
URL = "/api/v1/platform/audit-events/"


def test_audit_filters_details_and_csv_are_authoritative(context):
    client, actor, org, other = context
    session = str(uuid4())
    event = AuditEvent.objects.create(actor=actor, organization=org, action="support.create",
        resource_type="properties.property", resource_id="record", request_id="request-123",
        metadata={"support_session": session, "reason": '=HYPERLINK("unsafe")'})
    AuditEvent.objects.create(organization=other, action="unrelated")
    query = f"?actor={actor.pk}&workspace={org.public_id}&support_session={session}"
    data = client.get(URL + query).json()["response_data"]
    assert len(data) == 1 and data[0]["id"] == str(event.public_id)
    assert client.get(URL + f"{event.public_id}/").status_code == 200
    exported = client.get(URL + "export/" + query)
    assert exported.status_code == 200
    rows = list(csv.reader(StringIO(exported.content.decode("utf-8-sig"))))
    assert len(rows) == 2 and rows[1][-2].startswith("'=")
    assert rows[1][-1] == "request-123"
    assert exported["Cache-Control"] == "private, no-store"
    for filters in ["actor=bad", "workspace=bad", "support_session=bad", "date_from=bad",
                    "date_from=2026-10-22&date_to=2025-01-01"]:
        assert client.get(URL + "?" + filters).status_code == 400
        assert client.get(URL + "export/?" + filters).status_code == 400
    assert client.post(URL, {}, format="json").status_code == 405


@pytest.mark.parametrize("authenticated", [False, True])
@pytest.mark.parametrize("suffix", ["", "{id}/", "export/"])
def test_audit_and_csv_are_staff_only(context, authenticated, suffix):
    client, _, _, _ = context
    user = get_user_model().objects.create_user(username="not-admin")
    event = AuditEvent.objects.create(action="private")
    client.force_authenticate(user if authenticated else None)
    assert client.get(URL + suffix.format(id=event.public_id)).status_code == 403
