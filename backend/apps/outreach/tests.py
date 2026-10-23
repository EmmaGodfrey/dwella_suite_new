from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.audit.models import AuditEvent

from .models import (
    Contact,
    Enrollment,
    OutreachMessage,
    OutreachSettings,
    Sequence,
    Suppression,
    Template,
)

pytestmark = pytest.mark.django_db
BASE = "/api/v1/platform/outreach/"


def contact(client, **extra):
    response = client.post(
        BASE + "contacts/",
        {
            "name": "Example Contact",
            "first_name": "Example",
            "email": "example@example.com",
            "source": "Public business website",
            "organization": "Example Estates",
            **extra,
        },
        format="json",
    )
    assert response.status_code == 201, response.content
    return response.json()["response_data"]


def enroll(client, person):
    sequence = Sequence.objects.get(name="Agent beta invite")
    response = client.post(
        BASE + "enrollments/",
        {
            "contact": person["id"],
            "sequence": str(sequence.public_id),
        },
        format="json",
    )
    assert response.status_code == 201, response.content
    return response.json()["response_data"]


def approve(client, path):
    preview = client.get(path + "preview/")
    token = (
        preview.json()["response_data"].get("preview_token", "")
        if preview.status_code == 200
        else ""
    )
    return client.post(path + "approve/", {"preview_token": token}, format="json")


@pytest.mark.parametrize("authenticated", [False, True])
@pytest.mark.parametrize(
    "resource",
    ["contacts", "templates", "sequences", "enrollments", "messages", "settings", "summary"],
)
def test_all_outreach_data_requires_platform_staff(authenticated, resource):
    cache.clear()
    client = APIClient()
    if authenticated:
        client.force_authenticate(get_user_model().objects.create_user(username="ordinary-user"))
    assert client.get(BASE + resource + "/").status_code == 403
    assert client.post(BASE + resource + "/", {}, format="json").status_code == 403


def test_contact_validation_search_and_audit_atomicity(staff):
    client, user = staff
    data = contact(client)
    assert AuditEvent.objects.get(action="outreach.contact.created").actor == user
    assert client.post(BASE + "contacts/", {"name": "X"}, format="json").status_code == 400
    assert (
        client.post(
            BASE + "contacts/",
            {
                "name": "Duplicate",
                "source": "Referral",
                "email": "EXAMPLE@example.com",
            },
            format="json",
        ).status_code
        == 400
    )
    assert len(client.get(BASE + "contacts/?search=estates").json()["response_data"]) == 1
    with patch("apps.outreach.views.record_event", side_effect=RuntimeError("Audit failed")):
        with pytest.raises(RuntimeError):
            client.patch(BASE + f"contacts/{data['id']}/", {"name": "Changed"}, format="json")
    assert Contact.objects.get().name == "Example Contact"


@pytest.mark.parametrize(
    "field,value",
    [
        ("email", "invalid"),
        ("source", ""),
        ("tags", {"invalid": "shape"}),
        ("phone", "not-a-number"),
        ("segment", "invented"),
        ("profile_url", "javascript:alert(1)"),
    ],
)
def test_contact_bad_inputs_are_rejected(staff, field, value):
    client, _ = staff
    response = client.post(
        BASE + "contacts/",
        {
            "name": "Example Contact",
            "source": "Referral",
            field: value,
        },
        format="json",
    )
    assert response.status_code == 400
    assert not Contact.objects.exists()


def test_approval_persists_rendered_copy_and_cannot_be_repeated(staff):
    client, _ = staff
    person = contact(client)
    entry = enroll(client, person)
    path = BASE + f"enrollments/{entry['id']}/"
    preview = client.get(path + "preview/")
    assert preview.status_code == 200, preview.content
    assert "Dear Example" in preview.json()["response_data"]["messages"][0]["body"]
    assert approve(client, path).status_code == 200
    assert OutreachMessage.objects.count() == 3
    first = OutreachMessage.objects.get(step=0)
    body = first.body
    Template.objects.filter(
        pk=Sequence.objects.get(name="Agent beta invite").steps.first().template_id
    ).update(body="Changed after approval")
    first.refresh_from_db()
    assert first.body == body
    assert approve(client, path).status_code == 400
    assert (
        client.patch(
            BASE + f"contacts/{person['id']}/",
            {
                "email": "different@example.com",
            },
            format="json",
        ).status_code
        == 400
    )


