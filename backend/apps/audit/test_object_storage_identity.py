import io
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.files.base import File
from rest_framework.test import APIClient

from apps.accounts.models import IdentityVerification

pytestmark = pytest.mark.django_db


def test_remote_identity_document_stays_behind_staff_permission_and_audit(context):
    client, _, _, _ = context
    owner = get_user_model().objects.create_user(username="remote-document-owner")
    record = IdentityVerification.objects.create(
        user=owner, status="pending", document_image="profiles/verification_documents/id.png"
    )
    endpoint = f"/api/v1/platform/identity-verifications/{record.pk}/document/"
    field = IdentityVerification._meta.get_field("document_image")
    with patch.object(field, "storage") as storage:
        storage.open.return_value = File(io.BytesIO(b"remote-private-file"), name="id.png")
        response = client.get(endpoint)
        assert response.status_code == 200
        assert response["Cache-Control"] == "private, no-store"
        assert b"".join(response.streaming_content) == b"remote-private-file"
        storage.open.assert_called_once_with(record.document_image.name, "rb")
        storage.open.reset_mock()
        client.force_authenticate(owner)
        assert client.get(endpoint).status_code == 403
        assert APIClient().get(endpoint).status_code == 403
        storage.open.assert_not_called()
        storage.url.assert_not_called()
        storage.path.assert_not_called()
