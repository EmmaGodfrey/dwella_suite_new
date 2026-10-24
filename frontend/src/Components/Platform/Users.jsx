import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button, Field, Input } from "@fluentui/react-components";
import { Add20Regular, Search20Regular } from "@fluentui/react-icons";
import { toast } from "react-toastify";
import { usePlatformChoices, usePlatformList, usePlatformMutation } from "../../Services/platform";
import { useCurrentUserQuery } from "../../Services/queries";
import { StatusBadge } from "../../shared/components/StatusBadge";
import { AdminDrawer, AdminHeader, AdminState, AdminTable, Filter, choice, nameOf, roles, workspaceName } from "./AdminUI";

const identityOptions = ["pending", "approved", "rejected", "not_submitted"].map(choice);
const baseFields = [
  { key: "full_name", label: "Full name", required: true, maxLength: 150 },
  { key: "email", label: "Email", type: "email", required: true, maxLength: 150 },
  { key: "phone_number", label: "Phone number", pattern: /^\+?[\d\s-]{7,32}$/, maxLength: 32 },
];

export default function Users() {
  const [filters, setFilters] = useState({ page: 1, search: "", role: "", active: "", identity_status: "", two_factor: "", workspace: "" });
  const [creating, setCreating] = useState(false);
  const query = usePlatformList("users", filters);
  const workspaces = usePlatformChoices("workspaces", { active: "true" });
  const current = useCurrentUserQuery();
  const mutation = usePlatformMutation();
  const navigate = useNavigate();
  const update = (key, value) => setFilters((f) => ({ ...f, [key]: value, page: 1 }));
  const workspaceOptions = (workspaces.data?.results || []).map((w) => ({ value: w.id, label: workspaceName(w) }));
  const columns = [
    { key: "user", label: "User", render: (u) => <><Link className="dwella-table-link" to={`/admin/users/${u.id}`}>{nameOf(u)}</Link><span className="admin-note">{u.email}</span></> },
    { key: "role", label: "Role / persona", render: (u) => <StatusBadge value={u.is_staff || u.is_superuser ? "platform_admin" : u.access?.persona || "unassigned"}>{u.is_staff || u.is_superuser ? "Super admin" : u.access?.persona === "landlord" ? "Property manager" : undefined}</StatusBadge> },
    { key: "workspace", label: "Workspace", render: (u) => u.memberships?.filter((m) => m.is_active).map((m) => <span className="admin-note" key={m.id}>{workspaceName(m.organization)} · {choice(m.role).label}</span>) },
    { key: "identity", label: "Identity", render: (u) => <StatusBadge value={u.identity_verification?.status || "not_submitted"} /> },
    { key: "status", label: "Status", render: (u) => <><StatusBadge value={u.is_active ? "active" : "inactive"} /><span className="admin-note">2FA {u.has_two_factor ? "on" : "off"}</span></> },
  ];
  return <div className="admin-screen">
    <AdminHeader title="Users" description="Manage accounts, workspace access and identity checks.">
      <Button appearance="primary" icon={<Add20Regular />} onClick={() => setCreating(true)}>Create user</Button>
    </AdminHeader>
    <div className="admin-filters">
      <Field label="Search users" className="admin-search"><Input value={filters.search} contentBefore={<Search20Regular />}
        placeholder="Name or email" onChange={(_, d) => update("search", d.value)} /></Field>
      <Filter label="Role" value={filters.role} onChange={(v) => update("role", v)} options={roles.map(choice)} />
      <Filter label="Status" value={filters.active} onChange={(v) => update("active", v)} options={[{ value: "true", label: "Active" }, { value: "false", label: "Inactive" }]} />
      <Filter label="Identity" value={filters.identity_status} onChange={(v) => update("identity_status", v)} options={identityOptions} />
      <Filter label="2FA" value={filters.two_factor} onChange={(v) => update("two_factor", v)} options={[{ value: "true", label: "On" }, { value: "false", label: "Off" }]} />
      <Filter label="Workspace" value={filters.workspace} onChange={(v) => update("workspace", v)} options={workspaceOptions} />
    </div>
    <AdminState query={query} empty={!query.data?.results?.length} title="No users match your filters">
      <AdminTable rows={query.data?.results || []} columns={columns} pagination={query.data?.pagination}
        setPage={(page) => setFilters((f) => ({ ...f, page }))} />
    </AdminState>
    {creating && <AdminDrawer wideFields={["full_name", "account_type", "workspace_name"]} title="Create user" submitLabel="Create and send access link"
      initial={{ account_type: "landlord", full_name: "", email: "", phone_number: "" }}
      onClose={() => setCreating(false)} fields={(values) => [
        ...baseFields,
        { key: "account_type", label: "Account type", type: "select", required: true,
          options: [{ value: "landlord", label: "Property manager with a new workspace" }, { value: "member", label: "Add to an existing workspace" }, ...(current.data?.is_superuser ? [{ value: "platform_admin", label: "Super admin" }] : [])] },
        ...(values.account_type === "landlord" ? [{ key: "workspace_name", label: "Workspace name", required: true, maxLength: 180 }] : []),
        ...(values.account_type === "member" ? [
          { key: "organization", label: "Workspace", type: "select", required: true, options: workspaceOptions },
          { key: "role", label: "Role", type: "select", required: true, options: roles.map(choice) },
        ] : []),
      ]} onSubmit={async (values) => {
        const body = { full_name: values.full_name.trim(), email: values.email.trim(), phone_number: values.phone_number.trim(), account_type: values.account_type };
        if (values.account_type === "landlord") body.workspace_name = values.workspace_name.trim();
        if (values.account_type === "member") Object.assign(body, { organization: values.organization, role: values.role });
        const user = await mutation.mutateAsync({ resource: "users", body });
        toast.success("User created. Their access link has been sent.");
        navigate(`/admin/users/${user.id}`);
      }}>
      <p className="admin-note">They’ll receive a secure link to set their password. No password is shared with staff.</p>
      {workspaces.isError && <p role="alert" className="admin-error">Workspaces couldn’t be loaded. <Button onClick={() => workspaces.refetch()}>Retry</Button></p>}
    </AdminDrawer>}
  </div>;
}
