import React, { useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Button, Checkbox, DrawerBody, DrawerHeader, DrawerHeaderTitle, Field, Input, OverlayDrawer, Select } from "@fluentui/react-components";
import { ArrowDownload20Regular, Dismiss20Regular } from "@fluentui/react-icons";
import { useCurrentUserQuery, usePropertiesQuery, useTenantsQuery } from "../../Services/queries";
import { useActivityReport, useExportActivityReport } from "../../Services/activityReports";
import { PageActions, SegmentedFilter } from "../../shared/components";
import { StatementActivity, StatementBalances } from "../../shared/components/AccountStatement";
import { paymentMethods, reportOptions } from "../../shared/activityReports.mjs";
import { statementDateErrors, statementMoney, workspaceToday } from "../../shared/statement.mjs";
import { formatDate } from "../../shared/format";
import "../Portal/statement.scss";

function ScopePicker({ kind, onChoose, onClose }) {
  const tenant = kind === "tenant";
  const [search, setSearch] = useState("");
  const [submitted, setSubmitted] = useState("");
  const [archived, setArchived] = useState(false);
  const [page, setPage] = useState(1);
  const filters = { search: submitted, page, page_size: 25, ...(tenant ? { is_active: !archived } : {}) };
  const tenants = useTenantsQuery(filters, { enabled: tenant });
  const properties = usePropertiesQuery(filters, { enabled: !tenant });
  const query = tenant ? tenants : properties;
  return <OverlayDrawer open position="end" onOpenChange={(_, data) => !data.open && onClose()}>
    <DrawerHeader><DrawerHeaderTitle action={<Button appearance="subtle" icon={<Dismiss20Regular />} aria-label="Close selection" onClick={onClose} />}>
      Choose {kind}
    </DrawerHeaderTitle></DrawerHeader>
    <DrawerBody className="report-picker">
      <form onSubmit={event => { event.preventDefault(); setSubmitted(search.trim()); setPage(1); }}>
        <Field label={`Search ${tenant ? "tenants" : "properties"}`}><Input value={search} onChange={(_, data) => setSearch(data.value)} /></Field>
        <Button type="submit">Search</Button>
      </form>
      {tenant && <Checkbox label="Show archived tenants" checked={archived} onChange={(_, data) => { setArchived(data.checked); setPage(1); }} />}
      <Button appearance="subtle" onClick={() => onChoose(null)}>All {tenant ? "tenants" : "properties"}</Button>
      {query.isPending ? <p role="status">Loading choices…</p> : query.isError ? <div role="alert"><p>Could not load choices.</p><Button onClick={() => query.refetch()}>Retry choices</Button></div> : <>
        <div className="report-picker__choices">{(query.data?.results || []).map(row => <Button key={row.id} onClick={() => onChoose({ id: row.id, name: row.full_name || row.name, archived })}>
          {row.full_name || row.name}{tenant && archived ? " · Archived" : ""}
        </Button>)}</div>
        {!query.data?.results?.length && <p>No matching {tenant ? "tenants" : "properties"}.</p>}
        <div className="portal-statement__pagination"><span>Page {page} of {query.data?.pagination?.total_pages || 1}</span><div>
          <Button disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous choices</Button>
          <Button disabled={!query.data?.pagination?.next} onClick={() => setPage(page + 1)}>Next choices</Button>
        </div></div>
      </>}
    </DrawerBody>
  </OverlayDrawer>;
}