def test_missing_fields_and_unsafe_merge_syntax_block_render_and_approval(staff):
    client, _ = staff
    person = contact(client, first_name="")
    entry = enroll(client, person)
    path = BASE + f"enrollments/{entry['id']}/"
    assert client.get(path + "preview/").status_code == 400
    assert approve(client, path).status_code == 400
    assert not OutreachMessage.objects.exists()
    for value in ("{first_name.__class__}", "{first_name[0]}", "{missing}", "{first_name!r}", "{"):
        response = client.post(
            BASE + "templates/",
            {
                "name": value,
                "subject": "Subject",
                "body": value,
            },
            format="json",
        )
        assert response.status_code == 400


def test_braces_in_contact_data_render_literally_and_can_be_approved(staff):
    client, _ = staff
    person = contact(client, organization="Acme {Rentals}")
    entry = enroll(client, person)
    path = BASE + f"enrollments/{entry['id']}/"
    line = {"personal_line": "Loved the {offer} post."}
    assert client.patch(path, line, format="json").status_code == 200
    assert approve(client, path).status_code == 200
    first = OutreachMessage.objects.order_by("step").first()
    assert "Acme {Rentals}" in first.subject + first.body
    assert "Loved the {offer} post." in first.body


def test_suppression_survives_deletion_recreation_and_stops_approved_messages(staff):
    client, _ = staff
    person = contact(client)
    entry = enroll(client, person)
    path = BASE + f"enrollments/{entry['id']}/"
    assert approve(client, path).status_code == 200
    cpath = BASE + f"contacts/{person['id']}/"
    assert (
        client.post(cpath + "status/", {"status": "do_not_contact"}, format="json").status_code
        == 200
    )
    assert Enrollment.objects.get().status == "stopped_optout"
    assert client.post(path + "state/", {"action": "resume"}, format="json").status_code == 400
    assert (
        client.post(cpath + "status/", {"status": "interested"}, format="json").status_code == 400
    )
    assert client.delete(cpath).status_code == 204
    assert Suppression.objects.count() == 1
    recreated = contact(client)
    assert recreated["suppressed"] is True
    sequence = Sequence.objects.first()
    assert (
        client.post(
            BASE + "enrollments/",
            {
                "contact": recreated["id"],
                "sequence": str(sequence.public_id),
            },
            format="json",
        ).status_code
        == 400
    )


def test_reply_pause_stop_and_invalid_actions(staff):
    client, _ = staff
    person = contact(client)
    entry = enroll(client, person)
    path = BASE + f"enrollments/{entry['id']}/"
    approve(client, path)
    for command in ("pause", "resume", "send_next"):
        assert client.post(path + "state/", {"action": command}, format="json").status_code == 200
    assert client.post(path + "state/", {"action": "invalid"}, format="json").status_code == 400
    assert (
        client.post(
            BASE + f"contacts/{person['id']}/status/",
            {
                "status": "replied",
            },
            format="json",
        ).status_code
        == 200
    )
    assert Enrollment.objects.get().status == "stopped_reply"
    assert client.post(path + "state/", {"action": "send_next"}, format="json").status_code == 400


