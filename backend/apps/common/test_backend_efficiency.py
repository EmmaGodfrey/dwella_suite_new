"""Synthetic query-scaling probes; no provider calls or real customer data."""

import json
from datetime import timedelta
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.access_state import email_status, require_verified_access
from apps.accounts.models import AccountAccessState
from apps.audit.models import AuditEvent
from apps.audit.user_serializers import PlatformUserSerializer
from apps.billing.models import Invoice, InvoiceLine
from apps.common.permissions import get_user_access
from apps.documents.models import DocumentSignature, DocumentVersion, SignedLeaseOriginal
from apps.documents.snapshots import fingerprint, lease_source
from apps.leases.models import Lease
from apps.maintenance.models import MaintenanceRequest
from apps.organizations.models import Organization, OrganizationMembership
from apps.outreach.models import Contact, Suppression
from apps.properties.models import Property, Unit
from apps.tenants.models import Tenant

pytestmark = pytest.mark.django_db


@pytest.fixture
def portfolio():
    User = get_user_model()
    org = Organization.objects.create(name="Efficiency audit")
    manager = User.objects.create_user(username="audit-owner", email="owner@example.com")
    tenant = User.objects.create_user(username="audit-tenant", email="tenant@example.com")
    admin = User.objects.create_user(username="audit-admin", is_superuser=True, is_staff=True)
    for user, role in [(manager, "landlord"), (tenant, "tenant")]:
        OrganizationMembership.objects.create(user=user, organization=org, role=role)
    prop = Property.objects.create(organization=org, name="Audit homes", address="Test street")
    today = timezone.localdate()
    for i in range(25):
        Property.objects.create(organization=org, name=f"Other property {i}", address="Test")
        Organization.objects.create(name=f"Other workspace {i}")
        AuditEvent.objects.create(organization=org, actor=manager, action="audit.fixture")
        user = User.objects.create_user(username=f"audit-user-{i}", email=f"audit{i}@example.com")
        OrganizationMembership.objects.create(user=user, organization=org, role="landlord")
        person = Tenant.objects.create(
            organization=org,
            user=tenant,
            full_name=f"Tenant {i}",
            email=f"t{i}@example.com",
            phone_number=f"+26097{i:07d}",
        )
        unit = Unit.objects.create(
            organization=org,
            property=prop,
            name=f"Unit {i:02d}",
            rent_amount=100,
            occupancy_status="occupied",
        )
        lease = Lease.objects.create(
            organization=org,
            tenant=person,
            unit=unit,
            reference=f"LSE-{i}",
            start_date=today - timedelta(days=40),
            end_date=today + timedelta(days=90),
            monthly_rent=100,
            status="active",
        )
        invoice = Invoice.objects.create(
            organization=org,
            tenant=person,
            unit=unit,
            lease=lease,
            reference=f"INV-{i}",
            issue_date=today - timedelta(days=40),
            due_date=today - timedelta(days=i + 1),
            total=100,
        )
        InvoiceLine.objects.create(invoice=invoice, kind="rent", description="Rent", amount=100)
        lease.refresh_from_db()
        source = lease_source(lease)
        document = DocumentVersion.objects.create(
            organization=org,
            lease=lease,
            kind="lease",
            version=1,
            status="signing",
            snapshot=source,
            source_fingerprint=fingerprint(source),
            unsigned_pdf=b"x" * 65536,
            pdf=b"x" * 65536,
            sha256="0" * 64,
            page_count=1,
            created_by=manager,
            landlord_signer=manager,
        )
        DocumentSignature.objects.create(
            document=document,
            role="tenant",
            user=tenant,
            signer_name=person.full_name,
            signer_email=person.email,
            authentication_method="otp",
            source="drawn",
            png=b"x" * 32768,
            signed_pdf=b"x" * 65536,
            consent="Test consent",
            signed_at=timezone.now(),
            reviewed_sha256="0" * 64,
            sha256="0" * 64,
        )
        SignedLeaseOriginal.objects.create(
            organization=org,
            lease=lease,
            filename="test.pdf",
            pdf=b"x" * 65536,
            sha256="0" * 64,
            page_count=1,
            uploaded_by=manager,
            note="Test",
        )
        MaintenanceRequest.objects.create(
            organization=org,
            property=prop,
            tenant=person,
            unit=unit,
            title=f"Repair {i}",
            reference=f"MNT-{i}",
            reported_by=manager,
        )
        Contact.objects.create(name=f"Contact {i}", email=f"c{i}@example.com", source="Test only")
    return {"org": org, "manager": manager, "tenant": tenant, "admin": admin}


def measure(client, url):
    cache.clear()
    with CaptureQueriesContext(connection) as captured:
        response = client.get(url)
        assert response.status_code == 200, (url, response.status_code, response.content[:150])
    return {
        "queries": len(captured),
        "sql_bytes": sum(len(q["sql"]) for q in captured),
        "sql": [q["sql"] for q in captured],
    }


