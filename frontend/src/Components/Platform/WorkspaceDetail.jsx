import React, { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Button, Menu, MenuTrigger, MenuPopover, MenuList, MenuItem } from "@fluentui/react-components";
import { toast } from "react-toastify";
import { usePlatformDetail, usePlatformList, usePlatformMutation } from "../../Services/platform";
import { useCurrentUserQuery } from "../../Services/queries";
import { StatusBadge } from "../../shared/components/StatusBadge";
import { AdminDrawer, AdminHeader, AdminState, AdminTable, ConfirmAction, money, nameOf, when, workspaceName } from "./AdminUI";
import { occupancy, profileFields } from "./Workspaces";

export default function WorkspaceDetail() {
  const { id } = useParams();
  const query = usePlatformDetail("workspaces", id);
  const current = useCurrentUserQuery();
  const [dialog, setDialog] = useState(null);
  const owners = usePlatformList("users", { active: "true", page_size: 200 }, { enabled: dialog === "transfer" });
  const mutation = usePlatformMutation();
  const navigate = useNavigate();
  const workspace = query.data;
  const update = async (action, body, method = "post") => {
    await mutation.mutateAsync({ resource: "workspaces", id, action, body, method });
    setDialog(null); toast.success("Workspace updated.");
  };
  return <AdminState query={query}><div className="admin-screen">
    <Link to="/admin/workspaces">← Workspaces</Link>
    <AdminHeader title={workspaceName(workspace)} initials={workspaceName(workspace).split(" ").slice(0, 2).map((n) => n[0]).join("")}
      description={`${workspace?.town || workspace?.country || ""} · Created ${when(workspace?.created_at)}`}
      badge={<div className="admin-badges"><StatusBadge value={workspace?.is_active ? "active" : "suspended"} /></div>}>
      <Button onClick={() => setDialog("edit")}>Edit profile</Button>
      <Menu><MenuTrigger disableButtonEnhancement><Button>More actions</Button></MenuTrigger><MenuPopover><MenuList>
        <MenuItem onClick={() => setDialog("status")}>{workspace?.is_active ? "Suspend" : "Reactivate"}</MenuItem>
        <MenuItem disabled={!workspace?.is_active} onClick={() => setDialog("transfer")}>Transfer ownership</MenuItem>
        {current.data?.is_superuser && <MenuItem disabled={workspace?.is_active} onClick={() => setDialog("delete")}>Permanently delete</MenuItem>}
      </MenuList></MenuPopover></Menu>
    </AdminHeader>
    <section className="admin-card"><dl className="admin-metrics">
      {[['Properties / units', `${workspace?.properties_count} / ${workspace?.units_count}`], ['Occupancy', occupancy(workspace || {})], ['Active leases', workspace?.active_leases], ['Outstanding', money(workspace?.outstanding_balance)]].map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}
    </dl></section>
    <section className="admin-card"><h2>Members</h2><AdminTable rows={workspace?.members || []} columns={[
      { key: "member", label: "Member", render: (m) => <><Link className="dwella-table-link" to={`/admin/users/${m.user_id}`}>{m.name}</Link><span className="admin-note">{m.email}</span></> },
      { key: "role", label: "Role" },
      { key: "security", label: "Security", render: (m) => `2FA ${m.has_two_factor ? "enabled" : "not set"}` },
      { key: "status", label: "Status", render: (m) => <StatusBadge value={m.is_active ? "active" : "inactive"} /> },
      { key: "action", label: "Action", render: (m) => <Link to={`/admin/users/${m.user_id}`}>Manage membership</Link> },
    ]} />{!workspace?.members?.length && <p className="admin-note">No members.</p>}</section>
    {dialog === "edit" && <AdminDrawer title="Edit workspace profile" initial={workspace} fields={profileFields}
      onClose={() => setDialog(null)} onSubmit={(values) => update(null, Object.fromEntries(profileFields.map((f) => [f.key, values[f.key]])), "patch")} />}
    {dialog === "transfer" && <AdminDrawer title="Transfer ownership" submitLabel="Transfer ownership" onClose={() => setDialog(null)} fields={[
      { key: "owner", label: "New owner", type: "select", required: true, options: (owners.data?.results || []).map((u) => ({ value: u.id, label: `${nameOf(u)} · ${u.email}` })) },
    ]} onSubmit={(values) => update("transfer-owner", { owner: Number(values.owner) })}><p>Previous owners become workspace admins. The new owner receives full control of this workspace.</p>
      {owners.isError && <p role="alert" className="admin-error">Owners couldn’t be loaded. <Button onClick={() => owners.refetch()}>Retry</Button></p>}
    </AdminDrawer>}
    {dialog === "status" && <ConfirmAction title={workspace.is_active ? "Suspend workspace?" : "Reactivate workspace?"}
      description={workspace.is_active ? "Members will lose access to portfolio data. Support sessions will end." : "Members will regain workspace access. Support staff must open a new session."}
      onClose={() => setDialog(null)} onConfirm={() => update("status", { active: !workspace.is_active })} />}
    {dialog === "delete" && <ConfirmAction title="Permanently delete workspace?" description="This action cannot be undone. Retained financial or tenancy records may prevent deletion."
      confirmation={`DELETE ${workspaceName(workspace)}`} label="Delete workspace" onClose={() => setDialog(null)} onConfirm={async (confirmation) => {
        await update(null, { confirmation }, "delete"); navigate("/admin/workspaces");
      }} />}
  </div></AdminState>;
}
