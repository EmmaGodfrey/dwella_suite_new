import React, { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Button, Field, Input, Spinner } from "@fluentui/react-components";
import { CheckmarkCircle24Regular, Info24Regular } from "@fluentui/react-icons";
import { useRequestPaymentCheck, useStartRentCheckout, useTenantCollections, useTenantPaymentOptions, refreshPaymentRecords } from "../../Services/payments";
import { openLencoCheckout } from "../../Services/lencoCheckout.mjs";
import { formatMoney } from "../../shared/format";
import { paymentFeedback } from "../../shared/paymentFeedback.mjs";
import "../Billing/payments.scss";

export default function RentCheckout({ invoice }) {
  const options = useTenantPaymentOptions();
  const history = useTenantCollections(invoice.id);
  const start = useStartRentCheckout();
  const check = useRequestPaymentCheck();
  const [amount, setAmount] = useState(invoice.balance);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [stage, setStage] = useState("idle");
  const [returnedKind, setReturnedKind] = useState(null);
  const [delayed, setDelayed] = useState(false);
  const [activeCollectionId, setActiveCollectionId] = useState(null);
  const key = useRef(crypto.randomUUID());
  const lifetime = useRef(null);
  const confirmed = useRef(null);
  const rows = history.data?.results || [];
  const latest = activeCollectionId ? rows.find((row) => row.id === activeCollectionId) : rows[0];
  const checkId = activeCollectionId || latest?.id;
  const pending = latest?.status === "pending";
  const review = latest?.status === "review";
  const canPay = Number(invoice.balance) > 0 && invoice.status !== "void";
  const feedback = paymentFeedback({ stage, collection: latest, delayed, returnedKind });
  const waiting = feedback?.kind === "waiting";
  const confirmingCompletedCheckout = waiting && ["success", "pending"].includes(returnedKind);

  useEffect(() => {
    setDelayed(false);
    if (!waiting) return;
    const timer = setTimeout(() => setDelayed(true), 20_000);
    return () => clearTimeout(timer);
  }, [waiting, latest?.id]);

  useEffect(() => {
    const controller = new AbortController();
    lifetime.current = controller;
    return () => controller.abort();
  }, []);
  useEffect(() => { setAmount(invoice.balance); key.current = crypto.randomUUID(); }, [invoice.balance]);
  useEffect(() => { if (pending) setAmount(latest.amount); }, [pending, latest?.amount]);
  useEffect(() => {
    if (latest?.status === "successful" && latest.payment_id && confirmed.current !== latest.id) {
      confirmed.current = latest.id;
      setBusy(false);
      setStage("idle");
      refreshPaymentRecords();
    }
  }, [latest?.id, latest?.status, latest?.payment_id]);

  async function pay(event) {
    event.preventDefault();
    if (busy || start.isPending) return;
    if (!/^\d+(\.\d{1,2})?$/.test(amount) || Number(amount) <= 0 || Number(amount) > Number(invoice.balance)) {
      setError("Enter an amount above zero, up to your outstanding balance, with at most two decimal places.");
      return;
    }
    setBusy(true); setError(""); setStage("opening"); setReturnedKind(null);
    try {
      const result = await start.mutateAsync({ invoiceId: invoice.id, amount: Number(amount).toFixed(2), idempotencyKey: key.current });
      if (!lifetime.current?.signal.aborted) setActiveCollectionId(result.collection.id);
      if (!result.checkout) { setBusy(false); setStage("idle"); refreshPaymentRecords(); return; }
      await openLencoCheckout(result.checkout, (event) => {
        // Do not inspect any provider callback payload: verify our own record.
        if (!lifetime.current?.signal.aborted) {
          // Paint the waiting state immediately; never wait on the status request.
          setReturnedKind(event);
          setStage("checking");
          setBusy(false);
          check.mutate(result.collection.id);
        }
      }, lifetime.current?.signal);
      if (!lifetime.current?.signal.aborted) setStage((current) => current === "opening" ? "provider" : current);
    } catch (failure) {
      if (failure.name !== "AbortError" && !lifetime.current?.signal.aborted) setError(failure.message || "Could not open payment. Try again.");
      if (!lifetime.current?.signal.aborted) { setBusy(false); setStage("error"); }
    }
  }

  return (
    <section aria-label="Pay this invoice" className="dwella-online-checkout">
      <h3>Pay online</h3>
      {feedback && <div className="dwella-payment-feedback" data-kind={feedback.kind} role="status" aria-live="polite" aria-atomic="true">
        {feedback.working ? <Spinner size="small" aria-hidden="true" /> : feedback.kind === "confirmed" ? <CheckmarkCircle24Regular aria-hidden="true" /> : <Info24Regular aria-hidden="true" />}
        <div><strong>{feedback.title}</strong><p>{feedback.message}</p>
          {feedback.kind === "confirmed" && <Button as={Link} to={`/billing/receipts/${latest.payment_id}`} size="small">View receipt {latest.receipt_number}</Button>}
          {waiting && <Button size="small" disabled={check.isPending || !checkId} onClick={() => check.mutate(checkId)}>
            {check.isPending ? "Checking…" : "Check status"}
          </Button>}
          {check.isError && waiting && <p>We couldn’t request a fresh check. Automatic confirmation is still running; you can try checking again.</p>}
        </div>
      </div>}
      {options.isLoading ? <p role="status">Checking payment options…</p> : null}
      {options.isError ? <p role="alert">Could not check online payment options. <Button size="small" onClick={() => options.refetch()}>Retry</Button></p> : null}
      {options.data?.enabled && canPay && !review && !confirmingCompletedCheckout ? (
        <form onSubmit={pay}>
          <Field label="Amount to pay (ZMW)" validationMessage={error || undefined} validationState={error ? "error" : "none"}>
            <Input inputMode="decimal" value={amount} disabled={busy || pending} onChange={(_, data) => { setAmount(data.value); setError(""); key.current = crypto.randomUUID(); }} />
          </Field>
          <p className="dwella-muted-copy">Up to {formatMoney(invoice.balance)}. Choose mobile money or card in Lenco and review any fees before confirming.</p>
          <Button type="submit" appearance="primary" disabled={busy || start.isPending || history.isLoading}>
            {busy ? "Complete payment in Lenco…" : pending ? "Resume payment" : "Pay with Lenco"}
          </Button>
        </form>
      ) : options.data && !options.data.enabled && canPay && !review ? <p className="dwella-muted-copy">Online payments are not available for this invoice yet. Contact your property manager for payment details.</p> : null}
      {history.isError ? <p role="alert">Could not load payment status. <Button size="small" onClick={() => history.refetch()}>Retry</Button></p> : null}
    </section>
  );
}
