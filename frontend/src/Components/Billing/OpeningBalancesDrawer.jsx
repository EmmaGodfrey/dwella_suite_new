import React, { useEffect, useMemo, useState } from "react";
import { Button, Field, Input, Select } from "@fluentui/react-components";
import { Search20Regular } from "@fluentui/react-icons";
import { toast } from "react-toastify";

import { useOpeningBalances, useSaveOpeningBalances } from "../../Services/payments";
import { periodLabel } from "../../shared/billing";
import { SegmentedFilter, StatusBadge } from "../../shared/components";
import { FormDrawer } from "../../shared/components/FormFlow";
import { formatMoney } from "../../shared/format";
import { useFormErrors } from "../../shared/useFormErrors";
import "../../shared/records.scss";
import "./billing.scss";

const PAGE_SIZE = 10;
const MAX_ROWS = 25;
const MAX_MONTHS = 36;
const FIELDS = ["owes", "owed_since", "rent_paid_up_to", "deposit_held"];

const today = () => new Date().toLocaleDateString("en-CA");
const monthIso = (date) => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-01`;
const nextMonth = (iso) => {
  const [year, month] = iso.split("-").map(Number);
  return monthIso(new Date(year, month, 1));
};
const shortMonth = (iso) => {
  const [year, month] = iso.split("-").map(Number);
  return new Date(year, month - 1, 1).toLocaleDateString("en-GB", { month: "short", year: "numeric" });
};
const notPositive = (value) => !(Number(value) > 0);
const plural = (count) => `${count} ${count === 1 ? "tenancy" : "tenancies"}`;

// This month up to the month the lease ends, plus any month already saved.
function paidUpToOptions(row) {
  const start = new Date();
  const [endYear, endMonth] = row.end_date.split("-").map(Number);
  const last = monthIso(new Date(endYear, endMonth - 1, 1));
  const months = [];
  for (let offset = 0; offset < MAX_MONTHS; offset += 1) {
    const value = monthIso(new Date(start.getFullYear(), start.getMonth() + offset, 1));
    if (value > last) break;
    months.push(value);
  }
  if (row.rent_paid_up_to && !months.includes(row.rent_paid_up_to)) months.unshift(row.rent_paid_up_to);
  return months;
}

const debtRecorded = (row) => Boolean(row.opening_balance);
const depositRecorded = (row) => Number(row.deposit_held) > 0;
const isRecorded = (row) => debtRecorded(row) || depositRecorded(row) || Boolean(row.rent_paid_up_to);

// Only what the manager entered: the API refuses zero amounts, and leaving
// rent_paid_up_to out keeps what is saved.
function rowPayload(row, draft = {}) {
  const payload = {};
  if (draft.owes?.trim()) payload.owes = draft.owes.trim();
  if (draft.owed_since) payload.owed_since = draft.owed_since;
  if (draft.deposit_held?.trim()) payload.deposit_held = draft.deposit_held.trim();
  if (draft.rent_paid_up_to !== undefined && draft.rent_paid_up_to !== (row.rent_paid_up_to || "")) {
    payload.rent_paid_up_to = draft.rent_paid_up_to || null;
  }
  return payload;
}

// {rows: {"0": {owes: [...]}}} becomes {"<lease>": {owes: [...]}} for the form.
function errorsByLease(data, sent) {
  const rows = data?.rows;
  if (!rows || typeof rows !== "object" || Array.isArray(rows) && typeof rows[0] === "string") return null;
  const found = {};
  Object.entries(rows).forEach(([index, value]) => {
    const row = sent[Number(index)];
    if (!row || !value || !Object.keys(value).length) return;
    found[row.lease] = Array.isArray(value) ? { owes: value } : value;
  });
  return found;
}

function TenancyRow({ row, draft, change, fieldProps }) {
  const name = (field) => `${row.lease}.${field}`;
  const paidUpTo = draft?.rent_paid_up_to ?? row.rent_paid_up_to ?? "";
  const debt = row.opening_balance;
  const held = depositRecorded(row);
  const recorded = [
    debt ? `${debt.reference}: ${formatMoney(debt.owed)} brought forward, ${formatMoney(debt.balance)} still owed` : "",
    held ? `Deposit ${formatMoney(row.deposit_held)} held` : "",
  ].filter(Boolean).join(" · ");
  return (
    <li className="dwella-opening-row">
      <div className="dwella-opening-heading">
        <p><strong>{row.tenant}</strong> <small>{row.premises} · Rent {formatMoney(row.monthly_rent)}</small></p>
        {isRecorded(row) ? <StatusBadge color="success">Recorded</StatusBadge> : null}
      </div>
      {recorded ? <p className="dwella-opening-recorded">{recorded}</p> : null}
      <div className="dwella-opening-fields">
        {debt ? null : (
          <>
            <Field label="Owes (ZMW)" {...fieldProps(name("owes"))}>
              <Input inputMode="decimal" placeholder="0.00" value={draft?.owes || ""} onChange={(_, d) => change(row, "owes", d.value)} />
            </Field>
            <Field label="Owed since" {...fieldProps(name("owed_since"))}>
              <Input type="date" max={today()} value={draft?.owed_since || ""} onChange={(_, d) => change(row, "owed_since", d.value)} />
            </Field>
          </>
        )}
        {/* Stays editable: a wrong month silently stops billing, and no other screen can correct it. */}
        <Field label="Rent paid up to" {...fieldProps(name("rent_paid_up_to"))}>
          <Select value={paidUpTo} onChange={(_, d) => change(row, "rent_paid_up_to", d.value)}>
            <option value="">Not ahead</option>
            {paidUpToOptions(row).map((month) => <option key={month} value={month}>{shortMonth(month)}</option>)}
          </Select>
        </Field>
        {held ? null : (
          <Field label="Deposit held" {...fieldProps(name("deposit_held"))}>
            <Input inputMode="decimal" placeholder="0.00" value={draft?.deposit_held || ""} onChange={(_, d) => change(row, "deposit_held", d.value)} />
          </Field>
        )}
      </div>
      {paidUpTo ? <p className="dwella-opening-note">Next rent invoice: {periodLabel(nextMonth(paidUpTo))}.</p> : null}
      {debt || held ? (
        <p className="dwella-opening-note">
          {debt ? `To correct the debt, void ${debt.reference} and enter it again. ` : ""}
          {held ? "Deposit changes are made on the lease." : ""}
        </p>
      ) : null}
    </li>
  );
}

export default function OpeningBalancesDrawer({ onClose }) {
  const [asOf, setAsOf] = useState(today);
  const [search, setSearch] = useState("");
  const [term, setTerm] = useState("");
  const [scope, setScope] = useState("pending");
  const [page, setPage] = useState(1);
  const [drafts, setDrafts] = useState({}); // lease id -> { row, values }
  const [message, setMessage] = useState("");
  const { errors, validate, clearError, clearAll, fieldProps, showServerErrors } = useFormErrors();
  const save = useSaveOpeningBalances();

  useEffect(() => {
    const timeout = setTimeout(() => { setTerm(search.trim()); setPage(1); }, 300);
    return () => clearTimeout(timeout);
  }, [search]);

  const pending = scope === "pending";
  const list = useOpeningBalances(
    { page, page_size: PAGE_SIZE, ...(term ? { search: term } : {}), ...(pending ? { pending: "true" } : {}) },
    { placeholderData: (previous) => previous },
  );
  const pendingCount = useOpeningBalances({ page_size: 1, pending: "true" });
  const allCount = useOpeningBalances({ page_size: 1 });
  const rows = list.data?.results || [];
  const pagination = list.data?.pagination;

  const scopes = [
    { value: "pending", label: `Still to do${pendingCount.data ? ` · ${pendingCount.data.pagination.count}` : ""}` },
    { value: "all", label: `All active leases${allCount.data ? ` · ${allCount.data.pagination.count}` : ""}` },
  ];

  const change = (row, field, value) => {
    setDrafts((current) => ({
      ...current,
      [row.lease]: { row, values: { ...current[row.lease]?.values, [field]: value } },
    }));
    clearError(`${row.lease}.${field}`);
    setMessage("");
  };

  const changed = useMemo(
    () => Object.values(drafts)
      .map(({ row, values }) => ({ row, values, payload: rowPayload(row, values) }))
      .filter(({ payload }) => Object.keys(payload).length),
    [drafts],
  );

  const submit = async (event) => {
    event.preventDefault();
    if (save.isPending) return;
    if (!changed.length) {
      setMessage("Enter at least one tenancy's details first.");
      return;
    }
    if (changed.length > MAX_ROWS) {
      setMessage(`Save up to ${MAX_ROWS} tenancies at a time.`);
      return;
    }
    const rules = {};
    changed.forEach(({ row, payload }) => {
      const name = (field) => `${row.lease}.${field}`;
      if (payload.owes !== undefined) rules[name("owes")] = () => (notPositive(payload.owes) ? "Enter an amount more than zero." : "");
      if (payload.owed_since) {
        rules[name("owed_since")] = () => {
          if (payload.owed_since > today()) return "The date cannot be in the future.";
          return payload.owes === undefined ? "Enter what is owed, or clear this date." : "";
        };
      }
      if (payload.deposit_held !== undefined) rules[name("deposit_held")] = () => (notPositive(payload.deposit_held) ? "Enter an amount more than zero." : "");
    });
    if (!validate(rules, event.currentTarget)) return;

    const sent = changed.map(({ row, payload }) => ({ lease: row.lease, ...payload }));
    try {
      const data = await save.mutateAsync({ as_of: asOf, rows: sent });
      toast.success(`Saved ${plural(data.saved)}.`);
      setDrafts({});
      clearAll();
      setPage(1);
    } catch (error) {
      const found = errorsByLease(error.data, sent);
      const known = sent.flatMap(({ lease }) => FIELDS.map((field) => `${lease}.${field}`));
      if (!found || !showServerErrors(found, known)) {
        setMessage(error.message || "Could not save. Nothing was changed.");
        return;
      }
      // A row hidden by the current search still needs to be named.
      const hidden = Object.keys(found).filter((lease) => !rows.some((row) => row.lease === lease));
      if (hidden.length) {
        const names = hidden.map((lease) => drafts[lease]?.row.tenant).filter(Boolean).join(", ");
        setMessage(`Nothing was saved. Also check ${names}.`);
      }
    }
  };

  const unsaved = changed.length > 0;
  const footer = pagination ? (
    <div className="dwella-opening-footer">
      <p>
        Showing {rows.length} of {pagination.count}{pending ? " still to do" : ""}
        {pagination.total_pages > 1 ? ` · Page ${page} of ${pagination.total_pages}. Save this page before moving to the next.` : "."}
      </p>
      {pagination.total_pages > 1 ? (
        <span className="dwella-table-pager">
          <Button size="small" disabled={!pagination.previous || unsaved} onClick={() => setPage((value) => value - 1)}>Previous</Button>
          <Button size="small" disabled={!pagination.next || unsaved} onClick={() => setPage((value) => value + 1)}>Next</Button>
        </span>
      ) : null}
    </div>
  ) : null;

  return (
    <FormDrawer
      title="Opening balances"
      description="Record where each existing tenancy stands today. Nothing is sent to tenants."
      onClose={onClose}
      onSubmit={submit}
      busy={save.isPending}
      errors={errors}
      submitLabel={unsaved ? `Save ${plural(changed.length)}` : "Save"}
      pendingLabel="Saving…"
      notice={footer}
    >
      <div className="dwella-opening">
        {message ? <p role="alert" className="dwella-alert danger">{message}</p> : null}
        <div className="dwella-opening-controls">
          <Field label="Balances as of">
            <Input type="date" max={today()} value={asOf} onChange={(_, d) => d.value && setAsOf(d.value)} />
          </Field>
          <Field label="Find a tenancy">
            <Input contentBefore={<Search20Regular />} placeholder="Tenant, unit or lease" value={search} onChange={(_, d) => setSearch(d.value)} />
          </Field>
        </div>
        <SegmentedFilter label="Which tenancies" options={scopes} value={scope} onChange={(value) => { setScope(value); setPage(1); }} />
        <div className="dwella-soft-note">
          <strong>Old debt becomes one “Balance brought forward” invoice</strong>
          <span>The tenant can pay it straight away. No notice or late fee goes out, and months already paid are never billed again.</span>
        </div>
        {list.isLoading ? <span className="dwella-skeleton" style={{ height: 160, width: "100%" }} /> : null}
        {list.isError ? (
          <p role="alert" className="dwella-alert danger">
            Could not load your leases. <Button size="small" onClick={() => list.refetch()}>Retry</Button>
          </p>
        ) : null}
        {!list.isLoading && !list.isError && !rows.length ? (
          <p className="dwella-muted-copy">
            {term ? "No tenancies match this search." : pending ? "Every active lease has been recorded." : "No active leases yet. Activate a lease first."}
          </p>
        ) : null}
        <ul className="dwella-opening-list" aria-busy={list.isFetching}>
          {rows.map((row) => (
            <TenancyRow key={row.lease} row={row} draft={drafts[row.lease]?.values} change={change} fieldProps={fieldProps} />
          ))}
        </ul>
      </div>
    </FormDrawer>
  );
}
