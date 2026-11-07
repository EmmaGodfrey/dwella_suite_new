import React, { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  Button, DrawerBody, DrawerFooter, DrawerHeader, DrawerHeaderTitle, Field, OverlayDrawer, Textarea,
} from "@fluentui/react-components";
import { Camera24Regular, Dismiss20Regular, DocumentPdf24Regular, ReceiptMoney24Regular } from "@fluentui/react-icons";
import { toast } from "react-toastify";

import { useCurrentUserQuery } from "../../Services/queries";
import { openProofFile, useManagerProof, useManagerProofs, useProofDecision } from "../../Services/payments";
import { getUserAccess } from "../../shared/access";
import { EmptyState, SegmentedFilter, StatusBadge } from "../../shared/components";
import { useRestoreFocus } from "../../shared/components/FormFlow";
import { formatDate, formatMoney } from "../../shared/format";
import { useFormErrors } from "../../shared/useFormErrors";
import "../../shared/records.scss";
import "./billing.scss";

export const proofBadgeColor = {
  submitted: "warning",
  needs_information: "informative",
  confirmed: "success",
  rejected: "danger",
  cancelled: "subtle",
};

const emptyCopy = {
  open: "No payments are waiting for you. Tenants report direct payments here.",
  needs_information: "No tenant is answering a question right now.",
  confirmed: "Payments you confirm will appear here.",
  rejected: "Payments you mark as not received will appear here.",
  cancelled: "Reports a tenant cancels will appear here.",
};

const evidenceLabel = (proof) => {
  if (!proof.files.length) return "No file";
  return `${proof.files.length} ${proof.files.length === 1 ? "file" : "files"}`;
};

const dateTime = (value) => new Date(value).toLocaleString("en-GB", {
  day: "numeric", month: "short", hour: "2-digit", minute: "2-digit",
});
const sizeLabel = (bytes) => (bytes < 1024 * 1024
  ? `${Math.max(1, Math.round(bytes / 1024))} KB`
  : `${(bytes / (1024 * 1024)).toFixed(1)} MB`);

export function ProofFiles({ scope, files }) {
  if (!files.length) return <p className="dwella-muted-copy">No file was attached.</p>;
  const open = async (item) => {
    try {
      await openProofFile(scope, item);
    } catch (error) {
      toast.error(error.message || "Could not open this file.");
    }
  };
  return (
    <ul className="dwella-proof-files">
      {files.map((item) => (
        <li key={item.id}>
          <span className="dwella-proof-file-thumb" aria-hidden="true">
            {item.content_type === "application/pdf" ? <DocumentPdf24Regular /> : <Camera24Regular />}
          </span>
          <strong>{item.name}</strong>
          <small>{item.content_type === "application/pdf" ? "PDF" : "Screenshot"} · {sizeLabel(item.size)}</small>
          <Button size="small" appearance="transparent" onClick={() => open(item)} aria-label={`Open ${item.name}`}>Open</Button>
        </li>
      ))}
    </ul>
  );
}

function ProofHistory({ proof }) {
  return (
    <ul className="dwella-proof-history">
      {[...proof.history].reverse().map((entry) => (
        <li key={entry.revision}>
          <strong>{dateTime(entry.submitted_at)} · Sent {formatMoney(entry.amount)}</strong>
          {entry.question ? <span>You asked: {entry.question}</span> : null}
        </li>
      ))}
      <li>
        <strong>{dateTime(proof.submitted_at)} · {proof.history.length ? "Sent again" : "Sent"}{proof.channel === "whatsapp" ? " on WhatsApp" : ""}</strong>
      </li>
      {proof.reviewed_at && proof.status !== "submitted" ? (
        <li>
          <strong>{dateTime(proof.reviewed_at)} · {proof.status_label}</strong>
          {proof.review_note ? <span>{proof.review_note}</span> : null}
        </li>
      ) : null}
    </ul>
  );
}

const decisions = {
  ask: {
    label: "What do you need from the tenant?",
    submit: "Send question",
    required: "Say what you need from the tenant.",
    done: "Question sent to the tenant.",
  },
  reject: {
    label: "Why was it not received?",
    submit: "Mark not received",
    required: "Say why it was not received.",
    done: "Marked as not received. The tenant has been told.",
  },
};

