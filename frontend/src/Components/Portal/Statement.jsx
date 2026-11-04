import React, { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  Button, DrawerBody, DrawerHeader, DrawerHeaderTitle, Field, Input, OverlayDrawer,
} from "@fluentui/react-components";
import { ArrowLeft20Regular, Dismiss20Regular } from "@fluentui/react-icons";

import { useCurrentUserQuery } from "../../Services/queries";
import { useExportStatement, usePortalStatement, useStatementAccounts } from "../../Services/portalStatements";
import { formatDate } from "../../shared/format";
import { statementDateErrors, statementMoney, workspaceToday } from "../../shared/statement.mjs";
import "../../shared/records.scss";
import "./statement.scss";

function PeriodForm({ initial, today, onApply, disabled = false }) {
  const [draft, setDraft] = useState(initial);
  const [touched, setTouched] = useState(false);
  const errors = statementDateErrors(draft, today);
  return (
    <form className="portal-statement__dates" noValidate onSubmit={(event) => {
      event.preventDefault(); setTouched(true);
      if (!Object.keys(errors).length) onApply(draft);
    }}>
      {[ ["date_from", "From"], ["date_to", "To"] ].map(([key, label]) => (
        <Field key={key} label={label} required validationState={touched && errors[key] ? "error" : "none"}
          validationMessage={touched ? errors[key] : undefined}>
          <Input type="date" value={draft[key]} max={today} disabled={disabled}
            onChange={(_, data) => { setTouched(true); setDraft((current) => ({ ...current, [key]: data.value })); }} />
        </Field>
      ))}
      <Button type="submit" disabled={disabled || Boolean(Object.keys(errors).length)}>Apply dates</Button>
    </form>
  );
}

function Sheet({ title, onClose, children }) {
  return (
    <OverlayDrawer open position="bottom" className="portal-statement-sheet" onOpenChange={(_, data) => !data.open && onClose()}>
      <DrawerHeader>
        <DrawerHeaderTitle action={<Button appearance="subtle" icon={<Dismiss20Regular />} aria-label="Close" onClick={onClose} />}>
          {title}
        </DrawerHeaderTitle>
      </DrawerHeader>
      <DrawerBody>{children}</DrawerBody>
    </OverlayDrawer>
  );
}

function LoadError({ error, retry }) {
  const lost = [403, 404].includes(error?.status);
  return (
    <section className="dwella-surface portal-statement__error" role="alert">
      <h2>{lost ? "Your account access changed" : "Could not load your statement"}</h2>
      <p>{lost ? "This statement is no longer available here. Ask your property manager to check your tenant invitation."
        : error?.status === 400 ? "Check the statement period and page, then try again." : "Try again. Your recorded charges and payments have not changed."}</p>
      <div className="portal-statement__error-actions">
        <Button onClick={retry}>Retry</Button>
        {lost && <Button as={Link} to="/dashboard" appearance="subtle">Back to home</Button>}
      </div>
    </section>
  );
}

function StatementBalances({ data }) {
  const money = (value, full = false) => statementMoney(value, data.currency, full);
  return (
    <section className="portal-statement__balance" aria-label="Period balances">
      <div className="portal-statement__balance-heading">
        <div><span>Closing balance</span><strong>{money(data.totals.closing_balance, true)}</strong></div>
        <span className="portal-statement__as-of">{formatDate(data.date_to)}</span>
      </div>
      {data.totals.closing_balance.startsWith("-") && <p className="portal-statement__credit">Credit balance</p>}
      <dl className="portal-statement__facts">
        {[ ["Opening", "Opening balance", "opening_balance"], ["Charges", "Charges in this period", "charges"],
          ["Payments", "Payments in this period", "payments"] ].map(([short, label, key]) => (
          <div key={key}><dt><span className="portal-statement__desktop">{label}</span><span className="portal-statement__mobile">{short}</span></dt>
            <dd>{money(data.totals[key])}</dd></div>
        ))}
      </dl>
    </section>
  );
}