function Collections({ data, onPage }) {
  const money = value => statementMoney(value, data.currency);
  return <>
    <section className="report-collections-summary" aria-label="Collection totals">
      <div className="report-collections-summary__primary"><span>Recorded collections</span><strong>{money(data.totals.amount)}</strong><span>{data.totals.payments} recorded {data.totals.payments === 1 ? "payment" : "payments"}</span></div>
      <dl>{Object.entries(paymentMethods).map(([key, label]) => <div key={key}><dt>{label}</dt><dd>{money(data.by_method[key])}</dd></div>)}</dl>
    </section>
    <section className="portal-statement__activity">
      <div className="portal-statement__activity-heading"><h2>Recorded payments</h2><span>{data.total_rows} {data.total_rows === 1 ? "payment" : "payments"}</span></div>
      {!data.rows.length ? <div className="portal-statement__empty"><h3>No collections in this period</h3><p>Try another period or change the filters.</p></div> : <>
        <div className="portal-statement__desktop"><table className="dwella-table report-collections-table"><caption className="portal-statement__sr-only">Recorded collections in {data.currency}</caption>
          <thead><tr>{["Paid on", "Receipt / invoice", "Tenant", "Property / unit", "Method", `Amount (${data.currency})`].map(label => <th key={label} scope="col">{label}</th>)}</tr></thead>
          <tbody>{data.rows.map(row => <tr key={row.id}><td>{formatDate(row.paid_on)}</td>
            <td><strong>{row.receipt}</strong><div><Link to={`/billing/invoices/${row.invoice_id}`}>{row.invoice}</Link></div></td>
            <td>{row.tenant}</td><td>{row.property}<div className="dwella-muted-copy">{row.unit}</div></td>
            <td>{paymentMethods[row.method]}</td><td className="is-numeric">{statementMoney(row.amount, data.currency, false)}</td></tr>)}</tbody>
        </table></div>
        <ul className="portal-statement__mobile portal-statement__entries">{data.rows.map(row => <li key={row.id}>
          <div className="portal-statement__entry-heading"><strong>{row.tenant}</strong><strong>{money(row.amount)}</strong></div>
          <div className="portal-statement__entry-context"><time dateTime={row.paid_on}>{formatDate(row.paid_on)}</time><span>{row.property} · {row.unit}</span></div>
          <div className="report-collection-reference"><Link to={`/billing/invoices/${row.invoice_id}`}>{row.receipt} · {row.invoice}</Link><span>{paymentMethods[row.method]}</span></div>
        </li>)}</ul>
      </>}
      <footer className="portal-statement__pagination"><span>Page {data.page} of {data.total_pages}</span><div>
        <Button disabled={data.page <= 1} onClick={() => onPage(data.page - 1)}>Previous</Button>
        <Button disabled={data.page >= data.total_pages} onClick={() => onPage(data.page + 1)}>Next</Button>
      </div></footer>
    </section>
  </>;
}

