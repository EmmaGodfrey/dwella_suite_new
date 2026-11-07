# Handy test knowledge and schema refresh

Prepared 2026-10-28. Scope: test only. Production and the public marketing site
remain unchanged. A working TLS certificate does not itself synchronize Handy's
knowledge, database schema or action definitions.

## Sources

- Agent API base: `https://dwella.agents.handyagent.chat/agent`.
- Identity check: `https://dwella.agents.handyagent.chat/agent/me/`.
- Current test API schema: `https://app.dwella.properties/test/api/v1/schema/`.
- Knowledge source: `docs/handy-agent-knowledge/`, starting with `TOC.md`.
- Test actions have `/test/api/v1/assistant/` URLs. Import only operations marked
  `x-agent.enabled`; the current test release has eleven.

The provider's existing external database connection must continue to use the
isolated test database and restricted gateway. Keep its existing protected
connection credentials; no password belongs in a knowledge document or ZIP.
Do not substitute production or the Django application's database account.

## Provider-side sequence

1. Open the test agent's configuration in Handy. Confirm the selected agent and
   database are the existing test integration, not production.
2. Replace the old Dwella knowledge package with the newly generated package.
   Do not retain conflicting old role/action instructions. Make the overview
   and access-policy document available before database questions.
3. Refresh database metadata using the existing connection. This is schema
   discovery, not a grant of permission to new tables. Preserve the explicit
   eleven-table allowlist and organization policies from `01-data-access-rules.md`.
4. Refresh the test OpenAPI action source. Keep only the eleven `x-agent.enabled`
   operations. Do not expose account, platform-settings, payment-provider,
   withdrawal, signing, messaging-storage or other normal application APIs as
   assistant actions. Keep approval prompts for writes and exact-preview
   approval for tenant notices.
5. Save/rebuild the test agent using Handy's supported controls, then verify
   organization scope with the provider's test facilities. A super-admin token
   with no authorized organization must not return portfolio rows. A denied
   query must stay denied rather than falling back to a broader connection.
6. In Dwella test Settings, save the API base, check the connection, and enable
   availability when the provider refresh is ready. Changing an address clears
   prior verification and disables availability by design.

The code deployment cannot prove these provider-console operations happened.
No provider administration connector is configured in this workspace. Record
the provider refresh separately; the package and a reachable identity endpoint
are not proof of synchronized knowledge or authenticated chat.

## Expected boundaries after refresh

- Three app roles: system admin, Property manager, Tenant. Internal property
  manager key remains `landlord`; there is no new property-admin role.
- Property-manager groups remain `organization_admin`, `portfolio_manager`,
  `portfolio_viewer`. Tenants receive no Handy token.
- Eleven direct-read business tables, each limited to the signed organization
  context; child-table filters follow the authorized parent.
- Eleven approved actions, including notice preview and separate confirmation.
- No direct reads of private settings, authentication, provider-finance,
  signing or notification-storage records, including newly discovered tables.
- No automatic sending, payment, payout or other write to validate a refresh.

## Local artifacts

The release handoff produces a knowledge ZIP containing only the Markdown
knowledge documents, an allowlisted database-column snapshot with no business
rows, and a reduced test OpenAPI JSON file containing the approved actions and
their referenced components. These are distinct artifacts: import knowledge as
knowledge and action definitions as actions. A schema snapshot is a reference,
not a replacement for a provider-side refresh or row policies.
