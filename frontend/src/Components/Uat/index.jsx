import React, { useEffect, useMemo, useState } from "react";
import {
  Accordion, AccordionHeader, AccordionItem, AccordionPanel,
  Button, Field, Input, Select, Textarea,
} from "@fluentui/react-components";
import { useCurrentUserQuery } from "../../Services/queries";
import { useExportUatResults, useSaveUatResult, useUatChecklist } from "../../Services/uat";
import { getUserAccess } from "../../shared/access";
import { appHref } from "../../shared/storage";
import { BrandMark } from "../../shared/components/BrandMark";
import "./uat.scss";

const statuses = [
  ["not_tested", "Not tested"], ["passed", "Passed"], ["partial", "Partial"],
  ["failed", "Failed"], ["blocked", "Blocked"], ["not_applicable", "Not applicable"],
];
const moduleNames = {
  "Accounts": "Account", "Properties and units": "Properties & units",
  "Tenants and invitations": "Tenants", "Leases and documents": "Leases & documents",
  "Manual records and proofs": "Manual payments & proofs", "Maintenance": "Repairs",
  "Messages and email": "Email & notifications", "Settings and dashboard": "Settings & dashboard",
  "Access and resilience": "Access & usability",
};
const paths = {
  "Accounts": "/settings?tab=security", "Get Started": "/setup",
  "Properties and units": "/properties", "Tenants and invitations": "/tenants",
  "Leases and documents": "/leases", "Invoices": "/billing",
  "Manual records and proofs": "/billing", "Reports": "/reports", "Deposits": "/leases",
  "Maintenance": "/maintenance", "Messages and email": "/messages",
  "WhatsApp": "/settings?tab=notifications", "Settings and dashboard": "/settings",
  "Access and resilience": "/dashboard", "Assistant": "/dashboard",
};

