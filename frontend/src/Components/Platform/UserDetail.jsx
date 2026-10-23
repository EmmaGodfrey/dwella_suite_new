import React, { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Button, Menu, MenuTrigger, MenuPopover, MenuList, MenuItem } from "@fluentui/react-components";
import { toast } from "react-toastify";
import { usePlatformChoices, usePlatformDetail, usePlatformMutation } from "../../Services/platform";
import { useCurrentUserQuery } from "../../Services/queries";
import { StatusBadge } from "../../shared/components/StatusBadge";
import { AdminDrawer, AdminHeader, AdminState, AdminTable, ConfirmAction, choice, nameOf, roles, when, workspaceName } from "./AdminUI";
import { RecentActivity } from "./AuditLog";

export default function UserDetail() {
  const { id } = useParams();
  const query = usePlatformDetail("users", id);
  const current = useCurrentUserQuery();
  const workspaces = usePlatformChoices("workspaces", { active: "true" });
  const mutation = usePlatformMutation();
  const [dialog, setDialog] = useState(null);
  const user = query.data;
  const self = String(current.data?.id) === id;
  const run = async (action, body, method = "post") => {
    await mutation.mutateAsync({ resource: "users", id, action, body, method });
    setDialog(null); toast.success("Account updated.");
  };
  const confirmations = {
    status: { title: user?.is_active ? "Deactivate account?" : "Reactivate account?", description: user?.is_active ? "The user will lose access and their support sessions will end." : "The user will be able to sign in again.", action: "status", body: { active: !user?.is_active } },
    "password-reset": { title: "Send password reset link?", description: "A secure password reset link will be emailed to this user.", action: "password-reset" },
    "sign-out": { title: "Sign out everywhere?", description: "Their login token and active support sessions will be revoked.", action: "sign-out" },
    "reset-2fa": { title: "Reset two-factor authentication?", description: "Their authenticator will be removed and they will be signed out. Verify their identity before continuing.", action: "reset-2fa" },
    "admin-access": { title: user?.is_staff || user?.is_superuser ? "Revoke platform access?" : "Grant platform access?", description: "Platform administrators can manage users and request audited support access to workspaces.", action: "admin-access", body: { enabled: !(user?.is_staff || user?.is_superuser) } },
  };
  const confirm = confirmations[dialog?.type];
  return <AdminState query={query}><div className="admin-screen">
    <Link to="/admin/users">← Users</Link>
    <AdminHeader title={nameOf(user)} initials={nameOf(user).split(" ").slice(0, 2).map((n) => n[0]).join("")}
      description={`${user?.email || ""} · Joined ${when(user?.date_joined)}`}
      badge={<div className="admin-badges"><StatusBadge value={user?.is_active ? "active" : "inactive"} />
        <StatusBadge value={user?.identity_verification?.status || "not_submitted"} />
        <StatusBadge value={user?.has_two_factor ? "2FA on" : "2FA off"} /></div>}>
      <Button appearance="primary" onClick={() => setDialog({ type: "edit" })}>Edit profile</Button>
      <Menu><MenuTrigger disableButtonEnhancement><Button>More actions</Button></MenuTrigger>
        <MenuPopover><MenuList>
          <MenuItem disabled={self} onClick={() => setDialog({ type: "status" })}>{user?.is_active ? "Deactivate" : "Reactivate"}</MenuItem>
          {current.data?.is_superuser && <MenuItem disabled={self} onClick={() => setDialog({ type: "admin-access" })}>{user?.is_staff || user?.is_superuser ? "Revoke" : "Grant"} platform access</MenuItem>}
          {current.data?.is_superuser && <MenuItem disabled={self || user?.is_active} onClick={() => setDialog({ type: "delete" })}>Permanently delete</MenuItem>}
        </MenuList></MenuPopover></Menu>
    </AdminHeader>
    <div className="admin-two-columns"><div className="admin-stack">
      <section className="admin-card"><h2>Workspace memberships</h2>
        <AdminTable rows={user?.memberships || []} columns={[
          { key: "workspace", label: "Workspace", render: (m) => workspaceName(m.organization) },
          { key: "role", label: "Role" },
          { key: "status", label: "Status", render: (m) => <StatusBadge value={m.is_active ? "active" : "inactive"} /> },
          { key: "action", label: "Action", render: (m) => <Button appearance="subtle" onClick={() => setDialog({ type: "membership", membership: m })}>Change role / remove</Button> },
        ]} />
        {!user?.memberships?.length && <p className="admin-note">No workspace memberships.</p>}
        <div className="admin-card-actions"><Button onClick={() => setDialog({ type: "membership" })}>Add to workspace</Button></div>
      </section>
      <RecentActivity filters={{ user: id }} />
    </div><aside className="admin-stack">
      <section className="admin-card"><h2>Profile</h2><dl>
        <div><dt>Email</dt><dd>{user?.email}</dd></div>
        <div><dt>Phone</dt><dd>{user?.profile?.phone_number || "Not provided"}</dd></div>
        <div><dt>Last login</dt><dd>{when(user?.last_login)}</dd></div>
      </dl></section>
      <section className="admin-card"><h2>Security & identity</h2><dl>
        <div><dt>Two-factor authentication</dt><dd>{user?.has_two_factor ? "Enabled · Authenticator app" : "Not enabled"}</dd></div>
        <div><dt>Identity verification</dt><dd><StatusBadge value={user?.identity_verification?.status || "not_submitted"} /></dd></div>
      </dl><div className="admin-card-actions">
        <Button disabled={!user?.is_active} onClick={() => setDialog({ type: "password-reset" })}>Send reset link</Button>
        <Button onClick={() => setDialog({ type: "sign-out" })}>Sign out everywhere</Button>
        {user?.has_two_factor && <Button onClick={() => setDialog({ type: "reset-2fa" })}>Reset 2FA</Button>}
      </div><p className="admin-note">Platform access and permanent deletion require a superuser. Your own account and the last superuser are protected.</p></section>
    </aside></div>
    {dialog?.type === "edit" && <AdminDrawer title="Edit profile" onClose={() => setDialog(null)}
      initial={{ full_name: nameOf(user), email: user.email, phone_number: user.profile?.phone_number || "" }} fields={[
        { key: "full_name", label: "Full name", required: true, maxLength: 150 },
        { key: "email", label: "Email", required: true, type: "email", maxLength: 150 },
        { key: "phone_number", label: "Phone number", pattern: /^\+?[\d\s-]{7,32}$/, maxLength: 32 },
      ]} onSubmit={(values) => run(null, values, "patch")} />}
    {dialog?.type === "membership" && <AdminDrawer title={dialog.membership ? "Change workspace access" : "Add to workspace"}
      onClose={() => setDialog(null)} initial={{ organization: dialog.membership?.organization?.id || "", role: dialog.membership?.role || "viewer", remove: "false" }}
      fields={(values) => [
        { key: "organization", label: "Workspace", type: "select", required: true, disabled: Boolean(dialog.membership),
          options: [...new Map([...(workspaces.data?.results || []), ...(dialog.membership ? [dialog.membership.organization] : [])].map((w) => [w.id, { value: w.id, label: workspaceName(w) }])).values()] },
        ...(values.remove === "false" ? [{ key: "role", label: "Role", type: "select", required: true, options: roles.map(choice) }] : []),
        ...(dialog.membership ? [{ key: "remove", label: "Access", type: "select", required: true, options: [{ value: "false", label: "Keep membership" }, { value: "true", label: "Remove membership" }] }] : []),
      ]} onSubmit={(values) => run("membership", { ...values, remove: values.remove === "true" })} />}
    {confirm && <ConfirmAction {...confirm} onClose={() => setDialog(null)} onConfirm={() => run(confirm.action, confirm.body)} />}
    {dialog?.type === "delete" && <ConfirmAction title="Permanently delete user?" description="This cannot be undone. Financial records remain governed by retention rules."
      confirmation={`DELETE ${nameOf(user)}`} label="Delete user" onClose={() => setDialog(null)} onConfirm={async (confirmation) => {
        await mutation.mutateAsync({ resource: "users", id, method: "delete", body: { confirmation } });
        window.location.assign("/admin/users");
      }} />}
  </div></AdminState>;
}
