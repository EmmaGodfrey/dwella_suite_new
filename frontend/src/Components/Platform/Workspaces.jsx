import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button, Field, Input } from "@fluentui/react-components";
import { Add20Regular, Search20Regular } from "@fluentui/react-icons";
import { usePlatformDetail, usePlatformList, usePlatformMutation } from "../../Services/platform";
import { StatusBadge } from "../../shared/components/StatusBadge";
import { AdminDrawer, AdminHeader, AdminState, AdminTable, Filter, money, nameOf, workspaceName } from "./AdminUI";

export const profileFields = [
  { key: "display_name", label: "Workspace name", required: true, maxLength: 180 },
  { key: "email", label: "Email", type: "email", maxLength: 254 },
  { key: "phone_number", label: "Phone number", pattern: /^\+?[\d\s-]{7,40}$/, maxLength: 40 },
  { key: "address", label: "Address", type: "textarea", maxLength: 2000 },
  { key: "town", label: "Town", maxLength: 120 },
  { key: "country", label: "Country", required: true, maxLength: 80 },
  { key: "currency", label: "Currency", required: true, type: "select", options: [{ value: "ZMW", label: "Zambian kwacha (ZMW)" }] },
  { key: "timezone", label: "Timezone", required: true, maxLength: 80 },
];

export const occupancy = (workspace) => workspace.units_count
  ? `${Math.round(workspace.occupied_units / workspace.units_count * 100)}%` : "—";

export default function Workspaces() {
  const [filters, setFilters] = useState({ page: 1, search: "", active: "", created_after: "", created_before: "" });
  const [creating, setCreating] = useState(false);
  const query = usePlatformList("workspaces", filters);
  const totals = usePlatformDetail("workspaces", "summary");
  const owners = usePlatformList("users", { active: "true", page_size: 200 }, { enabled: creating });
  const mutation = usePlatformMutation();
  const navigate = useNavigate();
  const change = (key, value) => setFilters((f) => ({ ...f, [key]: value, page: 1 }));
  return <div className="admin-screen">
    <AdminHeader title="Workspaces" description="Manage landlord workspaces and open an audited support session.">
      <Button appearance="primary" icon={<Add20Regular />} onClick={() => setCreating(true)}>Create workspace</Button>
    </AdminHeader>
    <AdminState query={totals}><section className="admin-card" aria-label="Platform workspace totals"><dl className="admin-metrics">
      {[['Active', totals.data?.active], ['Suspended', totals.data?.suspended], ['New this week', totals.data?.new_this_week], ['Outstanding balance', money(totals.data?.outstanding_balance)]].map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}
    </dl></section></AdminState>
    <div className="admin-filters"><Field label="Search workspaces" className="admin-search"><Input value={filters.search}
      placeholder="Workspace, owner or town" contentBefore={<Search20Regular />} onChange={(_, d) => change("search", d.value)} /></Field>
      <Filter label="Status" value={filters.active} onChange={(v) => change("active", v)} options={[{ value: "true", label: "Active" }, { value: "false", label: "Suspended" }]} />
      <Field label="Created from"><Input type="date" value={filters.created_after} onChange={(_, d) => change("created_after", d.value)} /></Field>
      <Field label="Created to"><Input type="date" value={filters.created_before} min={filters.created_after || undefined} onChange={(_, d) => change("created_before", d.value)} /></Field>
    </div>
    <AdminState query={query} empty={!query.data?.results?.length} title="No workspaces match your filters">
      <AdminTable rows={query.data?.results || []} pagination={query.data?.pagination} setPage={(page) => setFilters((f) => ({ ...f, page }))} columns={[
        { key: "workspace", label: "Workspace / owner", render: (w) => <><Link className="dwella-table-link" to={`/admin/workspaces/${w.id}`}>{workspaceName(w)}</Link><span className="admin-note">{w.members?.filter((m) => m.role === "owner" && m.is_active).map((m) => m.name).join(", ") || "No active owner"}{w.town ? ` · ${w.town}` : ""}</span></> },
        { key: "units", label: "Properties / units", render: (w) => `${w.properties_count} properties · ${w.units_count} units` },
        { key: "occupancy", label: "Occupancy", render: occupancy },
        { key: "balance", label: "Balance", render: (w) => money(w.outstanding_balance) },
        { key: "status", label: "Status", render: (w) => <StatusBadge value={w.is_active ? "active" : "suspended"} color={w.is_active ? "success" : "warning"} /> },
      ]} />
    </AdminState>
    {creating && <AdminDrawer title="Create workspace" submitLabel="Create workspace" onClose={() => setCreating(false)}
      initial={{ country: "Zambia", currency: "ZMW", timezone: "Africa/Lusaka" }} fields={[
        { key: "owner", label: "Owner", type: "select", required: true, options: (owners.data?.results || []).map((u) => ({ value: u.id, label: `${nameOf(u)} · ${u.email}` })) },
        ...profileFields,
      ]} onSubmit={async (values) => {
        const workspace = await mutation.mutateAsync({ resource: "workspaces", body: { ...values, owner: Number(values.owner) } });
        navigate(`/admin/workspaces/${workspace.id}`);
      }}><p className="admin-note">Choose an existing account, or <Link to="/admin/users">create a landlord account</Link> and its workspace together.</p>
      {owners.isError && <p className="admin-error" role="alert">Owners couldn’t be loaded. <Button onClick={() => owners.refetch()}>Retry</Button></p>}
    </AdminDrawer>}
  </div>;
}