def test_csv_preview_confirm_replay_and_tampering(staff):
    client, _ = staff
    content = (
        "full_name,business_email,source\nExample,one@example.com,Referral\n"
        "Duplicate,one@example.com,Referral\nBad,not-email,Website\nNo email,,Referral"
    )
    response = client.post(
        BASE + "contacts/import-preview/",
        {
            "csv": content,
            "mapping": {"name": "full_name", "email": "business_email", "source": "source"},
        },
        format="json",
    )
    assert response.status_code == 200, response.content
    preview = response.json()["response_data"]
    assert preview["ready"] == 2
    assert [r["status"] for r in preview["rows"]] == ["ready", "duplicate", "invalid", "ready"]
    assert not Contact.objects.exists()
    path = BASE + "contacts/import-confirm/"
    assert (
        client.post(
            path, {"preview_token": preview["preview_token"] + "x"}, format="json"
        ).status_code
        == 400
    )
    assert (
        client.post(path, {"preview_token": preview["preview_token"]}, format="json").json()[
            "response_data"
        ]["created"]
        == 2
    )
    assert (
        client.post(path, {"preview_token": preview["preview_token"]}, format="json").status_code
        == 400
    )
    assert Contact.objects.count() == 2


def test_bulk_approval_rolls_back_when_any_selected_message_is_blocked(staff):
    client, _ = staff
    first = enroll(client, contact(client))
    second = enroll(
        client, contact(client, name="Other Example", email="other@example.com", first_name="")
    )
    response = client.post(
        BASE + "enrollments/approve-many/",
        {
            "ids": [first["id"], second["id"]],
            "tokens": {first["id"]: first["review"]["preview_token"]},
        },
        format="json",
    )
    assert response.status_code == 400
    assert not OutreachMessage.objects.exists()
    assert not Enrollment.objects.exclude(status="pending_review").exists()


def test_settings_boundaries_and_seed_preserves_edits(staff):
    client, _ = staff
    for payload in (
        {"daily_cap": 0},
        {"daily_cap": 100},
        {"send_from_hour": 17},
        {"send_until_hour": 8},
    ):
        assert client.patch(BASE + "settings/", payload, format="json").status_code == 400
    template = Template.objects.first()
    template.body = "Admin edited template"
    template.save()
    call_command("seed_outreach_templates", verbosity=0)
    template.refresh_from_db()
    assert template.body == "Admin edited template"
    assert Sequence.objects.count() == 3


def test_outreach_mutations_are_throttled(staff):
    client, _ = staff
    for _ in range(20):
        assert client.post(BASE + "contacts/", {}, format="json").status_code == 400
    assert client.post(BASE + "contacts/", {}, format="json").status_code == 429


def test_approval_refuses_missing_stale_or_tampered_preview(staff):
    client, _ = staff
    entry = enroll(client, contact(client))
    path = BASE + f"enrollments/{entry['id']}/"
    token = entry["review"]["preview_token"]
    for body in ({}, {"preview_token": token + "x"}):
        assert client.post(path + "approve/", body, format="json").status_code == 400
    OutreachSettings.objects.filter(pk=1).update(signature="Changed since preview")
    assert (
        client.post(path + "approve/", {"preview_token": token}, format="json").status_code == 400
    )
    assert not OutreachMessage.objects.exists()
    assert approve(client, path).status_code == 200


def test_invalid_json_shape_and_sequence_steps_are_rejected(staff):
    client, _ = staff
    assert client.post(BASE + "contacts/", [], format="json").status_code == 400
    assert (
        client.post(BASE + "sequences/", {"name": "Empty", "steps": []}, format="json").status_code
        == 400
    )


def test_checkin_first_delay_is_preserved_on_approval(staff):
    client, _ = staff
    person = contact(client)
    sequence = Sequence.objects.get(name="Early tester check-ins")
    response = client.post(
        BASE + "enrollments/",
        {
            "contact": person["id"],
            "sequence": str(sequence.public_id),
        },
        format="json",
    )
    path = BASE + f"enrollments/{response.json()['response_data']['id']}/"
    assert approve(client, path).status_code == 200
    obj = Enrollment.objects.get()
    assert (obj.next_send_at - obj.created_at).days == 3
