import React from "react";
import { paymentMethodLabel } from "../billing";
import { formatDate } from "../format";
import "./paymentReceipt.scss";

export default function PaymentReceipt({ receipt }) {
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