def test_measure_backend_lists(portfolio):
    paths = {
        "manager": [
            "/properties/",
            "/properties/units/",
            "/tenants/",
            "/leases/",
            "/maintenance/requests/",
            "/documents/versions/",
            "/documents/originals/",
        ],
        "tenant": ["/portal/leases/", "/portal/invoices/", "/portal/maintenance/"],
        "admin": [
            "/platform/users/",
            "/platform/workspaces/",
            "/platform/audit-events/",
            "/platform/outreach/contacts/",
        ],
    }
    results = {}
    for role, urls in paths.items():
        client = APIClient()
        client.force_authenticate(user=portfolio[role])
        for url in urls:
            full = "/api/v1" + url
            results[full] = {
                str(size): measure(client, full + f"?page_size={size}") for size in [1, 25]
            }
            assert results[full]["25"]["queries"] <= results[full]["1"]["queries"] + 1, full
    destination = Path(__file__).resolve().parents[3] / "output" / "audit-query-measurements.json"
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(results, indent=2))
    print(
        json.dumps(
            {url: {n: v["queries"] for n, v in sizes.items()} for url, sizes in results.items()}
        )
    )


def test_document_metadata_defers_binary_and_file_download_still_works(portfolio):
    client = APIClient()
    client.force_authenticate(portfolio["tenant"])
    document = DocumentVersion.objects.first()
    url = f"/api/v1/portal/leases/{document.lease.public_id}/documents/"
    with CaptureQueriesContext(connection) as queries:
        response = client.get(url)
    assert response.status_code == 200
    assert len(response.json()["response_data"]["versions"]) == 1
    for query in queries:
        sql = query["sql"]
        for table, columns in {
            "documents_documentversion": ["pdf", "unsigned_pdf"],
            "documents_documentsignature": ["png", "signed_pdf"],
            "documents_signedleaseoriginal": ["pdf"],
        }.items():
            for column in columns:
                assert f'"{table}"."{column}"' not in sql
    response = client.get(f"/api/v1/portal/documents/{document.public_id}/pdf/")
    assert response.status_code == 200
    assert b"".join(response.streaming_content) == bytes(document.pdf)
    outsider = get_user_model().objects.create_user(username="not-this-tenant")
    client.force_authenticate(outsider)
    assert client.get(url).status_code == 403


@pytest.mark.parametrize("role", ["landlord", "tenant", "unassigned", "platform_admin"])
@pytest.mark.parametrize("verified", [False, True])
def test_admin_access_projection_matches_fresh_authorization(role, verified):
    user = get_user_model().objects.create_user(
        username="projection", email="projection@example.com", is_staff=role == "platform_admin"
    )
    state = AccountAccessState.objects.create(
        user=user,
        requires_verification=True,
        verified_email=user.email,
        verified_at=timezone.now() if verified else None,
    )
    org = Organization.objects.create(name="Projection")
    membership = None
    if role in ("landlord", "tenant"):
        membership = OrganizationMembership.objects.create(user=user, organization=org, role=role)
    for change in ("initial", "suspended", "email_changed", "membership_revoked"):
        if change == "suspended":
            org.is_active = False
            org.save()
        elif change == "email_changed":
            user.email = "changed@example.com"
            user.save()
        elif change == "membership_revoked" and membership:
            membership.is_active = False
            membership.save()
        loaded = (
            get_user_model()
            .objects.select_related("account_access_state")
            .prefetch_related("organization_memberships__organization")
            .get(pk=user.pk)
        )
        serializer = PlatformUserSerializer()
        with CaptureQueriesContext(connection) as queries:
            projection = serializer.get_access(loaded)
            status = serializer.get_email_verification(loaded)
        assert not queries
        assert projection == get_user_access(user)
        assert status == email_status(user)
    # Display prefetches never make the canonical permission check trust stale state.
    state.verified_at = None
    state.save()
    from rest_framework.exceptions import PermissionDenied

    with pytest.raises(PermissionDenied):
        require_verified_access(loaded)


def test_signing_metadata_rechecks_membership_and_signatures_next_request(portfolio):
    client = APIClient()
    client.force_authenticate(portfolio["manager"])
    document = DocumentVersion.objects.first()
    url = f"/api/v1/documents/versions/{document.public_id}/"
    assert client.get(url).json()["response_data"]["can_sign"] is True
    document.signatures.update(role="landlord")
    assert client.get(url).json()["response_data"]["can_sign"] is False
    document.signatures.update(role="tenant")
    membership = portfolio["manager"].organization_memberships.get()
    membership.is_active = False
    membership.save()
    assert client.get(url).status_code == 403


def test_outreach_suppression_changes_and_edit_response_are_current(portfolio):
    client = APIClient()
    client.force_authenticate(portfolio["admin"])
    contact = Contact.objects.first()
    url = f"/api/v1/platform/outreach/contacts/{contact.public_id}/"
    assert client.get(url).json()["response_data"]["suppressed"] is False
    Suppression.objects.create(email=contact.email.upper(), reason="manual")
    assert client.get(url).json()["response_data"]["suppressed"] is True
    response = client.patch(url, {"email": "new@example.com"}, format="json")
    assert response.status_code == 200
    assert response.json()["response_data"]["suppressed"] is False
