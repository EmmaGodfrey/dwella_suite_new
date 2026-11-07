import React, { useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  Button, DrawerBody, DrawerFooter, DrawerHeader, DrawerHeaderTitle, Field, Input, OverlayDrawer, Select,
} from "@fluentui/react-components";
import { Add24Regular, Dismiss12Regular, Dismiss20Regular } from "@fluentui/react-icons";
import { toast } from "react-toastify";

import { useCancelProof, useResendProof, useSubmitProof } from "../../Services/payments";
import { usePortalInvoices } from "../../Services/portal";
import { invoicePeriodLabel } from "../../shared/billing";
import { StatusBadge } from "../../shared/components";
import { FormDrawer, useRestoreFocus } from "../../shared/components/FormFlow";
import { formatDate, formatMoney } from "../../shared/format";
import { useFormErrors } from "../../shared/useFormErrors";
import { ProofFiles, proofBadgeColor } from "../Billing/PaymentProofs";
import "../Billing/billing.scss";
import "../Billing/deposits.scss";

const today = () => new Date().toLocaleDateString("en-CA");
const METHODS = [
  ["mobile_money", "Mobile money"], ["bank_transfer", "Bank transfer"], ["cash", "Cash"], ["cheque", "Cheque"],
];
const MAX_FILES = 3;
const MAX_BYTES = 8 * 1024 * 1024;
const FILE_TYPES = "image/jpeg,image/png,image/webp,application/pdf";
const FIELD_NAMES = ["invoice", "amount", "method", "paid_on", "reference", "files", "status"];

// A new report needs a file for bank and mobile money, as on WhatsApp.
function evidenceProblem({ method, reference, files, existing }) {
  if (files.length > MAX_FILES) return `Attach up to ${MAX_FILES} files.`;
  if (files.some((file) => file.size > MAX_BYTES)) return "Each file must be 8 MB or smaller.";
  if (existing || files.length || method === "cash") return "";
  if (method === "cheque") return reference.trim() ? "" : "Attach a photo of the cheque or enter its number.";
  return "Attach a screenshot or receipt.";
}

