import React, { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Button, Field, Input, Select, Spinner } from "@fluentui/react-components";
import { CheckmarkCircle24Regular, Info24Regular } from "@fluentui/react-icons";
import { useRequestPaymentCheck, useStartRentCheckout, useTenantCollections, useTenantPaymentOptions, refreshPaymentRecords } from "../../Services/payments";
import { openLencoCheckout } from "../../Services/lencoCheckout.mjs";
import { formatMoney } from "../../shared/format";
import { paymentFeedback } from "../../shared/paymentFeedback.mjs";
import { useFormErrors } from "../../shared/useFormErrors";
import "../Billing/payments.scss";

export default function RentCheckout({ invoice }) {
  const options = useTenantPaymentOptions();
  const history = useTenantCollections(invoice.id);
  const start = useStartRentCheckout();
  const check = useRequestPaymentCheck();
  const [amount, setAmount] = useState(invoice.balance);
  const [channel, setChannel] = useState("mobile-money");
  const [phone, setPhone] = useState("");
  const [operator, setOperator] = useState("");
  const { validate, clearError, fieldProps, showServerErrors } = useFormErrors();
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
  const feedback = paymentFeedback({ stage, collection: latest, delayed, returnedKind, channel });
  const waiting = feedback?.kind === "waiting";
  const confirmingCompletedCheckout = waiting && (["success", "pending"].includes(returnedKind) || latest?.channel === "mobile-money");

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
    if (pending) setChannel(latest.channel === "mobile-money" ? "mobile-money" : "card");
    if (["failed", "expired"].includes(latest?.status)) key.current = crypto.randomUUID();
  }, [pending, latest?.channel, latest?.status]);
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
    if (!validate({
      amount: () => !/^\d+(\.\d{1,2})?$/.test(amount) || Number(amount) <= 0 || Number(amount) > Number(invoice.balance)
        ? "Enter an amount above zero, up to your outstanding balance, with at most two decimal places." : "",
      phone: () => channel === "mobile-money" && !/^(?:0[79]\d{8}|\+?260[79]\d{8})$/.test(phone.replace(/[\s()-]/g, ""))
        ? "Enter a valid Zambian mobile-money number." : "",
      operator: () => channel === "mobile-money" && !["mtn", "airtel", "zamtel"].includes(operator)
        ? "Choose the network for this number." : "",
    }, event.currentTarget)) return;
    setBusy(true); setError(""); setStage("opening"); setReturnedKind(null);
    try {
      const result = await start.mutateAsync({ invoiceId: invoice.id, amount: Number(amount).toFixed(2), idempotencyKey: key.current,
        channel, phone, operator });
      if (!lifetime.current?.signal.aborted) setActiveCollectionId(result.collection.id);
      if (!result.checkout) { setBusy(false); setStage("idle"); return; }
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
      if (failure.name !== "AbortError" && !lifetime.current?.signal.aborted) {
        if (!showServerErrors(failure.data, ["amount", "phone", "operator", "channel"]))
          setError(failure.message || "Could not confirm the payment request. Check its status before trying again.");
      }
      if (!lifetime.current?.signal.aborted) { setBusy(false); setStage("error"); }
    }
  }

  return (
    <section aria-label="Pay this invoice" className="dwella-online-checkout">
      <h3>Pay online</h3>
      {error && <p role="alert" className="dwella-alert danger">{error}</p>}
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
        <form onSubmit={pay} noValidate>
          <Field label="Payment method" {...fieldProps("channel")}>
            <Select value={pending ? latest.channel === "mobile-money" ? "mobile-money" : "card" : channel} disabled={busy || pending}
              onChange={(_, data) => { setChannel(data.value); setError(""); key.current = crypto.randomUUID(); }}>
              <option value="mobile-money">Mobile money</option><option value="card">Card</option>
            </Select>
          </Field>
          <Field label="Amount to pay (ZMW)" required {...fieldProps("amount")}>
            <Input name="amount" inputMode="decimal" value={amount} disabled={busy || pending} onChange={(_, data) => { setAmount(data.value); clearError("amount"); setError(""); key.current = crypto.randomUUID(); }} />
          </Field>
          {channel === "mobile-money" && !pending && <>
            <Field label="Your mobile-money number" required {...fieldProps("phone")}>
              <Input name="phone" type="tel" autoComplete="tel" inputMode="tel" maxLength={24} value={phone} disabled={busy}
                placeholder="e.g. 0971234567" onChange={(_, data) => { setPhone(data.value); clearError("phone"); key.current = crypto.randomUUID(); }} />
            </Field>
            <Field label="Mobile network" required {...fieldProps("operator")}>
              <Select name="operator" value={operator} disabled={busy} onChange={(_, data) => { setOperator(data.value); clearError("operator"); key.current = crypto.randomUUID(); }}>
                <option value="">Choose your network</option><option value="mtn">MTN Mobile Money</option>
                <option value="airtel">Airtel Money</option><option value="zamtel">Zamtel Money</option>
              </Select>
            </Field>
          </>}
          <p className="dwella-muted-copy">Up to {formatMoney(invoice.balance)}. {channel === "mobile-money" && !pending
            ? "Use your paying wallet’s number and network. You’ll authorize the payment on your phone."
            : "Enter your card details securely in Lenco checkout."}</p>
          <Button type="submit" appearance="primary" disabled={busy || start.isPending || history.isLoading}>
            {busy ? channel === "mobile-money" ? "Requesting payment…" : "Complete payment in Lenco…"
              : pending ? "Resume checkout" : channel === "mobile-money" ? "Request mobile-money payment" : "Pay by card"}
          </Button>
        </form>
      ) : options.data && !options.data.enabled && canPay && !review ? <p className="dwella-muted-copy">Online payments are not available for this invoice yet. Contact your property manager for payment details.</p> : null}
      {history.isError ? <p role="alert">Could not load payment status. <Button size="small" onClick={() => history.refetch()}>Retry</Button></p> : null}
    </section>
  );
}
