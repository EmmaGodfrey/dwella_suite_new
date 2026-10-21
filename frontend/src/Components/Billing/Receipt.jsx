import React, { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { Link, useParams } from "react-router-dom";
import {
  Button,
  Dialog,
  DialogSurface,
  DialogBody,
  DialogTitle,
  DialogContent,
  DialogActions,
  Field,
  Textarea,
} from "@fluentui/react-components";
import { Print20Regular } from "@fluentui/react-icons";
import { useCurrentUserQuery, useReceiptQuery } from "../../Services/queries";
import { useReversePaymentMutation } from "../../Services/mutations";
import { getUserAccess } from "../../shared/access";
import { paymentMethodLabel } from "../../shared/billing";
import { formatDate } from "../../shared/format";
import { useFormErrors } from "../../shared/useFormErrors";
import "./receipt.scss";

function ReceiptDocument({ receipt }) {
  const issuer = receipt.issuer;
  const money = (value) =>
    new Intl.NumberFormat("en-ZM", {
      style: "currency",
      currency: issuer.currency || "ZMW",
    }).format(Number(value));
  return (
    <article
      className="dwella-receipt-document"
      aria-label={`Payment receipt ${receipt.receipt_number}`}
    >
      <header className="dwella-receipt-heading">
        <div className="dwella-receipt-issuer">
          <strong>{issuer.name}</strong>
          <span>
            {[issuer.address, issuer.town].filter(Boolean).join(", ")}
          </span>
          <span>{issuer.email}</span>
          <span>{issuer.phone_number}</span>
        </div>
        <div className="dwella-receipt-number">
          <span>Payment receipt</span>
          <h1>{receipt.receipt_number}</h1>
          <span>{formatDate(receipt.paid_on)}</span>
        </div>
      </header>
      {receipt.reversed_at ? (
        <div className="dwella-receipt-reversed">
          <strong>REVERSED · {formatDate(receipt.reversed_at)}</strong>
          <p>
            This receipt no longer counts as payment. {receipt.reversal_reason}
          </p>
        </div>
      ) : null}
      <div className="dwella-receipt-parties">
        <section>
          <h2>Received from</h2>
          <strong>{receipt.tenant_name}</strong>
          <p>{receipt.tenant_phone}</p>
        </section>
        <section>
          <h2>Property / unit</h2>
          <strong>{receipt.property_name || "Not linked to a property"}</strong>
          <p>{receipt.unit_name || "—"}</p>
        </section>
      </div>
      <section className="dwella-receipt-amount">
        <span>Amount received</span>
        <strong>{money(receipt.amount)}</strong>
        <span>{paymentMethodLabel(receipt.method)}</span>
      </section>
      <table className="dwella-receipt-allocation">
        <caption>Payment allocation</caption>
        <thead>
          <tr>
            <th scope="col">Applied to</th>
            <th scope="col">Amount</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <strong>{receipt.invoice_reference}</strong>
              <span>Invoice payment</span>
            </td>
            <td>{money(receipt.amount)}</td>
          </tr>
        </tbody>
      </table>
      <dl className="dwella-receipt-details">
        <div>
          <dt>Payment date</dt>
          <dd>{formatDate(receipt.paid_on)}</dd>
        </div>
        <div>
          <dt>Payment method</dt>
          <dd>{paymentMethodLabel(receipt.method)}</dd>
        </div>
        <div>
          <dt>Transaction reference</dt>
          <dd>{receipt.reference || "Not provided"}</dd>
        </div>
        <div>
          <dt>Recorded by</dt>
          <dd>{receipt.recorded_by_name || "—"}</dd>
        </div>
        <div>
          <dt>Invoice total</dt>
          <dd>{money(receipt.invoice_total)}</dd>
        </div>
        <div>
          <dt>Current invoice balance</dt>
          <dd>{money(receipt.current_balance)}</dd>
        </div>
      </dl>
      <footer className="dwella-receipt-footer">
        <p>Thank you for your payment.</p>
        <span>
          Issued {formatDate(receipt.created_at)} · Recorded in Dwella
        </span>
        <small>
          Balance reflects the invoice at the time this copy was viewed. This
          receipt acknowledges a recorded payment and is not a tax invoice.
        </small>
      </footer>
    </article>
  );
}

export default function Receipt() {
  const { id } = useParams();
  const query = useReceiptQuery(id);
  useEffect(() => {
    if (!query.data?.receipt_number) return;
    const previous = document.title;
    document.title = `${query.data.receipt_number} · Payment receipt · Dwella`;
    return () => {
      document.title = previous;
    };
  }, [query.data?.receipt_number]);
  const { data: user } = useCurrentUserQuery();
  const [confirm, setConfirm] = useState(false);
  const [reason, setReason] = useState("");
  const { validate, fieldProps, clearError, showServerErrors } =
    useFormErrors();
  const reversal = useReversePaymentMutation({
    onSuccess: () => setConfirm(false),
    onError: (error) => showServerErrors(error.data, ["reason"]),
  });
  if (query.isLoading) return <p role="status">Loading receipt…</p>;
  if (query.isError)
    return (
      <div role="alert">
        <p>Could not load this receipt.</p>
        <Button onClick={() => query.refetch()}>Retry</Button>{" "}
        <Link to="/billing/receipts">Back to receipts</Link>
      </div>
    );
  const receipt = query.data;
  const reverse = (event) => {
    event.preventDefault();
    if (
      validate(
        {
          reason: () =>
            reason.trim().length >= 5 && reason.trim().length <= 500
              ? ""
              : "Give a reason between 5 and 500 characters.",
        },
        event.currentTarget,
      )
    )
      reversal.mutate({ id, reason: reason.trim() });
  };
  return (
    <div className="dwella-receipt-page">
      <div className="dwella-receipt-toolbar">
        <Link to="/billing/receipts">← Receipts</Link>
        <div>
          {getUserAccess(user).can_manage_properties && !receipt.reversed_at ? (
            <Button onClick={() => setConfirm(true)}>Reverse payment</Button>
          ) : null}
          <Button
            appearance="primary"
            icon={<Print20Regular />}
            onClick={() => window.print()}
          >
            Print / Save PDF
          </Button>
        </div>
      </div>
      <ReceiptDocument receipt={receipt} />
      <p className="dwella-receipt-context">
        <Link to={`/billing/invoices/${receipt.invoice_id}`}>
          View invoice {receipt.invoice_reference}
        </Link>
      </p>
      {createPortal(
        <div className="dwella-print-root">
          <ReceiptDocument receipt={receipt} />
        </div>,
        document.body,
      )}
      <Dialog
        open={confirm}
        onOpenChange={(_, data) => !reversal.isPending && setConfirm(data.open)}
      >
        <DialogSurface>
          <form onSubmit={reverse}>
            <DialogBody>
              <DialogTitle>Reverse {receipt.receipt_number}?</DialogTitle>
              <DialogContent>
                <p>
                  The invoice balance will reopen. The original receipt and your
                  reason remain on record. This does not refund a bank or
                  mobile-money transaction.
                </p>
                <Field label="Reason for correction" {...fieldProps("reason")}>
                  <Textarea
                    value={reason}
                    maxLength={500}
                    onChange={(_, data) => {
                      setReason(data.value);
                      clearError("reason");
                    }}
                  />
                </Field>
                {reversal.isError ? (
                  <p role="alert">{reversal.error.message}</p>
                ) : null}
              </DialogContent>
              <DialogActions>
                <Button
                  disabled={reversal.isPending}
                  onClick={() => setConfirm(false)}
                >
                  Keep payment
                </Button>
                <Button
                  type="submit"
                  appearance="primary"
                  disabled={reversal.isPending}
                >
                  {reversal.isPending ? "Reversing…" : "Reverse payment"}
                </Button>
              </DialogActions>
            </DialogBody>
          </form>
        </DialogSurface>
      </Dialog>
    </div>
  );
}
