import React, { useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  Button,
  Dialog,
  DialogActions,
  DialogBody,
  DialogContent,
  DialogSurface,
  DialogTitle,
  Field,
  Textarea,
} from "@fluentui/react-components";
import { Money20Regular, Receipt24Regular } from "@fluentui/react-icons";
import { toast } from "react-toastify";

import { useSaveInvoiceMutation, useVoidInvoiceMutation } from "../../Services/mutations";
import { useCurrentUserQuery, useInvoiceQuery } from "../../Services/queries";
import { getUserAccess } from "../../shared/access";
import { invoiceBadgeProps, lineKinds, paymentMethodLabel, periodLabel } from "../../shared/billing";
import { EmptyState, StatusBadge } from "../../shared/components";
import { formatDate, formatMoney } from "../../shared/format";
import RecordPaymentDrawer from "./RecordPaymentDrawer";
import "../../shared/records.scss";
import "./billing.scss";
import { useInvoiceDocument } from "../../Services/documents";
import DocumentPreview from "../Documents/DocumentPreview";

const kindLabel = (kind) => lineKinds.find((item) => item.value === kind)?.label || kind;

function NoteEditor({ invoice }) {
  const [notes, setNotes] = useState(invoice.notes || "");
  const dirty = notes.trim() !== (invoice.notes || "").trim();
  const mutation = useSaveInvoiceMutation({
    onSuccess: () => toast.success("Note saved."),
    onError: (error) => toast.error(error.message || "Could not save the note."),
  });
  return (
    <div className="dwella-note-editor">
      <Field label="Internal note" hint="Only your team sees this.">
        <Textarea rows={2} value={notes} onChange={(_, d) => setNotes(d.value)} />
      </Field>
      {dirty ? (
        <Button size="small" disabled={mutation.isPending} onClick={() => mutation.mutate({ id: invoice.id, payload: { notes: notes.trim() } })}>
          {mutation.isPending ? "Saving…" : "Save note"}
        </Button>
      ) : null}
    </div>
  );
}

