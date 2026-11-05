"""Requested documents, confirmed repair photos and one-invoice reminder journeys."""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core.files.storage import default_storage
from django.db import connection
from django.utils import timezone

from apps.maintenance.models import MaintenancePhoto, MaintenanceRequest
from apps.organizations.models import OrganizationMembership

from . import test_whatsapp as base
from .test_whatsapp import PHONE, choose, step, workspace
from .test_whatsapp_proof import META, attachment, png
from .whatsapp.access import revoke
from .whatsapp.media import cleanup_media, fetch_media
from .whatsapp.models import WhatsAppBinding, WhatsAppConversation, WhatsAppMedia, WhatsAppReply
from .whatsapp.worker import process_inbox

pytestmark = pytest.mark.django_db(transaction=True)
config = base.config
house = base.house


@pytest.fixture(autouse=True)
def private_files(settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path / "photos")


def repair_draft(house):
    menu = workspace(house)
    reply = step(token=choose(menu, "Report a repair"))
    step(token=reply.view["options"][0]["id"])
    step("Leaking tap")
    reply = step("Water is leaking below the kitchen tap.")
    return step(token=choose(reply, "Contact me first"))


def add_photo():
    attachment()
    process_inbox()
    return WhatsAppReply.objects.latest("pk")


def fetch_photo(meta=None, content=None):
    with (
        patch("apps.notifications.whatsapp.media.get_json", return_value=meta or META),
        patch(
            "apps.notifications.whatsapp.media.get_bytes",
            return_value=content or png(),
        ),
    ):
        return fetch_media()


def test_repair_photo_is_cleaned_then_attached_only_after_confirm_without_storage_io(house):
    repair_draft(house)
    reply = add_photo()
    assert not MaintenanceRequest.objects.exists()
    assert fetch_photo() == 1
    media = WhatsAppMedia.objects.get()
    assert media.content is None and media.name.startswith("maintenance/photos/")
    with default_storage.open(media.name, "rb") as photo:
        assert photo.read(2) == b"\xff\xd8"
    with patch.object(default_storage, "save", side_effect=AssertionError("storage under lock")):
        result = step(token=choose(reply, "Confirm repair"))
    job = MaintenanceRequest.objects.get()
    assert job.photos.count() == 1 and job.photos.get().image.name == media.name
    assert job.photos.get().uploaded_by == house["tenant"] and "1 photo" in result.view["text"]
    assert not WhatsAppMedia.objects.exists()


def test_unready_or_rejected_photo_preserves_draft_for_remove_and_confirm(house):
    repair_draft(house)
    reply = add_photo()
    reply = step(token=choose(reply, "Confirm repair"))
    assert not MaintenanceRequest.objects.exists() and "still being checked" in reply.view["text"]
    assert fetch_photo(meta={**META, "mime_type": "application/pdf"}, content=b"%PDF-fake") == 0
    reply = step(token=choose(reply, "Confirm repair"))
    assert not MaintenanceRequest.objects.exists()
    reply = step(token=choose(reply, "Remove photos"))
    step(token=choose(reply, "Confirm repair"))
    assert MaintenanceRequest.objects.count() == 1 and not MaintenancePhoto.objects.exists()


@pytest.mark.parametrize("change", ["stop", "lease", "member", "expired"])
def test_repair_media_does_not_download_after_access_or_draft_changes(house, change):
    repair_draft(house)
    add_photo()
    if change == "stop":
        revoke(phone=PHONE)
    elif change == "lease":
        type(house["lease"]).objects.update(status="ended")
    elif change == "member":
        OrganizationMembership.objects.filter(user=house["tenant"]).update(is_active=False)
    else:
        WhatsAppConversation.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
    with patch("apps.notifications.whatsapp.media.get_json") as lookup:
        assert fetch_media() == 0
    lookup.assert_not_called()


def test_cancelled_repair_files_expire_but_submitted_photos_survive_cleanup(house):
    repair_draft(house)
    reply = add_photo()
    assert fetch_photo() == 1
    media = WhatsAppMedia.objects.get()
    step(token=choose(reply, "Cancel"))
    WhatsAppMedia.objects.update(created_at=timezone.now() - timedelta(days=3))
    cleanup_media()
    assert not default_storage.exists(media.name) and not WhatsAppMedia.objects.exists()
    reply = repair_draft(house)
    attachment(identity="second-photo")
    process_inbox()
    reply = WhatsAppReply.objects.latest("pk")
    assert fetch_photo() == 1
    step(token=choose(reply, "Confirm repair"))
    stored = MaintenancePhoto.objects.get().image.name
    cleanup_media()
    assert default_storage.exists(stored)


def test_deleting_binding_keeps_photo_cleanup_pointer(house):
    repair_draft(house)
    add_photo()
    assert fetch_photo() == 1
    row = WhatsAppMedia.objects.get()
    WhatsAppBinding.objects.get().delete()
    row.refresh_from_db()
    assert row.binding_id is None and default_storage.exists(row.name)
    WhatsAppMedia.objects.update(created_at=timezone.now() - timedelta(days=3))
    cleanup_media()
    assert not default_storage.exists(row.name)


def test_repair_photos_deduplicate_and_stop_at_eight(house):
    repair_draft(house)
    add_photo()
    attachment(identity="repeat", media="meta-media-1")
    process_inbox()
    assert WhatsAppMedia.objects.count() == 1
    for number in range(1, 9):
        attachment(identity=f"photo-{number}", media=f"media-{number}")
        process_inbox()
    assert WhatsAppMedia.objects.count() == 8
    assert "up to 8" in WhatsAppReply.objects.latest("pk").view["text"]


def test_repair_photo_access_is_rechecked_after_download_before_storage(house):
    repair_draft(house)
    add_photo()

    def download(*args):
        assert not connection.in_atomic_block
        OrganizationMembership.objects.filter(user=house["tenant"]).update(is_active=False)
        return png()

    with (
        patch("apps.notifications.whatsapp.media.get_json", return_value=META),
        patch(
            "apps.notifications.whatsapp.media.get_bytes",
            side_effect=download,
        ),
        patch.object(default_storage, "save") as save,
    ):
        assert fetch_media() == 0
    save.assert_not_called()


def test_repair_photo_storage_runs_without_locks(house):
    repair_draft(house)
    reply = add_photo()
    save = default_storage.save

    def store(*args, **kwargs):
        assert not connection.in_atomic_block
        return save(*args, **kwargs)

    with patch.object(default_storage, "save", side_effect=store):
        assert fetch_photo() == 1
    step(token=choose(reply, "Confirm repair"))
    assert MaintenancePhoto.objects.count() == 1


def test_photo_during_entry_question_reissues_current_buttons(house):
    menu = workspace(house)
    reply = step(token=choose(menu, "Report a repair"))
    step(token=reply.view["options"][0]["id"])
    step("Tap leaking")
    step("Water leaks from the tap.")
    reply = add_photo()
    reply = step(token=choose(reply, "Contact me first"))
    assert fetch_photo() == 1
    step(token=choose(reply, "Confirm repair"))
    assert MaintenancePhoto.objects.count() == 1


def test_repair_rejects_document_metadata_without_fetching_its_bytes(house):
    repair_draft(house)
    add_photo()
    with (
        patch(
            "apps.notifications.whatsapp.media.get_json",
            return_value={
                **META,
                "mime_type": "application/pdf",
            },
        ),
        patch("apps.notifications.whatsapp.media.get_bytes") as fetch,
    ):
        assert fetch_media() == 0
    fetch.assert_not_called()
    assert WhatsAppMedia.objects.get().status == "rejected"