function Activity({ data, onPage }) {
  const money = (value, full = false) => statementMoney(value, data.currency, full);
  const home = (row) => [row.property, row.unit].filter(Boolean).join(" · ");
  const label = (row) => `${row.type === "charge" ? "Charge" : "Payment"} · ${row.reference}`;
  return (
    <section className="portal-statement__activity" aria-labelledby="statement-activity-heading">
      <div className="portal-statement__activity-heading"><h2 id="statement-activity-heading">Account activity</h2>
        <span>{data.total_rows} {data.total_rows === 1 ? "entry" : "entries"}</span></div>
      {!data.rows.length ? <div className="portal-statement__empty"><h3>No activity in this period</h3>
        <p>Your opening and closing balances are included in the CSV.</p></div> : <>
        <div className="portal-statement__desktop">
          <table className="dwella-table portal-statement__table">
            <caption className="portal-statement__sr-only">Charges, payments and running balance in {data.currency}</caption>
            <thead><tr><th scope="col">Date</th><th scope="col">Activity / reference</th><th scope="col">Home</th>
              <th scope="col" className="is-numeric">Charges ({data.currency})</th><th scope="col" className="is-numeric">Payments ({data.currency})</th>
              <th scope="col" className="is-numeric">Balance ({data.currency})</th></tr></thead>
            <tbody>{data.rows.map((row) => <tr key={`${row.type}-${row.id}`}>
              <td>{formatDate(row.date)}</td><td>{label(row)}</td><td>{home(row)}</td>
              <td className="is-numeric">{row.type === "charge" ? money(row.debit) : "—"}</td>
              <td className="is-numeric">{row.type === "payment" ? money(row.credit) : "—"}</td>
              <td className="is-numeric">{money(row.balance)}</td>
            </tr>)}</tbody>
          </table>
        </div>
        <ul className="portal-statement__mobile portal-statement__entries">
          {data.rows.map((row) => <li key={`${row.type}-${row.id}`}>
            <div className="portal-statement__entry-heading"><strong>{label(row)}</strong><strong>{money(row.type === "charge" ? row.debit : row.credit)}</strong></div>
            <div className="portal-statement__entry-context"><time dateTime={row.date}>{formatDate(row.date)}</time><span>{home(row)}</span></div>
            <p className="portal-statement__running">Balance {money(row.balance, true)}</p>
          </li>)}
        </ul>
      </>}
      <footer className="portal-statement__pagination">
        <span>Page {data.page} of {data.total_pages}</span>
        <div><Button disabled={data.page <= 1} onClick={() => onPage(data.page - 1)}>Previous</Button>
          <Button disabled={data.page >= data.total_pages} onClick={() => onPage(data.page + 1)}>Next</Button></div>
      </footer>
    </section>
  );
}

