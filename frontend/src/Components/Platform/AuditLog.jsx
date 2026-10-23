import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Button, Field, Input } from "@fluentui/react-components";
import { toast } from "react-toastify";
import { downloadPlatformFile, usePlatformChoices, usePlatformList } from "../../Services/platform";
import { useFormErrors } from "../../shared/useFormErrors";
import { StatusBadge } from "../../shared/components/StatusBadge";
import { AdminDrawer, AdminHeader, AdminState, AdminTable, Filter, nameOf, when, workspaceName } from "./AdminUI";

const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
export const eventLabel = (action) => action.replaceAll("_", " ").replaceAll(".", " · ");

export function AuditDetail({ event, onClose }) {
  return <AdminDrawer title="Audit event" fields={[]} submitLabel="Close" onClose={onClose} onSubmit={async () => onClose()}>
    <h2>{eventLabel(event.action)}</h2><dl className="admin-event-details">
      {[["When", when(event.created_at)], ["Actor", `${event.actor_name} · ${event.actor_email}`],
        ["Workspace", event.workspace_name || "Platform"], ["Resource", `${event.resource_type} · ${event.resource_id}`],
        ["Support session", event.metadata?.support_session || "None"], ["Reason", event.metadata?.reason || "—"],
        ["Request ID", event.request_id || "—"]].map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}
    </dl><Button disabled={!event.request_id} onClick={async () => {
      try { await navigator.clipboard.writeText(event.request_id); toast.success("Request ID copied."); }
      catch { toast.error("Couldn’t copy. Select the request ID above."); }
    }}>Copy request ID</Button>
    <h3>Recorded details</h3><pre className="admin-event-json">{JSON.stringify(event.metadata, null, 2)}</pre>
  </AdminDrawer>;
}

export function RecentActivity({ filters, showWorkspace = false }) {
  const query = usePlatformList("audit-events", { ...filters, page_size: 5 });
  const [selected, setSelected] = useState(null);
  return <section className="admin-card"><div className="admin-activity-heading"><h2>Recent activity</h2>{showWorkspace && <Link to="/admin/audit-log">Open audit log →</Link>}</div>
    <AdminState query={query} empty={!query.data?.results?.length} title="No recorded activity">
      <ul className="admin-activity">{query.data?.results?.map((event) => <li key={event.id}>
        <time dateTime={event.created_at}>{when(event.created_at)}</time><Button appearance="subtle" onClick={() => setSelected(event)}>
          <span>{eventLabel(event.action)} · {event.actor_name}{showWorkspace && <span className="admin-note">{event.workspace_name || "Platform"}{event.metadata?.reason ? ` · ${event.metadata.reason}` : ""}</span>}</span></Button>
      </li>)}</ul>
    </AdminState>{selected && <AuditDetail event={selected} onClose={() => setSelected(null)} />}
  </section>;
}

export default function AuditLog() {
  const [filters, setFilters] = useState({ page: 1 });
  const [draft, setDraft] = useState({ actor: "", workspace: "", action: "", resource_type: "", resource_id: "", date_from: "", date_to: "", support_session: "" });
  const [selected, setSelected] = useState(null);
  const [exporting, setExporting] = useState(false);
  const query = usePlatformList("audit-events", filters);
  const actors = usePlatformChoices("users");
  const workspaces = usePlatformChoices("workspaces");
  const { validate, fieldProps, clearError } = useFormErrors();
  const change = (key, value) => { setDraft((d) => ({ ...d, [key]: value })); clearError(key); };
  return <div className="admin-screen"><AdminHeader title="Audit log" description="Account and workspace actions with actor identity and support context.">
    <Button appearance="primary" disabled={exporting} onClick={async () => {
      setExporting(true);
      const params = new URLSearchParams(Object.entries(filters).filter(([key, value]) => value && key !== "page"));
      try { await downloadPlatformFile(`audit-events/export/?${params}`, "dwella-audit-log.csv"); }
      catch (error) { toast.error(error.message); }
      finally { setExporting(false); }
    }}>{exporting ? "Exporting…" : "Export CSV"}</Button>
  </AdminHeader>
    <form className="admin-filters" onSubmit={(event) => {
      event.preventDefault();
      if (validate({
        support_session: () => draft.support_session && !uuid.test(draft.support_session) ? "Enter a valid support session ID." : "",
        date_to: () => draft.date_from && draft.date_to && draft.date_from > draft.date_to ? "End date must follow start date." : "",
      }, event.currentTarget)) setFilters({ ...draft, page: 1 });
    }}>
      <Filter label="Actor" value={draft.actor} onChange={(v) => change("actor", v)} options={(actors.data?.results || []).map((u) => ({ value: u.id, label: nameOf(u) }))} />
      <Filter label="Workspace" value={draft.workspace} onChange={(v) => change("workspace", v)} options={(workspaces.data?.results || []).map((w) => ({ value: w.id, label: workspaceName(w) }))} />
      {[["action", "Action"], ["resource_type", "Resource type"], ["resource_id", "Resource ID"], ["support_session", "Support session"]].map(([key, label]) => <Field key={key} label={label} {...fieldProps(key)}><Input value={draft[key]} maxLength={120} onChange={(_, d) => change(key, d.value)} /></Field>)}
      <Field label="From"><Input type="date" value={draft.date_from} onChange={(_, d) => change("date_from", d.value)} /></Field>
      <Field label="To" {...fieldProps("date_to")}><Input type="date" value={draft.date_to} onChange={(_, d) => change("date_to", d.value)} /></Field>
      <Button type="submit">Apply filters</Button>
      <Button onClick={() => { setDraft(Object.fromEntries(Object.keys(draft).map((k) => [k, ""]))); setFilters({ page: 1 }); }}>Reset</Button>
    </form>
    <AdminState query={query} empty={!query.data?.results?.length} title="No audit events match your filters">
      <AdminTable rows={query.data?.results || []} pagination={query.data?.pagination} setPage={(page) => setFilters((f) => ({ ...f, page }))} columns={[
        { key: "time", label: "When", render: (e) => <Button appearance="subtle" onClick={() => setSelected(e)}>{when(e.created_at)}</Button> },
        { key: "actor", label: "Actor", render: (e) => <>{e.actor_name}<span className="admin-note">{e.actor_email}</span></> },
        { key: "action", label: "Action / resource", render: (e) => <>{eventLabel(e.action)}<span className="admin-note">{e.resource_type} · {e.resource_id}</span></> },
        { key: "workspace_name", label: "Workspace" },
        { key: "context", label: "Context", render: (e) => <StatusBadge value={e.metadata?.support_session ? "support" : e.action.startsWith("account.") ? "account" : "platform"} /> },
      ]} />
    </AdminState>{selected && <AuditDetail event={selected} onClose={() => setSelected(null)} />}
  </div>;
}