function FlowRow({ flow, result, userId, readOnly }) {
  const save = useSaveUatResult(userId, flow.id);
  const [notes, setNotes] = useState(result?.notes || "");
  const [dirty, setDirty] = useState(false);
  const [details, setDetails] = useState(false);
  const status = result?.status || "not_tested";
  useEffect(() => {
    if (!dirty) setNotes(result?.notes || "");
  }, [result?.notes, dirty]);
  const attention = ["partial", "failed", "blocked"].includes(status);
  const showNotes = details || attention || dirty;
  function persist(data) {
    const payload = { ...data, ...(dirty ? { notes } : {}) };
    save.mutate(payload, { onSuccess: () => {
      if ("notes" in payload) setDirty(false);
    } });
  }
  async function saveNote(event) {
    event.preventDefault();
    if (notes.length > 2000 || save.isPending) return;
    try {
      await save.mutateAsync({ notes });
      setDirty(false);
    } catch { /* The row keeps the draft and shows retry feedback. */ }
  }
  return <li className={`uat-flow is-${status}`} data-case-id={flow.id}>
    <div className="uat-flow-heading">
      <div>
        <h3>{flow.title}</h3>
        <Button size="small" appearance="transparent" onClick={() => setDetails(!details)}
          aria-expanded={details} aria-controls={`uat-details-${flow.id}`}>
          {details ? "Hide details" : "How to test"}
        </Button>
      </div>
      <div className="uat-result-control">
        <Select aria-label={`Result for ${flow.title}`} value={status} disabled={readOnly || save.isPending}
          onChange={(_, data) => persist({ status: data.value })}>
          {statuses.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
        </Select>
        <span className="uat-save-state" role="status">{save.isPending ? "Saving…" : save.isSuccess ? "Saved" : ""}</span>
      </div>
    </div>
    {details && <div className="uat-flow-details" id={`uat-details-${flow.id}`}>
      <p><strong>Try:</strong> {flow.steps}</p>
      <p><strong>Expect:</strong> {flow.expected}</p>
      <small>{flow.id}{flow.paired ? " · Test with your manager/tenant partner" : ""}</small>
    </div>}
    {showNotes && !readOnly && <form className="uat-note" onSubmit={saveNote}>
      <Field label={attention ? "What didn’t work? (optional)" : "Note (optional)"}
        validationState={notes.length > 2000 ? "error" : "none"}
        validationMessage={notes.length > 2000 ? "Keep your note under 2,000 characters." : undefined}>
        <Textarea value={notes} maxLength={2000} rows={2} resize="vertical" disabled={save.isPending}
          placeholder="Describe the problem. Keep passwords and verification codes out."
          onChange={(_, data) => { setNotes(data.value); setDirty(true); }} />
      </Field>
      <Button type="submit" size="small" disabled={!dirty || save.isPending}>Save note</Button>
    </form>}
    {save.isError && <p role="alert" className="uat-save-error">
      {save.error?.message || "Could not save this result."}{" "}
      <Button size="small" onClick={() => persist(save.variables)}>Retry save</Button>
    </p>}
  </li>;
}

export default function UatChecklist() {
  const user = useCurrentUserQuery().data;
  const access = getUserAccess(user);
  const ownRole = access.persona === "tenant" ? "tenant" : "manager";
  const query = useUatChecklist(user?.id);
  const download = useExportUatResults();
  const [role, setRole] = useState(ownRole);
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [exportEmail, setExportEmail] = useState("");
  const results = useMemo(() => new Map((query.data?.results || []).map(row => [row.case_id, row])), [query.data]);
  const relevant = useMemo(() => (query.data?.cases || []).filter(flow => role === "all" || flow.roles.includes(role)), [query.data, role]);
  const flows = relevant.filter(flow => {
    const status = results.get(flow.id)?.status || "not_tested";
    return (!search || `${flow.title} ${flow.module} ${flow.id}`.toLowerCase().includes(search.toLowerCase()))
      && (filter === "all" || (filter === "attention" ? ["partial", "failed", "blocked"].includes(status) : status === filter));
  });
  const modules = new Map();
  flows.forEach(flow => modules.set(flow.module, [...(modules.get(flow.module) || []), flow]));
  const reviewed = relevant.filter(flow => results.has(flow.id) && results.get(flow.id).status !== "not_tested").length;
  const readOnly = Boolean(query.data?.can_export);
  return <main className="dwella-uat">
    <div className="uat-topline"><BrandMark /><div className="uat-header-actions">
      {readOnly && <>
        <Field label="Tester email (optional)"><Input type="email" maxLength={254}
          value={exportEmail} onChange={(_, data) => setExportEmail(data.value)} /></Field>
        <Button disabled={download.isPending} onClick={() => download.mutate({ email: exportEmail })}>{download.isPending ? "Downloading…" : "Download tester results"}</Button>
      </>}
      <Button as="a" href={appHref("/dashboard")} target="_blank" rel="noreferrer">Open Dwella</Button>
    </div></div>
    <header className="uat-heading"><div><h1>Test checklist</h1>
      <p>{readOnly ? "Participant flows only. Download saved responses to review feedback." : "Choose a result for each flow. Saved to your account and shared with Dwella for review."}</p>
    </div><span className="uat-progress" role="status">{readOnly ? `${query.data.cases.length} participant flows` : <><strong>{reviewed}</strong> / {relevant.length} reviewed</>}</span></header>
    {query.isLoading ? <p role="status">Loading your checklist…</p> : query.isError ? <div role="alert" className="uat-load-error">
      <p>{query.error?.status === 404 ? "The tester checklist is not available in this environment." : "Could not load your checklist."}</p>
      {query.error?.status !== 404 && <Button onClick={() => query.refetch()}>Retry</Button>}
    </div> : <>
      <div className="uat-filters">
        <Field label="Flows"><Select value={role} onChange={(_, data) => setRole(data.value)}>
          <option value="manager">Manager flows{ownRole === "manager" ? " (yours)" : ""}</option>
          <option value="tenant">Tenant flows{ownRole === "tenant" ? " (yours)" : ""}</option>
          <option value="all">All participant flows</option>
        </Select></Field>
        <Field label="Results"><Select value={filter} onChange={(_, data) => setFilter(data.value)}>
          <option value="all">All results</option><option value="not_tested">Not tested</option>
          <option value="attention">Needs attention</option><option value="passed">Passed</option>
          <option value="not_applicable">Not applicable</option>
        </Select></Field>
        <Field label="Find a flow"><Input value={search} onChange={(_, data) => setSearch(data.value)} placeholder="Search module or flow" /></Field>
      </div>
      {download.isError && <p role="alert">{download.error?.message || "Could not download results."} <Button onClick={() => download.mutate({ email: exportEmail })}>Retry download</Button></p>}
      {!flows.length ? <p className="uat-empty" role="status">No flows match these filters.</p> : <Accordion multiple collapsible defaultOpenItems={[]}>
        {[...modules].map(([module, items]) => {
          const done = items.filter(flow => results.get(flow.id)?.status && results.get(flow.id).status !== "not_tested").length;
          let path = paths[module] || "/dashboard";
          if (ownRole === "tenant" && module === "Reports") path = "/billing/statement";
          if (ownRole === "tenant" && module === "Messages and email") path = "/settings?tab=notifications";
          return <AccordionItem value={module} key={module} className="uat-module">
            <AccordionHeader><span>{moduleNames[module] || module}</span><span className="uat-module-count">{readOnly ? `${items.length} flows` : `${done}/${items.length} reviewed`}</span></AccordionHeader>
            <AccordionPanel>
              <a className="uat-module-link" href={appHref(path)} target="_blank" rel="noreferrer">Open module ↗</a>
              <ul>{items.map(flow => <FlowRow key={flow.id} flow={flow} result={readOnly ? undefined : results.get(flow.id)} userId={user.id} readOnly={readOnly} />)}</ul>
            </AccordionPanel>
          </AccordionItem>;
        })}
      </Accordion>}
    </>}
    {query.data && !query.isError && <footer>TEST only · Use fictional tenancy data · Online money movement is disabled</footer>}
  </main>;
}
