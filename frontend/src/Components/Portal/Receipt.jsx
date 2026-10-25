import React, { useEffect } from "react";
import { createPortal } from "react-dom";
import { Link, useParams } from "react-router-dom";
import { Button } from "@fluentui/react-components";
import { Print20Regular } from "@fluentui/react-icons";

import { usePortalReceipt } from "../../Services/portal";
import { StatusBadge } from "../../shared/components";
import PaymentReceipt from "../../shared/components/PaymentReceipt";
import PortalState from "./PortalState";

export default function PortalReceipt() {
  const { id } = useParams();
  const query = usePortalReceipt(id);
  useEffect(() => {
    if (!query.data?.receipt_number) return;
    const previous = document.title;
    document.title = `${query.data.receipt_number} · Payment receipt · Dwella`;
    return () => { document.title = previous; };
  }, [query.data?.receipt_number]);
  return <PortalState query={query} label="this receipt">
    {(receipt) => <div className="dwella-receipt-page">
      <div className="dwella-receipt-toolbar">
        <Link to="/billing">← Payments</Link>
        <div><StatusBadge color={receipt.reversed ? "subtle" : "success"}>
          {receipt.reversed ? "Reversed" : "Payment received"}
        </StatusBadge>
          <Button appearance="primary" icon={<Print20Regular />} onClick={() => window.print()}>Print / Save PDF</Button>
        </div>
      </div>
      <PaymentReceipt receipt={receipt} />
      <p className="dwella-receipt-context"><Link to={`/billing?invoice=${receipt.invoice_id}`}>
        View invoice {receipt.invoice_reference}
      </Link></p>
      {createPortal(<div className="dwella-print-root"><PaymentReceipt receipt={receipt} /></div>, document.body)}
    </div>}
  </PortalState>;
}
