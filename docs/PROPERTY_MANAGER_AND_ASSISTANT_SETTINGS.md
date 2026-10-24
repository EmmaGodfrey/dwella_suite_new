# Property Manager naming and assistant availability

The displayed account types are Super Admin, Property Manager and Tenant. The stored membership/persona key `landlord` is retained for API and existing-data compatibility. This is a display rename, not a new role or permission grant. Historical beta-application occupations are preserved as submitted; those are not account permissions.

Handy groups are unchanged: property managers receive `organization_admin`, `portfolio_manager`, and `portfolio_viewer`. The knowledge base should call these clients property managers and explain that `landlord` is the legacy internal identifier.

Super Admins control Handy in **Settings > Handy assistant**. `GET/PATCH /api/v1/platform/settings/` is superuser-only. The flag defaults to disabled independently in each database and changes are audited atomically. A connection URL and signing secret must be configured before enabling.

Authenticated browsers check `/api/v1/accounts/handy-agent/config/` before loading the official script and every 30 seconds or on window focus. Disabling hides the widget, prevents new tokens, and immediately rejects action calls, including existing action tokens. Tokens already shared with Handy can remain valid for read access until their 15-minute expiry; the local switch cannot revoke a third-party-issued session or already-issued JWT remotely.

Production must use a separately configured production Handy agent, never the staging agent. Until its URL and signing secret are configured, the production build and backend stay disabled. Changing Vite build configuration requires a rebuild; the database switch itself does not.

Deployment preparation: create a restricted production PostgreSQL dump, record beta signup IDs/statuses/counts, deploy migrations, verify the same beta rows afterward, confirm the assistant setting is false, and check production health and the Super Admin settings page. Do not enable the feature merely to smoke-test production.
