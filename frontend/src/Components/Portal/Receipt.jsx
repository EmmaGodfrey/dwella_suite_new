import React from "react";
import { Link, useParams } from "react-router-dom";
import { Button } from "@fluentui/react-components";
import { Print20Regular } from "@fluentui/react-icons";

import { usePortalReceipt } from "../../Services/portal";
import { paymentMethodLabel } from "../../shared/billing";
import { StatusBadge } from "../../shared/components";
import { formatDate, formatMoney } from "../../shared/format";
import PortalState from "./PortalState";

export default function PortalReceipt() {
  const { id } = useParams();
  const query = usePortalReceipt(id);
  return (
    <PortalState query={query} label="this receipt">
      {(receipt) => (
        <article className="dwella-surface dwella-portal-receipt" aria-label={`Receipt ${receipt.receipt_number}`}>
          <div className="dwella-portal-heading">
            <h2>Receipt {receipt.receipt_number}</h2>
            {receipt.reversed ? <StatusBadge color="subtle">Reversed {formatDate(receipt.reversed_at)}</StatusBadge> : <StatusBadge color="success">Paid</StatusBadge>}
          </div>
          <p className="dwella-muted-copy">
            {[receipt.issuer.name, receipt.issuer.address, receipt.issuer.town].filter(Boolean).join(" · ")}
          </p>
          <p className="dwella-portal-amount">{formatMoney(receipt.amount)}</p>
          {receipt.reversed ? (
            <p className="dwella-callout is-warning">This payment was reversed and no longer counts toward your balance.</p>
          ) : null}
          <dl className="dwella-detail-list">
            <div><dt>Received from</dt><dd>{receipt.tenant_name}</dd></div>
            <div><dt>For</dt><dd><Link to={`/billing?invoice=${receipt.invoice_id}`}>{receipt.invoice_reference}</Link></dd></div>
            {receipt.property_name ? <div><dt>Home</dt><dd>{receipt.property_name} · {receipt.unit_name}</dd></div> : null}
            <div><dt>Paid on</dt><dd>{formatDate(receipt.paid_on)}</dd></div>
            <div><dt>Method</dt><dd>{paymentMethodLabel(receipt.method)}</dd></div>
            <div><dt>Reference</dt><dd>{receipt.reference || "—"}</dd></div>
            <div><dt>Invoice total</dt><dd>{formatMoney(receipt.invoice_total)}</dd></div>
            <div><dt>Invoice balance</dt><dd>{formatMoney(receipt.current_balance)}</dd></div>
          </dl>
          <div className="dwella-portal-print">
            <Button icon={<Print20Regular />} onClick={() => window.print()}>Print receipt</Button>
          </div>
        </article>
      )}
    </PortalState>
  );
}
