import React, { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Button, Field, Input } from "@fluentui/react-components";
import { useRequestPaymentCheck, useStartRentCheckout, useTenantCollections, useTenantPaymentOptions, refreshPaymentRecords } from "../../Services/payments";
import { openLencoCheckout } from "../../Services/lencoCheckout.mjs";
import { formatMoney } from "../../shared/format";
import "../Billing/payments.scss";

export default function RentCheckout({ invoice }) {
  const options = useTenantPaymentOptions();
  const history = useTenantCollections(invoice.id);
  const start = useStartRentCheckout();
  const check = useRequestPaymentCheck();
  const [amount, setAmount] = useState(invoice.balance);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const key = useRef(crypto.randomUUID());
  const lifetime = useRef(null);
  const confirmed = useRef(null);
  const latest = history.data?.results?.[0];
  const pending = latest?.status === "pending";
  const review = latest?.status === "review";
  const canPay = Number(invoice.balance) > 0 && invoice.status !== "void";

  useEffect(() => {
    const controller = new AbortController();
    lifetime.current = controller;
    return () => controller.abort();
  }, []);
  useEffect(() => { setAmount(invoice.balance); key.current = crypto.randomUUID(); }, [invoice.balance]);
  useEffect(() => { if (pending) setAmount(latest.amount); }, [pending, latest?.amount]);
  useEffect(() => {
    if (latest?.status === "successful" && confirmed.current !== latest.id) {
      confirmed.current = latest.id;
      setNotice("Payment verified. Your invoice and receipt have been updated.");
      refreshPaymentRecords();
    }
    if (["failed", "review"].includes(latest?.status)) setNotice("");
  }, [latest?.id, latest?.status]);

  async function pay(event) {
    event.preventDefault();
    if (busy || start.isPending) return;
    if (!/^\d+(\.\d{1,2})?$/.test(amount) || Number(amount) <= 0 || Number(amount) > Number(invoice.balance)) {
      setError("Enter an amount above zero, up to your outstanding balance, with at most two decimal places.");
      return;
    }
    setBusy(true); setError(""); setNotice("");
    try {
      const result = await start.mutateAsync({ invoiceId: invoice.id, amount: Number(amount).toFixed(2), idempotencyKey: key.current });
      if (!result.checkout) { setBusy(false); refreshPaymentRecords(); return; }
      await openLencoCheckout(result.checkout, () => {
        // Do not inspect any provider callback payload: verify our own record.
        check.mutate(result.collection.id);
        if (!lifetime.current?.signal.aborted) {
          setBusy(false);
          setNotice("Checking your payment. You can close this drawer; confirmation will update here.");
        }
      }, lifetime.current?.signal);
    } catch (failure) {
      if (failure.name !== "AbortError" && !lifetime.current?.signal.aborted) setError(failure.message || "Could not open payment. Try again.");
      if (!lifetime.current?.signal.aborted) setBusy(false);
    }
  }

  return (
    <section aria-label="Pay this invoice" className="dwella-online-checkout">
      <h3>Pay online</h3>
      {notice ? <p role="status">{notice}</p> : null}
      {latest?.status === "failed" ? <p role="status">Your last payment failed. You can try again.</p> : null}
      {review ? <p role="status">This payment needs review. Contact your property manager before paying again.</p> : null}
      {latest?.payment_id ? <p><Link to={`/billing/receipts/${latest.payment_id}`}>View {latest.receipt_number}</Link></p> : null}
      {options.isLoading ? <p role="status">Checking payment options…</p> : null}
      {options.isError ? <p role="alert">Could not check online payment options. <Button size="small" onClick={() => options.refetch()}>Retry</Button></p> : null}
      {options.data?.enabled && canPay && !review ? (
        <form onSubmit={pay}>
          <Field label="Amount to pay (ZMW)" validationMessage={error || undefined} validationState={error ? "error" : "none"}>
            <Input inputMode="decimal" value={amount} disabled={busy || pending} onChange={(_, data) => { setAmount(data.value); setError(""); key.current = crypto.randomUUID(); }} />
          </Field>
          <p className="dwella-muted-copy">Up to {formatMoney(invoice.balance)}. Choose mobile money or card in Lenco and review any fees before confirming.</p>
          <Button type="submit" appearance="primary" disabled={busy || start.isPending || history.isLoading}>
            {busy ? "Complete payment in Lenco…" : pending ? "Resume payment" : "Pay with Lenco"}
          </Button>
        </form>
      ) : options.data && canPay && !review ? <p className="dwella-muted-copy">Online payments are not available for this invoice yet. Contact your property manager for payment details.</p> : null}
      {pending ? <p role="status">Awaiting payment confirmation. <Button size="small" disabled={check.isPending} onClick={() => check.mutate(latest.id)}>Check status</Button></p> : null}
      {history.isError ? <p role="alert">Could not load payment status. <Button size="small" onClick={() => history.refetch()}>Retry</Button></p> : null}
      {check.isError ? <p role="alert">Could not request a payment check. Confirmation will also be checked automatically.</p> : null}
    </section>
  );
}
