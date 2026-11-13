import React, { useEffect, useRef, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { Button, Field, Input, Radio, RadioGroup, Select } from "@fluentui/react-components";
import { toast } from "react-toastify";
import { useCurrentUserQuery } from "../../Services/queries";
import {
  useCancelWithdrawal, usePayoutSummary, usePayoutTiming, usePreviewWithdrawal, useRequestWithdrawal,
  useSavePayoutTiming, useWithdrawals,
} from "../../Services/payments";
import { getUserAccess, isWorkspaceAdmin } from "../../shared/access";
import { EmptyState, StatusBadge } from "../../shared/components";
import { FormDrawer } from "../../shared/components/FormFlow";
import { formatDate, formatMoney } from "../../shared/format";
import {
  destinationLong, destinationShort, timingLabel, weekdays, withdrawalFee, withdrawalStatus,
} from "../../shared/payouts";
import { ReceivingDrawer } from "./ReceivingDetails";
import "../../shared/records.scss";
import "./payouts.scss";

const amountPattern = /^\d{1,9}(\.\d{1,2})?$/;
const time = new Intl.DateTimeFormat("en-GB", { hour: "2-digit", minute: "2-digit" });
const requestedAt = (value) => `${formatDate(value)}, ${time.format(new Date(value))}`;

function Balance({ summary }) {
  const data = summary.data;
  const stat = (label, value, note, tone) => (
    <div className="dwella-stat">
      <span>{label}</span>
      {summary.isLoading ? <span className="dwella-skeleton" style={{ height: 24, width: 110 }} /> : <strong className={tone}>{formatMoney(value)}</strong>}
      {note ? <small>{note}</small> : null}
    </div>
  );
  return (
    <div className="dwella-stat-strip">
      {stat("Available to withdraw", data?.available, "After Lenco collection fees", "is-positive")}
      {stat("Awaiting settlement", data?.awaiting_settlement, "Usually ready within 1–2 days")}
      {stat("Withdrawals processing", data?.processing, Number(data?.processing) > 0 ? "Including fees held" : null)}
      {stat("Withdrawn this month", data?.withdrawn_this_month, Number(data?.fees_this_month) > 0 ? `Plus ${formatMoney(data.fees_this_month)} transfer fees` : null)}
    </div>
  );
}

function WithdrawDrawer({ summary, onClose, onChangeAccount }) {
  const [amount, setAmount] = useState("");
  const [message, setMessage] = useState("");
  const key = useRef(crypto.randomUUID());
  const preview = usePreviewWithdrawal();
  const request = useRequestWithdrawal();
  const valid = amountPattern.test(amount) && Number(amount) > 0;
  const quote = preview.data && preview.variables === amount ? preview.data : null;

  // Ask for the fee once typing pauses; each new amount is a new request key.
  useEffect(() => {
    key.current = crypto.randomUUID();
    setMessage("");
    if (!valid) return undefined;
    const timer = setTimeout(() => preview.mutate(amount), 350);
    return () => clearTimeout(timer);
  }, [amount]); // eslint-disable-line react-hooks/exhaustive-deps

  const previewError = valid && preview.isError && preview.variables === amount
    ? preview.error.data?.amount?.[0] || preview.error.message : "";
  const submit = async (event) => {
    event.preventDefault();
    if (request.isPending) return;
    if (!quote) {
      setMessage(valid ? "Wait for the fee to load, then confirm." : "Enter the amount you want to receive.");
      return;
    }
    try {
      await request.mutateAsync({ amount: quote.amount, fee: quote.fee, idempotencyKey: key.current });
      toast.success(`Withdrawal of ${formatMoney(quote.amount)} is on its way.`);
      onClose();
    } catch (error) {
      setMessage(error.data?.fee?.[0] || error.data?.amount?.[0] || error.message || "Could not start the withdrawal.");
      if (error.data?.fee) preview.mutate(amount);
    }
  };
  const largest = summary.largest;
  return (
    <FormDrawer title="Withdraw" description={`Available to withdraw · ${formatMoney(summary.available)}`}
      onClose={onClose} onSubmit={submit} busy={request.isPending}
      submitLabel={quote ? `Withdraw ${formatMoney(quote.amount)}` : "Withdraw"} pendingLabel="Starting withdrawal…">
      <div className="dwella-withdraw">
        {message ? <p role="alert" className="dwella-alert danger">{message}</p> : null}
        <Field label="Amount you receive" required validationState={previewError ? "error" : "none"} validationMessage={previewError || undefined}>
          <Input value={amount} inputMode="decimal" contentBefore="K" autoFocus aria-invalid={Boolean(previewError)}
            onChange={(_, data) => setAmount(data.value.replace(/[^\d.]/g, ""))} placeholder="0.00" />
        </Field>
        {largest ? (
          <Button appearance="transparent" className="dwella-link-button" onClick={() => setAmount(largest)}>
            Withdraw the maximum · {formatMoney(largest)}
          </Button>
        ) : <p className="dwella-drawer-note">Your balance is below the smallest withdrawal of {formatMoney(summary.minimum)} plus its fee.</p>}
        <section className="dwella-withdraw-review" aria-live="polite" aria-busy={preview.isPending}>
          <h3>Review</h3>
          <dl>
            <div><dt>You receive</dt><dd>{quote ? formatMoney(quote.amount) : "—"}</dd></div>
            <div><dt>Most Lenco can charge</dt><dd>{quote ? formatMoney(quote.fee) : "—"}</dd></div>
            <div className="is-total"><dt>Held from your balance</dt><dd>{quote ? formatMoney(quote.total) : "—"}</dd></div>
            <div><dt>Balance after</dt><dd>{quote ? formatMoney(quote.balance_after) : "—"}</dd></div>
          </dl>
          <p className="dwella-withdraw-note">This is the highest fee for this amount. If Lenco charges less, the difference returns to your balance after delivery.</p>
        </section>
        <div className="dwella-withdraw-account">
          <strong>Sent to</strong>
          <span>{destinationLong(summary.destination)}</span>
          <Button appearance="transparent" className="dwella-link-button" onClick={onChangeAccount}>Change receiving account</Button>
        </div>
        <p className="dwella-drawer-note">
          {summary.destination?.kind === "bank-account"
            ? "Bank withdrawals can take until the next working day."
            : "Mobile-money withdrawals usually arrive within minutes."} You can follow the status in Withdrawal history.
        </p>
      </div>
    </FormDrawer>
  );
}

const timings = [
  { value: "manual", label: "Hold until I request", note: "Rent stays in your balance until you withdraw it." },
  { value: "settled", label: "As funds settle", note: "Sent soon after each payment settles. Each transfer has its own fee." },
  { value: "weekly", label: "Weekly", note: "Everything available is sent once a week." },
  { value: "monthly", label: "Monthly", note: "Everything available is sent once a month." },
];
const monthDays = Array.from({ length: 28 }, (_, index) => index + 1);
const nextRun = new Intl.DateTimeFormat("en-GB", {
  weekday: "long", day: "numeric", month: "long", hour: "2-digit", minute: "2-digit",
});

function TimingDrawer({ plan, destination, onClose }) {
  const [form, setForm] = useState({
    timing: plan?.timing || "manual", weekday: plan?.weekday ?? 0, month_day: plan?.month_day ?? 0,
  });
  const [message, setMessage] = useState("");
  const save = useSavePayoutTiming();
  const change = (key, value) => { setMessage(""); setForm((current) => ({ ...current, [key]: value })); };
  const chosen = timings.find((item) => item.value === form.timing);
  const submit = async (event) => {
    event.preventDefault();
    if (save.isPending) return;
    try {
      await save.mutateAsync(form);
      toast.success(`Payout timing saved · ${timingLabel(form)}.`);
      onClose();
    } catch (error) {
      setMessage(error.data?.timing?.[0] || error.message || "Could not save the payout timing.");
    }
  };
  return (
    <FormDrawer title="Payout timing" description="Choose when settled rent is sent to your receiving account."
      onClose={onClose} onSubmit={submit} busy={save.isPending} submitLabel="Save timing" pendingLabel="Saving…">
      <div className="dwella-withdraw">
        {message ? <p role="alert" className="dwella-alert danger">{message}</p> : null}
        <Field label="Send settled rent">
          <RadioGroup value={form.timing} onChange={(_, data) => change("timing", data.value)}>
            {timings.map((item) => <Radio key={item.value} value={item.value} label={item.label} />)}
          </RadioGroup>
        </Field>
        {form.timing === "weekly" ? (
          <Field label="Payout day">
            <Select value={String(form.weekday)} onChange={(_, data) => change("weekday", Number(data.value))}>
              {weekdays.map((day, index) => <option key={day} value={index}>{day} · 08:00</option>)}
            </Select>
          </Field>
        ) : null}
        {form.timing === "monthly" ? (
          <Field label="Payout day">
            <Select value={String(form.month_day)} onChange={(_, data) => change("month_day", Number(data.value))}>
              <option value="0">Last day of the month · 08:00</option>
              {monthDays.map((day) => <option key={day} value={day}>Day {day} · 08:00</option>)}
            </Select>
          </Field>
        ) : null}
        <p className="dwella-withdraw-note">
          {chosen?.note} {form.timing === "manual" ? "" : "Only settled rent is sent, up to the largest amount your balance covers after the Lenco fee. Payments still settling carry forward."}
        </p>
        {form.timing !== "manual" ? (
          <p className="dwella-drawer-note">
            {destination ? `Sent to ${destinationLong(destination)}.` : "Add a receiving account before choosing automatic payouts."} Times are Lusaka time.
          </p>
        ) : null}
      </div>
    </FormDrawer>
  );
}

function History({ canWithdraw }) {
  const [page, setPage] = useState(1);
  const query = useWithdrawals(page);
  const cancel = useCancelWithdrawal();
  const rows = query.data?.results || [];
  const pagination = query.data?.pagination;
  if (query.isLoading) return <p role="status">Loading withdrawals…</p>;
  if (query.isError) return <div role="alert"><p>Could not load withdrawals.</p><Button onClick={() => query.refetch()}>Retry</Button></div>;
  if (!rows.length) {
    return <p className="dwella-payouts-empty">No withdrawals yet. Settled rent stays in your balance until you withdraw it.</p>;
  }
  return (
    <>
      <div className="dwella-table-card">
        <div style={{ overflowX: "auto" }}>
          <table className="dwella-table">
            <caption className="dwella-visually-hidden">Withdrawal history</caption>
            <thead>
              <tr>
                <th scope="col">Requested</th>
                <th scope="col">Receiving account</th>
                <th scope="col" className="is-numeric">You received</th>
                <th scope="col" className="is-numeric">Fee</th>
                <th scope="col">Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => {
                const status = withdrawalStatus[row.status] || { label: row.status, color: "subtle" };
                return (
                  <tr key={row.id}>
                    <td>{requestedAt(row.created_at)}<span className="dwella-cell-note">{row.automatic ? `Automatic · ${row.reference}` : row.reference}</span></td>
                    <td>{destinationShort(row.destination)}</td>
                    <td className="is-numeric">{formatMoney(row.amount)}</td>
                    <td className="is-numeric">{withdrawalFee(row, formatMoney)}</td>
                    <td>
                      <StatusBadge color={status.color}>{status.label}</StatusBadge>
                      {row.status === "review" ? <span className="dwella-cell-note">Contact Dwella support with this reference.</span> : null}
                      {canWithdraw && row.status === "queued" ? (
                        <Button size="small" appearance="subtle" disabled={cancel.isPending}
                          onClick={() => cancel.mutate(row.id, { onError: (error) => toast.error(error.message || "Could not cancel.") })}>
                          Cancel
                        </Button>
                      ) : null}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
      {pagination && pagination.total_pages > 1 ? (
        <div className="dwella-page-toolbar" style={{ marginTop: 16 }}>
          <span>Page {page} of {pagination.total_pages}</span>
          <Button disabled={page <= 1 || query.isFetching} onClick={() => setPage(page - 1)}>Previous</Button>
          <Button disabled={!pagination.next || query.isFetching} onClick={() => setPage(page + 1)}>Next</Button>
        </div>
      ) : null}
    </>
  );
}

export default function Payouts() {
  const user = useCurrentUserQuery();
  const access = getUserAccess(user.data);
  const canWithdraw = access.persona === "landlord" && !user.data?.is_staff && !user.data?.is_superuser;
  // Pooled rent, receiving accounts and withdrawals belong to property admins.
  const allowed = isWorkspaceAdmin(user.data);
  const summary = usePayoutSummary({ enabled: allowed });
  const timing = usePayoutTiming({ enabled: allowed });
  const [drawer, setDrawer] = useState(null); // null | "withdraw" | "account" | "timing"
  const data = summary.data;
  const destination = data?.destination;
  const blocked = !data?.withdrawals_enabled
    ? "Withdrawals are not switched on yet."
    : !destination ? "Add a receiving account first." : !data.largest ? "Your balance is too low to withdraw." : "";
  if (user.data && !allowed) return <Navigate to="/billing" replace />;
  return (
    <div className="dwella-payouts-page">
      <header className="dwella-detail-header">
        <div>
          <Link to="/billing">← Invoices</Link>
          <h1>Payouts</h1>
          <p>{timing.data && timing.data.timing !== "manual"
            ? "Settled rent is sent on your payout timing, and you can still withdraw at any time."
            : "Settled rent is yours to withdraw whenever you choose."}</p>
        </div>
        {canWithdraw ? (
          <div className="dwella-payouts-actions">
            <Button onClick={() => setDrawer("account")}>{destination ? "Change account" : "Add receiving account"}</Button>
            <Button appearance="primary" disabled={Boolean(blocked) || summary.isLoading} title={blocked || undefined}
              onClick={() => setDrawer("withdraw")}>Withdraw</Button>
          </div>
        ) : null}
      </header>
      {summary.isError ? (
        <EmptyState title="Could not load your balance" description={summary.error.message} actionLabel="Try again" onAction={() => summary.refetch()} />
      ) : (
        <>
          <Balance summary={summary} />
          <section className="dwella-surface dwella-payouts-account">
            <div>
              <h2>Receiving account</h2>
              <p>{summary.isLoading ? "Loading…" : destination ? destinationLong(destination) : "No receiving account yet. Add one to withdraw your rent."}</p>
            </div>
            {canWithdraw && blocked && !summary.isLoading ? <p className="dwella-payouts-blocked" role="status">{blocked}</p> : null}
          </section>
          <section className="dwella-surface dwella-payouts-account">
            <div>
              <h2>Payout timing</h2>
              <p>
                {timing.isLoading ? "Loading…" : timing.isError ? "Could not load your payout timing." : timingLabel(timing.data)}
                {timing.data?.next_run_at && timing.data.timing !== "settled" ? ` · next ${nextRun.format(new Date(timing.data.next_run_at))}` : ""}
              </p>
            </div>
            {canWithdraw ? (
              <Button disabled={timing.isLoading || timing.isError} onClick={() => setDrawer("timing")}>Change timing</Button>
            ) : null}
          </section>
          <p className="dwella-payouts-note is-callout">
            Your balance stays in Dwella’s Lenco account until you withdraw. Each withdrawal is sent once, and the Lenco transfer fee is shown before you confirm.
          </p>
          <h2 className="dwella-payouts-heading">Withdrawal history</h2>
          <History canWithdraw={canWithdraw} />
          <p className="dwella-payouts-note">A failed withdrawal returns the amount and fee to your balance. Tenant payments and receipts are never affected.</p>
        </>
      )}
      {drawer === "withdraw" && data ? (
        <WithdrawDrawer summary={data} onClose={() => setDrawer(null)} onChangeAccount={() => setDrawer("account")} />
      ) : null}
      {drawer === "account" ? <ReceivingDrawer destination={destination} onClose={() => setDrawer(null)} /> : null}
      {drawer === "timing" ? <TimingDrawer plan={timing.data} destination={destination} onClose={() => setDrawer(null)} /> : null}
    </div>
  );
}
