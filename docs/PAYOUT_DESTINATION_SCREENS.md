# Self-service receiving details

2026-10-25: user explicitly removed admin approval. Phone verification belongs on
the landlord's side, potentially WhatsApp/SMS once configured. Neither sending
service is configured; user explicitly requested leaving verification open FOR
TEST so they can test payments. No SMS/WhatsApp integration is part of this change.
Do not prefill or save receiving details from chat.

Landlords save their registered wallet name, network and number from Billing.
No administrator approval, password re-entry or OTP is required in this explicit
test bypass. Backend still enforces authenticated active landlord access,
workspace/currency isolation, input confirmation, throttling and audit history.
Gate bypass on BOTH APP_ENVIRONMENT=test and
LENCO_ALLOW_UNVERIFIED_DESTINATIONS=true, defaulting closed elsewhere. Do not
present the number as verified. Existing collections retain their immutable
destination version. Repeated identical saves reuse the active version.
Legacy approved_by/approval_reason database columns record the configuring
actor and test-bypass reason; they do not imply an admin step or phone verification.

Use the existing Figma payout drawer (227:113), Fluent UI and FormDrawer.
Keep account fields readable on phone and desktop in both themes. Bank/card
destinations and payout scheduling are separate features; expose only mobile
money and automatic payout after settlement. Reuse existing hooks and components.

Security workflow: plan, implement, validate. This runtime does not expose
in-place model switching. Retain native permissions, throttles and backend
validation. Test unauthenticated/tenant/other-workspace/support-admin/staff access,
malformed data, default-closed and explicit test-only bypass, repeated actions
and preservation of earlier collection destinations. Run the full backend suite
and frontend build before test deployment.
Production must remain untouched and test data must not be reset again.