export default function InvoiceDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: user } = useCurrentUserQuery({ staleTime: 60_000 });
  const canManage = getUserAccess(user).can_manage_properties;
  const invoiceQuery = useInvoiceQuery(id, { staleTime: 15_000 });
  const invoice = invoiceQuery.data;
  const [paying, setPaying] = useState(false);
  const [confirmVoid, setConfirmVoid] = useState(false);
  const [document, setDocument] = useState(null);
  const previewButton = useRef(null);
  const preview = useInvoiceDocument({ onSuccess: setDocument, onError: error => toast.error(error.message || "Could not prepare the invoice PDF.") });
  const voidMutation = useVoidInvoiceMutation({
    onSuccess: (data) => {
      toast.success(`${data.reference} voided.`);
      setConfirmVoid(false);
    },
    onError: (error) => toast.error(error.message || "Could not void the invoice."),
  });

  if (invoiceQuery.isLoading) {
    return (
      <div className="dwella-invoice-detail" aria-busy="true">
        <span className="dwella-skeleton" style={{ height: 28, width: 200 }} />
        <span className="dwella-skeleton" style={{ height: 260, width: "100%" }} />
      </div>
    );
  }
  if (invoiceQuery.isError || !invoice) {
    return (
      <EmptyState
        icon={<Receipt24Regular />}
        title="Invoice not found"
        description="It may belong to another workspace."
        actionLabel="Back to billing"
        onAction={() => window.history.back()}
      />
    );
  }

  const isVoid = invoice.status === "void";
  const owing = Number(invoice.balance) > 0 && !isVoid;

  return (
    <div className="dwella-invoice-detail">

      <header className="dwella-detail-header">
        <div>
          <div className="dwella-detail-title">
            <h1>{invoice.reference}</h1>
            <StatusBadge {...invoiceBadgeProps(invoice)} />
          </div>
          <p>
            {invoice.tenant_name}
            {invoice.unit_name ? ` · ${invoice.unit_name}, ${invoice.property_name}` : ""} · {periodLabel(invoice.period_start)}
          </p>
        </div>
        {canManage ? (
          <div className="dwella-detail-actions">
            <Button ref={previewButton} disabled={preview.isPending} onClick={() => preview.mutate(invoice.id)}>{preview.isPending ? "Preparing PDF…" : document ? "Refresh invoice preview" : "Preview invoice"}</Button>
            {!isVoid && !invoice.payments.some((payment) => !payment.reversed_at) ? <Button onClick={() => setConfirmVoid(true)}>Void</Button> : null}
            {owing ? (
              <Button appearance="primary" icon={<Money20Regular />} onClick={() => setPaying(true)}>Record payment</Button>
            ) : null}
          </div>
        ) : null}
      </header>

      <div className={`dwella-invoice-workspace${document ? " has-preview" : ""}`}>
        <div className="dwella-invoice-grid">
          <section className="dwella-surface">
            <div className="dwella-invoice-meta">
              <div><span>Bill to</span><strong>{invoice.tenant_name}</strong><small>{invoice.tenant_phone}</small></div>
              <div><span>Issued</span><strong>{formatDate(invoice.issue_date)}</strong></div>
              <div><span>Due</span><strong>{formatDate(invoice.due_date)}</strong></div>
              {invoice.lease_reference ? <div><span>Lease</span><strong>{invoice.lease_reference}</strong></div> : null}
            </div>

            <table className="dwella-table dwella-lines-table">
              <thead>
                <tr><th scope="col">Description</th><th scope="col">Type</th><th scope="col" className="is-numeric">Amount</th></tr>
              </thead>
              <tbody>
                {invoice.lines.map((line, index) => (
                  <tr key={index}>
                    <td><strong>{line.description}</strong></td>
                    <td>{kindLabel(line.kind)}</td>
                    <td className={`is-numeric ${line.kind === "late_fee" ? "is-negative" : ""}`}>{formatMoney(line.amount)}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            <dl className="dwella-detail-list dwella-invoice-totals">
              <div><dt>Total</dt><dd>{formatMoney(invoice.total)}</dd></div>
              <div><dt>Paid</dt><dd>{formatMoney(invoice.amount_paid)}</dd></div>
              <div className="is-balance"><dt>Balance due</dt><dd className={owing ? (invoice.days_overdue > 0 ? "is-negative" : "") : ""}>{isVoid ? "Void" : formatMoney(invoice.balance)}</dd></div>
            </dl>
          </section>

          <aside className="dwella-invoice-rail">
            <section className="dwella-surface">
              <h3>Payments</h3>
              {invoice.payments.length ? (
                <ul className="dwella-payment-list">
                  {invoice.payments.map((payment) => (
                    <li key={payment.id}>
                      <div>
                        <strong>{formatMoney(payment.amount)}</strong>
                        <small>{paymentMethodLabel(payment.method)} · {formatDate(payment.paid_on)}{payment.reference ? ` · ${payment.reference}` : ""}</small>
                        <small><Link to={`/billing/receipts/${payment.id}`}>{payment.receipt_number}</Link>{payment.reversed_at ? " · Reversed" : ""}{payment.recorded_by_name ? ` · recorded by ${payment.recorded_by_name}` : ""}</small>
                      </div>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="dwella-muted-copy">{isVoid ? "This invoice was voided." : "No payments yet."}</p>
              )}
            </section>
            {canManage ? (
              <section className="dwella-surface">
                <NoteEditor key={invoice.id + (invoice.notes || "")} invoice={invoice} />
              </section>
            ) : invoice.notes ? (
              <section className="dwella-surface"><h3>Note</h3><p className="dwella-muted-copy">{invoice.notes}</p></section>
            ) : null}
          </aside>
        </div>
        {document && <DocumentPreview key={`${document.id}-${document.sha256}`} document={document} returnFocusRef={previewButton} onClose={() => setDocument(null)} />}
      </div>

      {paying ? <RecordPaymentDrawer invoice={invoice} onClose={() => setPaying(false)} onSaved={(data) => {
        setPaying(false);
        if (data.recorded_payment) navigate(`/billing/receipts/${data.recorded_payment.id}`);
      }} /> : null}

      <Dialog open={confirmVoid} onOpenChange={(_, data) => !voidMutation.isPending && setConfirmVoid(data.open)}>
        <DialogSurface>
          <DialogBody>
            <DialogTitle>Void {invoice.reference}?</DialogTitle>
            <DialogContent>
              The tenant will no longer owe {formatMoney(invoice.total)} on this invoice. It stays on record as void. For rent, you can generate the month again afterwards.
            </DialogContent>
            <DialogActions>
              <Button disabled={voidMutation.isPending} onClick={() => setConfirmVoid(false)}>Keep invoice</Button>
              <Button appearance="primary" disabled={voidMutation.isPending} onClick={() => voidMutation.mutate({ id: invoice.id })}>
                {voidMutation.isPending ? "Voiding…" : "Void invoice"}
              </Button>
            </DialogActions>
          </DialogBody>
        </DialogSurface>
      </Dialog>
    </div>
  );
}
