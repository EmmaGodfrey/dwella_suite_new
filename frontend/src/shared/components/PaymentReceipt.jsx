import React from "react";
import { paymentMethodLabel } from "../billing";
import { formatDate } from "../format";
import "./paymentReceipt.scss";

export default function PaymentReceipt({ receipt }) {
  if (receipt.missing_details?.length) return <div className="dwella-callout is-warning" role="status">
    <strong>Payment recorded; tenant details needed for the receipt</strong>
    <p>{receipt.missing_details.map(item => item.label).join(", ")}. Complete these details to issue the document. The payment remains recorded.</p>
  </div>;
  const issuer = receipt.issuer;
  const money = (value) =>
    new Intl.NumberFormat("en-ZM", {
      style: "currency",
      currency: issuer.currency || "ZMW",
    }).format(Number(value));
  // Older API responses have no split; show the whole payment against the invoice.
  const allocation = receipt.allocation?.length
    ? receipt.allocation
    : [{ kind: "charges", label: "Invoice payment", note: "", document: receipt.invoice_reference, period: null, amount: receipt.amount }];
  const formatMonth = (value) =>
    new Date(`${value}T00:00:00`).toLocaleDateString("en-GB", { month: "short", year: "numeric" });
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
          {receipt.tenant_phone && <p>{receipt.tenant_phone}</p>}
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
        <caption>How this payment was allocated</caption>
        <thead>
          <tr>
            <th scope="col">Applied to</th>
            <th scope="col">Document</th>
            <th scope="col">Period</th>
            <th scope="col">Amount</th>
          </tr>
        </thead>
        <tbody>
          {allocation.map((row) => (
            <tr key={row.kind} className={row.kind === "deposit" ? "is-deposit" : undefined}>
              <td>
                <strong>{row.label}</strong>
                {row.note ? <span>{row.note}</span> : null}
              </td>
              <td>{row.document}</td>
              <td>{row.period ? formatMonth(row.period) : "—"}</td>
              <td>{money(row.amount)}</td>
            </tr>
          ))}
        </tbody>
        {allocation.length > 1 ? (
          <tfoot>
            <tr>
              <th scope="row" colSpan={3}>Total allocated</th>
              <td>{money(receipt.amount)}</td>
            </tr>
          </tfoot>
        ) : null}
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
        {receipt.recorded_by_name !== undefined && <div>
          <dt>Recorded by</dt>
          <dd>{receipt.recorded_by_name || "—"}</dd>
        </div>}
        <div>
          <dt>Invoice total</dt>
          <dd>{money(receipt.invoice_total)}</dd>
        </div>
        <div>
          <dt>Current invoice balance</dt>
          <dd>{money(receipt.current_balance)}</dd>
        </div>
        {receipt.deposit_held ? (
          <div>
            <dt>Deposit now held for tenant</dt>
            <dd>{money(receipt.deposit_held)}</dd>
          </div>
        ) : null}
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

