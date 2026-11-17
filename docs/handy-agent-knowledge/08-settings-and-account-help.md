# Settings and account help

## Roles and beta signup

Dwella has platform admins, property admins, property managers and tenants.
Property admins oversee the entire workspace. Property managers are assigned
properties and can cover a teammate's properties temporarily when a live cover
session is active. Public beta applications request property-manager access; an
application alone does not create an active workspace, verify a mailbox or
grant access to records.

Property managers can use Handy for data and approved writes within their
assigned/covered property scope. Creating a new property and workspace-level
team/financial settings remain property-admin work. Tenants use their tenancy
portal and do not have Handy access. Changing tenant access must preserve
historical financial records. For invitations, recovery or access removal,
guide the user through the app; Handy has no corresponding write action.

## System-admin settings

System admins can edit the Handy connection, title and suggested questions;
public support contacts; approved sender and reply-to identities; daily SMTP
recipient allowance; SMS/WhatsApp identity, template and activation; beta
registration, email pause/resume, opening/launch dates, countdown offsets and
local sending hour.

These controls are admin-only. Handy cannot edit them, request secrets or query
their database storage. User preferences and organization settings do not grant
platform-admin authority. Guide the system admin to Settings. Resend setup
remains a separate, deferred decision; do not claim these controls enabled it.

## Assistant connection

Changing the saved Handy address disables the assistant and clears verification.
The admin checks the connection and then explicitly enables availability.
A successful check verifies HTTPS and the identity endpoint; it does not prove
authenticated chat, tools or database access. Disabling prevents new tokens and
action calls; issued read identities may remain usable until expiry. Never ask
the user to paste a token or signing key.

## Communications

Notices are outbound communications, not a two-way chat inbox. A configured
channel also needs provider readiness and the required phone consent. Provider
credentials, approval, consent, quota and activation can prevent sending. Saving
settings or enabling a channel does not send old held requests.

Preview selected active-tenant notices through the approved action, show exact
recipients/content/readiness, and confirm only after explicit approval of that
preview. Re-preview changed content or recipients. Queued or provider-accepted
does not prove a tenant received the notice.

## Public dates and support

Dates, registration availability and support contacts are editable. Use the
current page or public configuration. If unavailable, say the current value is
unavailable and guide the user to the app. Do not invent dates, addresses or a
registration guarantee. Test and production may differ.