export default function ActivityReports({ report }) {
  const [, setParams] = useSearchParams();
  const { data: user } = useCurrentUserQuery();
  const org = user?.memberships?.find(row => row.is_active && row.organization?.id === user?.access?.organization_id)?.organization
    || user?.memberships?.find(row => row.is_active)?.organization;
  let today;
  try { today = workspaceToday(org?.timezone); } catch { today = workspaceToday(); }
  const [period, setPeriod] = useState(null);
  const [draft, setDraft] = useState(null);
  const [tenant, setTenant] = useState(null);
  const [property, setProperty] = useState(null);
  const [method, setMethod] = useState("");
  const [page, setPage] = useState(1);
  const [picker, setPicker] = useState(null);
  const tenantTrigger = useRef(null), propertyTrigger = useRef(null);
  const statement = report === "tenant-statement";
  const filters = { ...period, tenant: tenant?.id, property: property?.id, method, page };
  const query = useActivityReport(report, filters);
  const download = useExportActivityReport();
  const data = query.data;
  const effectiveToday = data?.as_of || today;
  const shown = draft || period || (data ? { date_from: data.date_from, date_to: data.date_to } : { date_from: `${today.slice(0, 7)}-01`, date_to: today });
  const errors = statementDateErrors(shown, effectiveToday);
  const reset = () => { setPage(1); download.reset(); };
  const closePicker = () => { const kind = picker; setPicker(null); requestAnimationFrame(() => (kind === "tenant" ? tenantTrigger : propertyTrigger).current?.focus()); };
  const pinPeriod = () => { if (data) setPeriod({ date_from: data.date_from, date_to: data.date_to }); };
  return <div className="portal-statement manager-activity-report">
    <PageActions><Button icon={<ArrowDownload20Regular />} disabled={!data || query.isError || query.isFetching || download.isPending}
      onClick={() => download.mutate({ report, filters: { ...filters, date_from: data.date_from, date_to: data.date_to } })}>
      {download.isPending ? "Exporting…" : "Export CSV"}</Button></PageActions>
    <SegmentedFilter label="Choose report" options={reportOptions} value={report} onChange={value => setParams(current => { const next = new URLSearchParams(current); next.set("report", value); return next; })} />
    <section className="report-filter-panel" aria-label="Report filters">
      <form className="report-filter-panel__dates" noValidate onSubmit={event => { event.preventDefault(); if (!Object.keys(errors).length) { setPeriod(shown); setDraft(null); reset(); } }}>
        {[["date_from", "From"], ["date_to", "To"]].map(([key, label]) => <Field key={key} label={label} required validationState={errors[key] ? "error" : "none"} validationMessage={errors[key]}>
          <Input type="date" max={effectiveToday} value={shown[key]} onChange={(_, next) => setDraft({ ...shown, [key]: next.value })} />
        </Field>)}
        <Button type="submit" disabled={Boolean(Object.keys(errors).length)}>Apply dates</Button>
      </form>
      <div className="report-filter-panel__scope">
        <Field label="Property"><Button ref={propertyTrigger} onClick={() => setPicker("property")}>{property?.name || "All properties"}</Button></Field>
        <Field label={statement ? "Tenant (required)" : "Tenant"}><Button ref={tenantTrigger} onClick={() => setPicker("tenant")}>{tenant ? `${tenant.name}${tenant.archived ? " · Archived" : ""}` : statement ? "Choose tenant" : "All tenants"}</Button></Field>
        {!statement && <Field label="Payment method"><Select value={method} onChange={(_, next) => { pinPeriod(); setMethod(next.value); reset(); }}><option value="">All methods</option>
          {Object.entries(paymentMethods).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</Select></Field>}
      </div>
    </section>
    <p className="portal-statement__basis">{statement ? "Current ledger restated for the selected period, including later corrections. Deposits are shown separately; negative balances are credits."
      : "Gross recorded payments by payment date. Reversed payments and void invoices are excluded. This is not net settlement."}</p>
    {statement && !tenant ? <section className="portal-statement__activity"><h2>Choose a tenant to view their statement</h2><p>Search active or archived tenants. Each statement includes recorded charges, payments and running balances.</p><Button onClick={() => setPicker("tenant")}>Choose tenant account</Button></section>
      : query.isPending ? <div className="portal-statement__loading" role="status" aria-busy="true"><span>Loading report…</span><div className="dwella-skeleton" /><div className="dwella-skeleton" /></div>
        : query.isError ? <section className="dwella-surface portal-statement__error" role="alert"><h2>Could not load this report</h2>
          <p>{[403, 404].includes(query.error?.status) ? "Your access may have changed. Check your workspace and report selection." : query.error?.status === 400 ? "Check your filters. If records changed, return to the first page." : "Try again to load the recorded activity."}</p>
          <div><Button onClick={() => query.refetch()}>Retry report</Button>{page > 1 && <Button onClick={() => setPage(1)}>First page</Button>}</div></section>
          : data && <>{statement ? <><div className="report-tenant-context"><h2>{data.tenant.name}</h2>{data.tenant.archived && <span>Archived tenant</span>}</div><StatementBalances data={data} /><StatementActivity data={data} onPage={next => { pinPeriod(); setPage(next); download.reset(); }} /></>
            : <Collections data={data} onPage={next => { pinPeriod(); setPage(next); download.reset(); }} />}</>}
    {download.isError && <p role="alert">{download.error?.status === 429 ? "CSV download limit reached. Try again later." : "Could not export this report. Check your access and try again."}</p>}
    {picker && <ScopePicker kind={picker} onClose={closePicker} onChoose={value => { pinPeriod(); if (picker === "tenant") setTenant(value); else setProperty(value); reset(); closePicker(); }} />}
  </div>;
}
