import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from apps.accounts.models import IdentityVerification
from apps.accounts.private_media import deny_public_identity_document

pytestmark = pytest.mark.django_db


def test_identity_document_is_staff_only_no_store_and_audited(context, tmp_path):
    client, actor, _, _ = context
    with override_settings(MEDIA_ROOT=tmp_path):
        user = get_user_model().objects.create_user(username="document-owner")
        verification = IdentityVerification.objects.create(
            user=user, status="pending",
            document_image=SimpleUploadedFile("identity.png", b"private-document"),
        )
        path = f"/api/v1/platform/identity-verifications/{verification.pk}/document/"
        response = client.get(path)
        assert response.status_code == 200
        assert response["Cache-Control"] == "private, no-store"
        assert b"".join(response.streaming_content) == b"private-document"
        client.force_authenticate(user)
        assert client.get(path).status_code == 403
        assert deny_public_identity_document(None, "identity.png").status_code == 404
        verification.document_image.delete()