/** Reports a direct payment, or corrects one the landlord asked about. */
export function ProofFormDrawer({ invoice, proof, onClose, onSent }) {
  const unpaid = usePortalInvoices({ page_size: 50, unpaid: "true" }, { enabled: !proof });
  const choices = unpaid.data?.results || [];
  const [selected, setSelected] = useState(invoice);
  const [changing, setChanging] = useState(false);
  const [form, setForm] = useState(proof
    ? { amount: proof.amount, method: proof.method, paid_on: proof.paid_on, reference: proof.reference }
    : { amount: invoice.balance, method: "", paid_on: today(), reference: "" });
  const [files, setFiles] = useState([]);
  const [message, setMessage] = useState("");
  const picker = useRef(null);
  const submit = useSubmitProof();
  const resend = useResendProof();
  const mutation = proof ? resend : submit;
  const { errors, validate, clearError, fieldProps, showServerErrors } = useFormErrors();
  const balance = proof ? proof.invoice.balance : selected.balance;
  const existing = proof ? proof.files.length : 0;

  const change = (name, value) => {
    setForm((current) => ({ ...current, [name]: value }));
    clearError(name);
    if (name === "method" || name === "reference") clearError("files");
    setMessage("");
  };
  const pickInvoice = (id) => {
    const next = choices.find((row) => row.id === id);
    if (!next) return;
    setSelected(next);
    setForm((current) => ({ ...current, amount: next.balance }));
    setChanging(false);
    clearError("amount");
  };

  const send = async (event) => {
    event.preventDefault();
    if (mutation.isPending) return;
    if (!validate({
      amount: () => {
        if (!(Number(form.amount) > 0)) return "Enter an amount more than zero.";
        return Number(form.amount) > Number(balance) ? `Only ${formatMoney(balance)} is owed.` : "";
      },
      method: () => (form.method ? "" : "Choose how you paid."),
      paid_on: () => (form.paid_on && form.paid_on <= today() ? "" : "Choose a date that is not in the future."),
      files: () => evidenceProblem({ ...form, files, existing }),
    }, event.currentTarget)) return;
    try {
      const saved = await mutation.mutateAsync(proof
        ? { id: proof.id, ...form, files }
        : { invoice: selected.id, ...form, files });
      toast.success(proof ? "Corrected details sent to your landlord." : "Sent to your landlord.");
      onSent?.(saved);
      onClose();
    } catch (error) {
      if (!showServerErrors(error.data, FIELD_NAMES)) setMessage(error.message || "Could not send this. Try again.");
      else if (error.data?.invoice || error.data?.status) setMessage(error.data.invoice?.[0] || error.data.status?.[0]);
    }
  };

  return (
    <FormDrawer
      title={proof ? "Send corrected details" : "I've already paid"}
      description={proof ? "Change what was wrong, then send it back." : "Tell your landlord about a payment you made directly."}
      onClose={onClose}
      onSubmit={send}
      busy={mutation.isPending}
      errors={errors}
      submitLabel={proof ? "Send corrected details" : "Send to landlord"}
      pendingLabel="Sending…"
    >
      <div className="dwella-proof">
        {message ? <p role="alert" className="dwella-alert danger">{message}</p> : null}
        {proof ? (
          <p className="dwella-proof-invoice"><span><strong>{proof.invoice.reference}</strong><small>{formatMoney(balance)} owed</small></span></p>
        ) : changing ? (
          <Field label="Which invoice did you pay?">
            <Select value={selected.id} onChange={(_, data) => pickInvoice(data.value)}>
              {choices.map((row) => (
                <option key={row.id} value={row.id}>{row.reference} · {invoicePeriodLabel(row)} · {formatMoney(row.balance)}</option>
              ))}
            </Select>
          </Field>
        ) : (
          <div className="dwella-proof-invoice">
            <span><strong>{selected.reference} · {invoicePeriodLabel(selected)}</strong><small>{formatMoney(balance)} owed</small></span>
            {choices.length > 1 ? <Button size="small" appearance="subtle" onClick={() => setChanging(true)}>Change</Button> : null}
          </div>
        )}
        <Field label="Amount paid (ZMW)" required {...fieldProps("amount")}>
          <Input inputMode="decimal" value={form.amount} onChange={(_, data) => change("amount", data.value)} />
        </Field>
        <Field label="How you paid" required {...fieldProps("method")}>
          <Select value={form.method} onChange={(_, data) => change("method", data.value)}>
            <option value="">Choose</option>
            {METHODS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </Select>
        </Field>
        <Field label="Date paid" required {...fieldProps("paid_on")}>
          <Input type="date" max={today()} value={form.paid_on} onChange={(_, data) => change("paid_on", data.value)} />
        </Field>
        <Field label="Transaction ID" {...fieldProps("reference")}>
          <Input maxLength={80} value={form.reference} onChange={(_, data) => change("reference", data.value)} />
        </Field>
        <Field
          label={proof ? "Add a screenshot or receipt" : "Screenshot or receipt"}
          required={!proof && form.method !== "cash"}
          hint={proof ? "Files you already sent stay with this report." : "Up to 3 photos or PDFs. Needed for bank and mobile money; optional for cash."}
          {...fieldProps("files")}
        >
          <div className="dwella-deposit-attach">
            {files.length ? (
              <ul className="dwella-deposit-evidence" aria-label="Files to send">
                {files.map((file, index) => (
                  <li key={`${file.name}-${index}`}>
                    <Button size="small" icon={<Dismiss12Regular />} iconPosition="after" aria-label={`Remove ${file.name}`}
                      onClick={() => setFiles((current) => current.filter((_, position) => position !== index))}>{file.name}</Button>
                  </li>
                ))}
              </ul>
            ) : null}
            {files.length < MAX_FILES ? (
              <Button className="dwella-proof-add" icon={<Add24Regular />} aria-label={files.length ? "Add another file" : "Add a file"} onClick={() => picker.current?.click()} />
            ) : null}
            <input ref={picker} type="file" multiple hidden accept={FILE_TYPES}
              onChange={(event) => {
                // Copied first: clearing the input empties its live file list.
                const picked = [...event.target.files];
                setFiles((current) => [...current, ...picked]);
                clearError("files");
                event.target.value = "";
              }} />
          </div>
        </Field>
        <div className="dwella-soft-note">
          <span>Your balance changes once your landlord confirms the money arrived. You will get a receipt then.</span>
        </div>
      </div>
    </FormDrawer>
  );
}

/** What the tenant sent and where it stands; answers a question from here. */
export function ProofStatusDrawer({ proof, onClose }) {
  useRestoreFocus();
  const [correcting, setCorrecting] = useState(false);
  const [confirmCancel, setConfirmCancel] = useState(false);
  const cancel = useCancelProof();
  if (correcting) return <ProofFormDrawer proof={proof} onClose={onClose} />;
  const asked = proof.status === "needs_information";
  const stop = () => cancel.mutate(proof.id, {
    onSuccess: () => { toast.success("Report cancelled."); onClose(); },
    onError: (error) => toast.error(error.data?.status?.[0] || error.message || "Could not cancel this report."),
  });
  return (
    <OverlayDrawer open position="end" size="medium" className="dwella-drawer" onOpenChange={(_, data) => !data.open && !cancel.isPending && onClose()}>
      <DrawerHeader>
        <DrawerHeaderTitle action={<Button appearance="subtle" icon={<Dismiss20Regular />} aria-label="Close" onClick={onClose} />}>
          Payment report {proof.number}
        </DrawerHeaderTitle>
        <p className="dwella-drawer-note">{proof.invoice.reference} · {invoicePeriodLabel({ ...proof.invoice, period_start: proof.invoice.period })}</p>
      </DrawerHeader>
      <DrawerBody>
        <div className="dwella-proof">
          <div><StatusBadge color={proofBadgeColor[proof.status]}>{proof.status_label}</StatusBadge></div>
          {asked ? (
            <div className="dwella-soft-note is-warning"><strong>Your landlord asks</strong><span>{proof.review_note}</span></div>
          ) : null}
          {proof.status === "rejected" ? (
            <div className="dwella-soft-note is-warning"><strong>Your landlord says this was not received</strong><span>{proof.review_note}</span></div>
          ) : null}
          {proof.receipt ? (
            <p className="dwella-muted-copy">Confirmed. Your receipt is <Link to={`/billing/receipts/${proof.receipt.id}`}>{proof.receipt.number}</Link>.</p>
          ) : null}
          <section>
            <h3>What you sent</h3>
            <dl className="dwella-detail-list">
              <div><dt>Amount</dt><dd>{formatMoney(proof.amount)}</dd></div>
              <div><dt>How you paid</dt><dd>{proof.method_label}</dd></div>
              <div><dt>Date paid</dt><dd>{formatDate(proof.paid_on)}</dd></div>
              <div><dt>Transaction ID</dt><dd>{proof.reference || "None given"}</dd></div>
            </dl>
          </section>
          <section>
            <h3>Files</h3>
            <ProofFiles scope="portal" files={proof.files} />
          </section>
          {asked ? (
            <div className="dwella-soft-note">
              <span>Nothing has changed on your balance. Send the corrected details and your landlord reviews them again.</span>
            </div>
          ) : null}
        </div>
      </DrawerBody>
      <DrawerFooter className="dwella-drawer-footer dwella-proof-footer">
        {confirmCancel ? (
          <>
            <span className="dwella-muted-copy">Cancel this report?</span>
            <Button disabled={cancel.isPending} onClick={() => setConfirmCancel(false)}>Keep it</Button>
            <Button appearance="primary" disabled={cancel.isPending} onClick={stop}>{cancel.isPending ? "Cancelling…" : "Cancel report"}</Button>
          </>
        ) : (
          <>
            {proof.can_cancel ? <Button appearance="subtle" onClick={() => setConfirmCancel(true)}>Cancel this report</Button> : null}
            {proof.can_resend ? <Button appearance="primary" onClick={() => setCorrecting(true)}>Send corrected details</Button> : <Button onClick={onClose}>Close</Button>}
          </>
        )}
      </DrawerFooter>
    </OverlayDrawer>
  );
}
