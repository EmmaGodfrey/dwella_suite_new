from .models import SupportSession

URL = "/api/v1/platform/support-sessions/"
LANDLORD_URLS = [
    "/api/v1/properties/",
    "/api/v1/properties/dashboard/",
    "/api/v1/tenants/",
    "/api/v1/leases/",
    "/api/v1/billing/invoices/",
    "/api/v1/reports/rent-roll/",
    "/api/v1/reports/arrears/",
    "/api/v1/notifications/",
    "/api/v1/organizations/onboarding/",
    "/api/v1/organizations/",
    "/api/v1/maintenance/requests/",
    "/api/v1/maintenance/vendors/",
    "/api/v1/integrations/smart-invoice/",
    "/api/v1/documents/versions/",
    "/api/v1/documents/originals/",
    "/api/v1/subscriptions/entitlements/",
]


def start(client, org):
    response = client.post(
        URL, {"organization": str(org.public_id), "reason": "Beta onboarding call"}, format="json"
    )
    assert response.status_code == 201, response.content
    client.credentials(HTTP_X_DWELLA_WORKSPACE=str(org.public_id))
    return SupportSession.objects.get(public_id=response.json()["response_data"]["id"])