function ReviewDrawer({ id, canManage, onClose }) {
  useRestoreFocus();
  const query = useManagerProof(id);
  const proof = query.data;
  const [decision, setDecision] = useState(null); // null | "ask" | "reject"
  const [note, setNote] = useState("");
  const mutation = useProofDecision();
  const { validate, clearError, fieldProps } = useFormErrors();
  const busy = mutation.isPending;
  const canReview = canManage && proof?.can_review;

  const decide = (name, text = "") => mutation.mutate({ id, decision: name, note: text }, {
    onSuccess: (data) => {
      toast.success(name === "confirm" ? `Payment confirmed. Receipt ${data.receipt?.number || ""} sent.` : decisions[name].done);
      onClose();
    },
    // Someone else may have decided it first; show what it is now.
    onError: (error) => {
      toast.error(error.data?.status?.[0] || error.data?.amount?.[0] || error.data?.note?.[0] || error.message || "Could not save this decision.");
      query.refetch();
    },
  });

  const send = () => {
    if (validate({ note: () => (note.trim() ? "" : decisions[decision].required) })) decide(decision, note.trim());
  };

  return (
    <OverlayDrawer open position="end" size="medium" className="dwella-drawer" onOpenChange={(_, data) => !data.open && !busy && onClose()}>
      <DrawerHeader>
        <DrawerHeaderTitle action={<Button appearance="subtle" icon={<Dismiss20Regular />} aria-label="Close" disabled={busy} onClick={onClose} />}>
          {proof ? `Payment proof ${proof.number}` : "Payment proof"}
        </DrawerHeaderTitle>
        {proof ? (
          <p className="dwella-drawer-note">
            {proof.tenant.name}{proof.premises ? ` · ${proof.premises}` : ""} · <Link to={`/billing/invoices/${proof.invoice.id}`}>{proof.invoice.reference}</Link>
          </p>
        ) : null}
      </DrawerHeader>
      <DrawerBody>
        {query.isLoading ? <span className="dwella-skeleton" style={{ height: 240, width: "100%" }} /> : null}
        {query.isError ? (
          <p role="alert" className="dwella-alert danger">
            Could not load this payment. <Button size="small" onClick={() => query.refetch()}>Retry</Button>
          </p>
        ) : null}
        {proof ? (
          <div className="dwella-proof">
            <section className="dwella-proof-summary">
              <div className="dwella-proof-amount">
                <div><span>Tenant says they paid</span><strong>{formatMoney(proof.amount)}</strong></div>
                <StatusBadge color={proofBadgeColor[proof.status]}>{proof.status_label}</StatusBadge>
              </div>
              <dl className="dwella-proof-facts">
                <div><dt>Method</dt><dd>{proof.method_label}</dd></div>
                <div><dt>Paid on</dt><dd>{formatDate(proof.paid_on)}</dd></div>
                <div><dt>Reference</dt><dd>{proof.reference || "None given"}</dd></div>
                <div><dt>Invoice balance</dt><dd>{formatMoney(proof.invoice.balance)}</dd></div>
              </dl>
            </section>
            {proof.possible_duplicates.length ? (
              <div className="dwella-soft-note is-warning">
                <strong>This file is also on {proof.possible_duplicates.join(", ")}</strong>
                <span>It may be a resend or a reused screenshot. Check your statement before confirming.</span>
              </div>
            ) : null}
            <section>
              <h3>Evidence</h3>
              <ProofFiles scope="billing" files={proof.files} />
            </section>
            {proof.note ? (
              <section>
                <h3>Note from the tenant</h3>
                <p className="dwella-muted-copy">{proof.note}</p>
              </section>
            ) : null}
            <section>
              <h3>History</h3>
              <ProofHistory proof={proof} />
            </section>
            {proof.receipt ? (
              <p className="dwella-muted-copy">Receipt <Link to={`/billing/receipts/${proof.receipt.id}`}>{proof.receipt.number}</Link> was issued for this payment.</p>
            ) : null}
            {canReview && !decision ? (
              <div className="dwella-soft-note">
                <strong>Confirm only once the money is in your account</strong>
                <span>Confirming records one payment and sends the receipt. Until then the balance stays the same.</span>
              </div>
            ) : null}
            {canReview && decision ? (
              <Field label={decisions[decision].label} required {...fieldProps("note")}>
                <Textarea autoFocus rows={3} maxLength={1000} value={note} disabled={busy}
                  onChange={(_, data) => { setNote(data.value); clearError("note"); }} />
              </Field>
            ) : null}
          </div>
        ) : null}
      </DrawerBody>
      <DrawerFooter className="dwella-drawer-footer dwella-proof-footer">
        {!canReview ? <Button onClick={onClose}>Close</Button> : decision ? (
          <>
            <Button disabled={busy} onClick={() => { setDecision(null); setNote(""); clearError("note"); }}>Back</Button>
            <Button appearance="primary" disabled={busy} onClick={send}>{busy ? "Saving…" : decisions[decision].submit}</Button>
          </>
        ) : (
          <>
            <Button appearance="subtle" disabled={busy} onClick={() => setDecision("ask")}>Ask for details</Button>
            <Button disabled={busy} onClick={() => setDecision("reject")}>Not received</Button>
            <Button appearance="primary" disabled={busy} onClick={() => decide("confirm")}>{busy ? "Confirming…" : "Confirm received"}</Button>
          </>
        )}
      </DrawerFooter>
    </OverlayDrawer>
  );
}