export default function PortalStatement() {
  const { data: user } = useCurrentUserQuery({ staleTime: 60_000 });
  const [accountPage, setAccountPage] = useState(1);
  const accounts = useStatementAccounts(accountPage);
  const [selection, setSelection] = useState(null);
  const [accountsOpen, setAccountsOpen] = useState(false);
  const [periodOpen, setPeriodOpen] = useState(false);
  const [period, setPeriod] = useState(null);
  const [page, setPage] = useState(1);
  const periodTrigger = useRef(null);
  const accountTrigger = useRef(null);
  const accountCount = accounts.data?.pagination.count;
  const account = selection || (accountCount === 1 ? accounts.data.results[0] : null);
  const query = usePortalStatement(!accounts.isError ? account?.id : null, period, page);
  const download = useExportStatement();
  const data = query.data;
  const organization = user?.memberships?.find((row) => row.is_active && row.organization?.id === user?.access?.organization_id)?.organization
    || user?.memberships?.find((row) => row.is_active)?.organization;
  let localToday;
  try { localToday = workspaceToday(organization?.timezone); } catch { localToday = workspaceToday(); }
  const today = data?.as_of || localToday;
  const shownPeriod = period || (data ? { date_from: data.date_from, date_to: data.date_to }
    : { date_from: `${today.slice(0, 7)}-01`, date_to: today });
  const exportAccessError = [403, 404].includes(download.error?.status) ? download.error : null;
  const error = accounts.error || query.error || exportAccessError;
  const ready = Boolean(account && data && !error && !accounts.isPending);
  const periodKey = `${account?.id}:${shownPeriod.date_from}:${shownPeriod.date_to}`;

  useEffect(() => { if (accountCount > 1 && !selection) setAccountsOpen(true); }, [accountCount, selection]);
  const closePeriod = () => { setPeriodOpen(false); requestAnimationFrame(() => periodTrigger.current?.focus()); };
  const closeAccounts = () => { setAccountsOpen(false); requestAnimationFrame(() => accountTrigger.current?.focus()); };
  const apply = (next) => { setPeriod(next); setPage(1); closePeriod(); download.reset(); };
  const retry = () => { download.reset(); accounts.refetch(); if (account) query.refetch(); };
  const chooseAccount = (next) => {
    setSelection(next); setPage(1); closeAccounts(); download.reset();
  };
  const exportCsv = () => download.mutate({ accountId: account.id, date_from: data.date_from, date_to: data.date_to });
  const downloadButton = (className) => <Button className={className} appearance="primary" disabled={!ready || query.isFetching || download.isPending}
    onClick={exportCsv}>{download.isPending ? "Downloading…" : "Download CSV"}</Button>;

  return (
    <div className="portal-statement">
      <header className="portal-statement__header">
        <div className="portal-statement__title">
          <Button as={Link} to="/billing" className="portal-statement__mobile" icon={<ArrowLeft20Regular />} aria-label="Back to payments" />
          <div><h1>Statement</h1><p>{account?.name || "Your recorded charges and payments"}<span className="portal-statement__desktop">{account ? " · Recorded charges and payments" : ""}</span></p></div>
        </div>
        {downloadButton("portal-statement__desktop")}
      </header>
      {accountCount > 1 && <div className="portal-statement__account">
        <span>{account ? `Tenant account: ${account.name}` : "Choose a tenant account to view its statement."}</span>
        <Button ref={accountTrigger} onClick={() => setAccountsOpen(true)} disabled={download.isPending}>Change account</Button>
      </div>}
      {account && <>
        <section className="portal-statement__period portal-statement__desktop" aria-label="Statement period">
          <PeriodForm key={periodKey} initial={shownPeriod} today={today} onApply={apply} disabled={download.isPending || accounts.isPending} />
        </section>
        <section className="portal-statement__period-compact portal-statement__mobile" aria-label="Statement period">
          <div><strong>Statement period</strong><span>{formatDate(shownPeriod.date_from)}–{formatDate(shownPeriod.date_to)}</span></div>
          <Button ref={periodTrigger} appearance="subtle" onClick={() => setPeriodOpen(true)} disabled={download.isPending}>Change</Button>
        </section>
      </>}
      {error ? <LoadError error={error} retry={retry} /> : accounts.isPending || (account && query.isPending) ? (
        <div className="portal-statement__loading" role="status" aria-busy="true"><span>Loading your statement…</span>
          <div className="dwella-skeleton" /><div className="dwella-skeleton" /></div>
      ) : ready ? <>
        <StatementBalances data={data} />
        {downloadButton("portal-statement__mobile portal-statement__download")}
        <Activity data={data} onPage={(next) => { setPeriod({ date_from: data.date_from, date_to: data.date_to }); setPage(next); }} />
        <p className="portal-statement__basis">Includes later corrections. Negative balances are credits. Deposits are shown separately.</p>
      </> : !account && !accounts.isPending && <section className="dwella-surface"><h2>Choose your tenant account</h2>
        <p>Each account has its own statement.</p><Button onClick={() => setAccountsOpen(true)}>Choose account</Button></section>}
      {download.isError && !exportAccessError && <p role="alert" className="portal-statement__export-error">
        {download.error?.status === 429 ? "You have reached the CSV download limit. Try again later; you can still view your statement." : "Could not download the CSV. Please try again."}
      </p>}
      {periodOpen && <Sheet title="Statement period" onClose={closePeriod}>
        <PeriodForm key={periodKey} initial={shownPeriod} today={today} onApply={apply} />
        <p className="portal-statement__basis">Choose up to 366 days, ending today or earlier.</p>
      </Sheet>}
      {accountsOpen && <Sheet title="Choose tenant account" onClose={closeAccounts}>
        <p>Each account has its own statement.</p>
        {accounts.isPending ? <p role="status">Loading accounts…</p> : accounts.isError ? <LoadError error={accounts.error} retry={() => accounts.refetch()} /> : <>
          <div className="portal-statement__account-options">{accounts.data?.results.map((row, index) => <Button key={row.id}
            aria-pressed={row.id === account?.id} onClick={() => chooseAccount(row)}>
            {row.name} · account {(accountPage - 1) * 50 + index + 1}
          </Button>)}</div>
          {accounts.data?.pagination.total_pages > 1 && <div className="portal-statement__pagination">
            <span>Page {accountPage} of {accounts.data.pagination.total_pages}</span><div>
              <Button disabled={accountPage <= 1} onClick={() => setAccountPage(accountPage - 1)}>Previous</Button>
              <Button disabled={accountPage >= accounts.data.pagination.total_pages} onClick={() => setAccountPage(accountPage + 1)}>Next</Button>
            </div></div>}
        </>}
      </Sheet>}
    </div>
  );
}
