import React, { useState } from "react";
import {
  Button, DrawerBody, DrawerFooter, DrawerHeader, DrawerHeaderTitle, Field, Input,
  OverlayDrawer, Select, Textarea,
} from "@fluentui/react-components";
import { Dismiss20Regular } from "@fluentui/react-icons";
import { toast } from "react-toastify";
import { useDeductionDecision, useDeposit, useDepositAction } from "../../Services/payments";
import { EmptyState, StatusBadge } from "../../shared/components";
import { FormDrawer } from "../../shared/components/FormFlow";
import { formatDate, formatMoney } from "../../shared/format";
import { useFormErrors } from "../../shared/useFormErrors";
import "./deposits.scss";

const today = () => new Date().toLocaleDateString("en-CA");
const methods = [
  ["bank_transfer", "Bank transfer"], ["mobile_money", "Mobile money"], ["cash", "Cash"], ["cheque", "Cheque"],
];
const deductionColor = { proposed: "warning", accepted: "informative", disputed: "danger", applied: "success", withdrawn: "subtle" };
const positive = (value) => Number(value) > 0;

/** One form per action, sharing validation and server error handling. */
function ActionDrawer({ leaseId, action, deposit, onClose }) {
  const config = {
    request: {
      title: "Request deposit", submit: "Send deposit invoice",
      description: "Issues a deposit invoice the tenant can pay online or directly. It is kept separate from rent.",
      initial: { amount: deposit.outstanding },
    },
    opening: {
      title: "Deposit already held", submit: "Record deposit",
      description: "For a deposit the tenant paid before using Dwella. No new receipt is issued.",
      initial: { amount: deposit.outstanding, occurred_on: today(), note: "" },
    },
    deductions: {
      title: "Propose deduction", submit: "Send to tenant",
      description: "The amount is reserved, not deducted, until the tenant accepts or the dispute is resolved. Fair wear and tear is not deductible.",
      initial: { amount: "", reason: "", details: "" },
    },
    refunds: {
      title: "Record refund", submit: "Record refund",
      description: "Record a refund you have already paid. Amounts reserved for open deductions stay held.",
      initial: { amount: deposit.available, method: "bank_transfer", reference: "", paid_on: today(), note: "" },
    },
  }[action];
  const [form, setForm] = useState(config.initial);
  const [message, setMessage] = useState("");
  const mutation = useDepositAction(leaseId);
  const { errors, validate, clearError, fieldProps, showServerErrors } = useFormErrors();
  const change = (key, value) => { setForm((f) => ({ ...f, [key]: value })); clearError(key); setMessage(""); };
  const limit = action === "refunds" || action === "deductions" ? Number(deposit.available) : null;
  const submit = async (event) => {
    event.preventDefault();
    if (mutation.isPending) return;
    if (!validate({
      amount: () => !positive(form.amount) ? "Enter an amount more than zero."
        : limit !== null && Number(form.amount) > limit ? `Only ${formatMoney(limit)} is available.` : "",
      ...(action === "deductions" ? { reason: () => !form.reason.trim() ? "Say what the deduction is for." : "" } : {}),
      ...(form.occurred_on !== undefined ? { occurred_on: () => !form.occurred_on || form.occurred_on > today() ? "Choose a date that is not in the future." : "" } : {}),
      ...(form.paid_on !== undefined ? { paid_on: () => !form.paid_on || form.paid_on > today() ? "Choose a date that is not in the future." : "" } : {}),
    }, event.currentTarget)) return;
    try {
      await mutation.mutateAsync({ action, ...form });
      toast.success({ request: "Deposit invoice sent.", opening: "Deposit recorded.", deductions: "Deduction sent to the tenant.", refunds: "Refund recorded." }[action]);
      onClose();
    } catch (error) {
      if (!showServerErrors(error.data, Object.keys(form))) setMessage(error.message || "Could not save this.");
    }
  };
  const text = (key, label, props = {}) => <Field label={label} {...fieldProps(key)} {...props.field}>
    <Input value={form[key]} onChange={(_, d) => change(key, d.value)} {...props.input} />
  </Field>;
  return <FormDrawer title={config.title} description={config.description} onClose={onClose} onSubmit={submit}
    busy={mutation.isPending} errors={errors} submitLabel={config.submit} pendingLabel="Saving…">
    <div className="dwella-receiving-fields">
      {message && <p role="alert" className="dwella-alert danger">{message}</p>}
      {text("amount", "Amount (ZMW)", { field: { required: true, hint: limit !== null ? `Available: ${formatMoney(limit)}` : undefined }, input: { inputMode: "decimal" } })}
      {action === "deductions" && <>
        {text("reason", "What it is for", { field: { required: true }, input: { maxLength: 200, placeholder: "e.g. Replace broken bedroom door lock" } })}
        <Field label="Details for the tenant" {...fieldProps("details")}>
          <Textarea value={form.details} maxLength={2000} onChange={(_, d) => change("details", d.value)}
            placeholder="What was found, when, and how the amount was worked out (quote or receipt)." />
        </Field>
      </>}
      {action === "opening" && text("occurred_on", "Date it was paid", { field: { required: true }, input: { type: "date", max: today() } })}
      {action === "refunds" && <>
        <Field label="Paid by" {...fieldProps("method")}>
          <Select value={form.method} onChange={(_, d) => change("method", d.value)}>
            {methods.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </Select>
        </Field>
        {text("reference", "Payment reference", { input: { maxLength: 100 } })}
        {text("paid_on", "Date paid", { field: { required: true }, input: { type: "date", max: today() } })}
      </>}
      {(action === "opening" || action === "refunds") && text("note", "Note", { input: { maxLength: 500 } })}
    </div>
  </FormDrawer>;
}

function Deduction({ row, leaseId }) {
  const decide = useDeductionDecision(leaseId);
  const [resolution, setResolution] = useState("");
  const [resolving, setResolving] = useState(false);
  const open = ["proposed", "accepted", "disputed"].includes(row.status);
  const run = async (decision) => {
    try {
      await decide.mutateAsync({ id: row.id, decision, resolution_note: resolution });
      toast.success(decision === "apply" ? "Deduction applied." : "Deduction withdrawn.");
    } catch (error) {
      toast.error(error.data?.resolution_note?.[0] || error.message || "Could not update this deduction.");
    }
  };
  return <article className="dwella-deposit-deduction">
    <div className="dwella-deposit-deduction-head">
      <strong>{row.reason}</strong>
      <strong>{formatMoney(row.amount)}</strong>
    </div>
    <p className="dwella-deposit-muted">Proposed {formatDate(row.proposed_on)}{row.details ? ` · ${row.details}` : ""}</p>
    <div className="dwella-deposit-status">
      <StatusBadge color={deductionColor[row.status]}>{row.status_label}</StatusBadge>
      {row.tenant_note && <span>Tenant: “{row.tenant_note}”</span>}
      {row.resolution_note && <span>Resolution: {row.resolution_note}</span>}
    </div>
    {open && <div className="dwella-deposit-row-actions">
      {row.status === "disputed" && resolving && <Field label="How was the dispute resolved?" className="dwella-deposit-resolution">
        <Textarea value={resolution} maxLength={1000} onChange={(_, d) => setResolution(d.value)} />
      </Field>}
      {row.status === "accepted" && <Button size="small" appearance="primary" disabled={decide.isPending} onClick={() => run("apply")}>Apply deduction</Button>}
      {row.status === "disputed" && (resolving
        ? <Button size="small" appearance="primary" disabled={decide.isPending || !resolution.trim()} onClick={() => run("apply")}>Apply after resolution</Button>
        : <Button size="small" onClick={() => setResolving(true)}>Resolve and apply</Button>)}
      <Button size="small" appearance="subtle" disabled={decide.isPending} onClick={() => run("withdraw")}>Withdraw</Button>
    </div>}
  </article>;
}

export function DepositSummary({ deposit }) {
  return <section className="dwella-deposit-summary" aria-label="Deposit balance">
    <div className="dwella-deposit-held">
      <div><span>Held for tenant</span><strong>{formatMoney(deposit.held)}</strong></div>
      <StatusBadge color="success">Refundable</StatusBadge>
    </div>
    <dl className="dwella-deposit-figures">
      <div><dt>Agreed in lease</dt><dd>{formatMoney(deposit.agreed)}</dd></div>
      <div><dt>Reserved for deductions</dt><dd>{formatMoney(deposit.reserved)}</dd></div>
      <div><dt>Available to refund</dt><dd className="is-positive">{formatMoney(deposit.available)}</dd></div>
    </dl>
    {positive(deposit.requested_unpaid) && <p className="dwella-deposit-muted">{formatMoney(deposit.requested_unpaid)} invoiced and not yet paid.</p>}
    <p className="dwella-deposit-muted">Recorded as money held for the tenant, separate from rent. Dwella records the deposit; it does not hold or protect the funds.</p>
  </section>;
}

export function DepositHistory({ entries }) {
  if (!entries.length) return <p className="dwella-deposit-muted">Nothing recorded yet.</p>;
  return <ol className="dwella-deposit-history">
    {entries.map((entry) => <li key={entry.id} className={Number(entry.amount) < 0 ? "is-out" : "is-in"}>
      <span className="dwella-deposit-date">{formatDate(entry.date)}</span>
      <div>
        <strong>{entry.label}</strong>
        <span>{formatMoney(Math.abs(Number(entry.amount)))}{Number(entry.amount) < 0 ? " out" : " in"}
          {entry.reference ? ` · ${entry.reference}` : ""}{entry.method ? ` · ${entry.method}` : ""}{entry.note ? ` · ${entry.note}` : ""}</span>
      </div>
    </li>)}
  </ol>;
}

export default function DepositDrawer({ lease, onClose }) {
  const query = useDeposit(lease.id);
  const [action, setAction] = useState(null);
  const deposit = query.data && {
    ...query.data,
    outstanding: Math.max(0, Number(query.data.agreed) - Number(query.data.held) - Number(query.data.requested_unpaid)).toFixed(2),
  };
  if (action && deposit) return <ActionDrawer leaseId={lease.id} action={action} deposit={deposit} onClose={() => setAction(null)} />;
  const ended = lease.status === "ended";
  return <OverlayDrawer open position="end" size="medium" className="dwella-drawer"
    onOpenChange={(_, data) => { if (!data.open) onClose(); }}>
    <DrawerHeader>
      <DrawerHeaderTitle action={<Button appearance="subtle" icon={<Dismiss20Regular />} aria-label="Close" onClick={onClose} />}>
        Security deposit
      </DrawerHeaderTitle>
      <p className="dwella-drawer-note">{lease.tenant_name} · {lease.property_name}, {lease.unit_name} · Lease {lease.reference}</p>
    </DrawerHeader>
    <DrawerBody>
      {query.isPending ? <p role="status">Loading deposit…</p>
        : query.isError ? <EmptyState title="Could not load the deposit" description={query.error.message} actionLabel="Try again" onAction={() => query.refetch()} />
          : <div className="dwella-deposit">
            <DepositSummary deposit={deposit} />
            {deposit.deductions.length > 0 && <section aria-labelledby="deposit-deductions">
              <h3 id="deposit-deductions">Deductions</h3>
              {deposit.deductions.map((row) => <Deduction key={row.id} row={row} leaseId={lease.id} />)}
            </section>}
            <section aria-labelledby="deposit-history">
              <h3 id="deposit-history">Deposit history</h3>
              <DepositHistory entries={deposit.entries} />
            </section>
            {positive(deposit.available) && positive(deposit.reserved) && <p className="dwella-callout is-info">
              <strong>Return the undisputed {formatMoney(deposit.available)} now.</strong> The refund stays owed until you record it with a payment reference. The reserved {formatMoney(deposit.reserved)} stays held until it is resolved.
            </p>}
          </div>}
    </DrawerBody>
    {deposit && <DrawerFooter className="dwella-drawer-footer dwella-deposit-footer">
      {!ended && positive(deposit.outstanding) && <>
        <Button onClick={() => setAction("opening")}>Already held</Button>
        <Button onClick={() => setAction("request")}>Request {formatMoney(deposit.outstanding)}</Button>
      </>}
      {positive(deposit.available) && <Button onClick={() => setAction("deductions")}>Propose deduction</Button>}
      {positive(deposit.available) && <Button appearance="primary" onClick={() => setAction("refunds")}>Record refund · {formatMoney(deposit.available)}</Button>}
    </DrawerFooter>}
  </OverlayDrawer>;
}