function TableSkeleton() {
  return [0, 1, 2].map((row) => (
    <tr key={row} className="is-loading" aria-hidden="true">
      {[150, 70, 80, 90, 80, 70, 110].map((width, index) => (
        <td key={index}><span className="dwella-skeleton" style={{ height: 12, width }} /></td>
      ))}
    </tr>
  ));
}

export default function PaymentProofs() {
  const [params, setParams] = useSearchParams();
  const { data: user } = useCurrentUserQuery({ staleTime: 60_000 });
  const canManage = getUserAccess(user).can_manage_properties;
  const [view, setView] = useState("open");
  const query = useManagerProofs(view, { placeholderData: (previous) => previous, staleTime: 15_000 });
  const proofs = query.data?.results || [];
  const openId = params.get("proof");
  const count = (value) => (value ? ` · ${value}` : "");
  const views = [
    { value: "open", label: `Waiting for you${count(query.data?.waiting)}` },
    { value: "needs_information", label: `Asked for details${count(query.data?.asked)}` },
    { value: "confirmed", label: "Confirmed" },
    { value: "rejected", label: "Not received" },
    { value: "cancelled", label: "Cancelled" },
  ];
  const setOpen = (id) => {
    const next = new URLSearchParams(params);
    if (id) next.set("proof", id);
    else next.delete("proof");
    setParams(next, { replace: true });
  };

  return (
    <div className="dwella-billing-page">
      <header className="dwella-page-header">
        <div className="dwella-page-header-copy">
          <h1>Payment proofs</h1>
          <p>Tenants report direct payments here. A balance only changes when you confirm the money arrived.</p>
        </div>
      </header>
      <div className="dwella-page-toolbar">
        <SegmentedFilter label="Filter payment proofs" options={views} value={view} onChange={setView} />
      </div>

      {query.isError ? (
        <div className="dwella-alert danger">
          Unable to load payment proofs. <Button size="small" onClick={() => query.refetch()}>Retry</Button>
        </div>
      ) : null}

      {query.isError && !proofs.length ? null : !query.isLoading && !proofs.length ? (
        <EmptyState icon={<ReceiptMoney24Regular />} title="Nothing here" description={emptyCopy[view]} />
      ) : (
        <div className="dwella-table-card" aria-busy={query.isFetching}>
          <table className="dwella-table dwella-proof-table">
            <thead>
              <tr>
                <th scope="col">Tenant</th>
                <th scope="col">Invoice</th>
                <th scope="col" className="is-numeric">Amount</th>
                <th scope="col">Method</th>
                <th scope="col">Paid on</th>
                <th scope="col">Evidence</th>
                <th scope="col">Status</th>
              </tr>
            </thead>
            <tbody>
              {query.isLoading ? <TableSkeleton /> : null}
              {proofs.map((proof) => (
                <tr key={proof.id} tabIndex={0} onClick={() => setOpen(proof.id)}
                  onKeyDown={(event) => (event.key === "Enter" || event.key === " ") && (event.preventDefault(), setOpen(proof.id))}>
                  <td data-label="Tenant"><strong>{proof.tenant.name}</strong><small>{proof.premises}</small></td>
                  <td data-label="Invoice">{proof.invoice.reference}</td>
                  <td data-label="Amount" className="is-numeric"><strong>{formatMoney(proof.amount)}</strong></td>
                  <td data-label="Method">{proof.method_label}</td>
                  <td data-label="Paid on">{formatDate(proof.paid_on)}</td>
                  <td data-label="Evidence">
                    <span>
                      {evidenceLabel(proof)}
                      {proof.possible_duplicates.length ? <small className="dwella-proof-duplicate">Also on {proof.possible_duplicates[0]}</small> : null}
                    </span>
                  </td>
                  <td data-label="Status"><StatusBadge color={proofBadgeColor[proof.status]}>{proof.status_label}</StatusBadge></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {openId ? <ReviewDrawer key={openId} id={openId} canManage={canManage} onClose={() => setOpen(null)} /> : null}
    </div>
  );
}
