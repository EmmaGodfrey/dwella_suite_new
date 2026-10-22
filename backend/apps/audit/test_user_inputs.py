import pytest
from django.contrib.auth import get_user_model

from .user_serializers import CreateUserInput, UserProfileInput

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("data", [
    {}, {"full_name": "A", "email": "not-email"},
    {"full_name": "A", "email": "a@mailinator.com"},
    {"full_name": "A", "email": "a@example.com", "phone_number": "abc"},
])
def test_invalid_profile_input(data):
    assert not UserProfileInput(data=data).is_valid()


def test_email_is_normalized_unique_and_edit_can_keep_own_address():
    user = get_user_model().objects.create_user(username="known", email="a@example.com")
    serializer = UserProfileInput(data={"full_name": "A", "email": "A@EXAMPLE.COM"})
    assert not serializer.is_valid()
    serializer = UserProfileInput(user, data={"full_name": "A", "email": " A@EXAMPLE.COM "})
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["email"] == "a@example.com"


@pytest.mark.parametrize("kind", ["landlord", "member", "unknown"])
def test_creation_requires_kind_specific_details(kind):
    serializer = CreateUserInput(data={
        "full_name": "New User", "email": "new@example.com", "account_type": kind,
    })
    assert not serializer.is_valid()
