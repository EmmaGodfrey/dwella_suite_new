import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Button, Field, Input } from "@fluentui/react-components";
import { Search20Regular } from "@fluentui/react-icons";
import { toast } from "react-toastify";
import { downloadPlatformFile, usePlatformDetail, usePlatformList, usePlatformMutation } from "../../Services/platform";
import { StatusBadge } from "../../shared/components/StatusBadge";
import { AdminDrawer, AdminHeader, AdminState, AdminTable, Filter, choice, nameOf, when, workspaceName } from "./AdminUI";

export default function IdentityChecks() {
  const [filters, setFilters] = useState({ status: "pending", search: "", page: 1, submitted_after: "", submitted_before: "" });
  const [selected, setSelected] = useState(null);
  const [downloading, setDownloading] = useState(false);
  const query = usePlatformList("identity-verifications", filters);
  const totals = usePlatformDetail("identity-verifications", "summary");
  const mutation = usePlatformMutation();
  const change = (key, value) => setFilters((f) => ({ ...f, [key]: value, page: 1 }));
  return <div className="admin-screen">
    <AdminHeader title="Identity checks" description="Review submitted identity documents and record a clear decision." />
    <AdminState query={totals}><dl className="admin-metrics">
      {[["Pending review", "pending"], ["Approved", "approved"], ["Rejected", "rejected"]].map(([label, key]) => <div key={key}><dt>{label}</dt><dd>{totals.data?.[key]}</dd></div>)}
    </dl></AdminState>
    <div className="admin-filters"><Field label="Search identity checks" className="admin-search">
      <Input contentBefore={<Search20Regular />} placeholder="Name or email" value={filters.search} onChange={(_, d) => change("search", d.value)} />
    </Field><Filter label="Status" value={filters.status} onChange={(v) => change("status", v)} options={["pending", "approved", "rejected"].map(choice)} />
      <Field label="Submitted from"><Input type="date" value={filters.submitted_after} onChange={(_, d) => change("submitted_after", d.value)} /></Field>
      <Field label="Submitted to"><Input type="date" value={filters.submitted_before} min={filters.submitted_after || undefined} onChange={(_, d) => change("submitted_before", d.value)} /></Field>
    </div>
    <AdminState query={query} empty={!query.data?.results?.length} title="No identity checks to review">
      <AdminTable rows={query.data?.results || []} pagination={query.data?.pagination} setPage={(page) => setFilters((f) => ({ ...f, page }))} columns={[
        { key: "applicant", label: "Applicant", render: (r) => <><Link className="dwella-table-link" to={`/admin/users/${r.user.id}`}>{nameOf(r.user)}</Link><span className="admin-note">{r.user.email}</span></> },
        { key: "document", label: "Document", render: (r) => <>{choice(r.document_type).label}<span className="admin-note">Ending {r.document_number_last4 || "—"}</span></> },
        { key: "workspace", label: "Workspace", render: (r) => r.user.memberships?.filter((m) => m.is_active).map((m) => workspaceName(m.organization)).join(", ") || "—" },
        { key: "submitted_at", label: "Submitted", render: (r) => when(r.submitted_at) },
        { key: "status", label: "Status", render: (r) => <StatusBadge value={r.status} /> },
        { key: "action", label: "Action", render: (r) => <Button appearance="subtle" onClick={() => setSelected(r)}>{r.status === "pending" ? "Review" : "View decision"}</Button> },
      ]} />
    </AdminState>
    {selected && <AdminDrawer modal title="Review identity" submitLabel={selected.status === "pending" ? "Record decision" : "Close"}
      initial={{ decision: "approved", reason: "" }} onClose={() => setSelected(null)}
      fields={(values) => selected.status !== "pending" ? [] : [
        { key: "decision", label: "Decision", type: "select", required: true, options: [{ value: "approved", label: "Approve" }, { value: "rejected", label: "Reject" }] },
        ...(values.decision === "rejected" ? [{ key: "reason", label: "Reason for rejection", type: "textarea", required: true, minLength: 5, maxLength: 300 }] : []),
      ]} onSubmit={async (values) => {
        if (selected.status === "pending") {
          await mutation.mutateAsync({ resource: "identity-verifications", id: selected.id, action: "review", body: { ...values, reason: values.decision === "rejected" ? values.reason.trim() : "" } });
          toast.success("Identity review recorded.");
        }
        setSelected(null);
      }}>
      <h2>{selected.legal_name || nameOf(selected.user)}</h2><p>{selected.user.email}</p>
      <StatusBadge value={selected.status} /><p>{choice(selected.document_type).label} · ending {selected.document_number_last4 || "—"}</p>
      <p className="admin-note">Submitted {when(selected.submitted_at)}. Document access and decisions are recorded.</p>
      <Button disabled={!selected.has_document || downloading} onClick={async () => {
        setDownloading(true);
        try { await downloadPlatformFile(`identity-verifications/${selected.id}/document/`, `identity-${selected.id}`); }
        catch (error) { toast.error(error.message); }
        finally { setDownloading(false); }
      }}>{downloading ? "Downloading…" : selected.has_document ? "Download document" : "No document available"}</Button>
      {selected.rejection_reason && <p>Rejection reason: {selected.rejection_reason}</p>}
      {selected.reviewed_at && <p className="admin-note">Reviewed {when(selected.reviewed_at)}</p>}
    </AdminDrawer>}
  </div>;
}
