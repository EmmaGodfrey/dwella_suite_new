import React from "react";
import { Link } from "react-router-dom";
import { Button } from "@fluentui/react-components";
import { useManagerCollections } from "../../Services/payments";
import { formatMoney } from "../../shared/format";
import { StatusBadge } from "../../shared/components";
import { destinationShort } from "../../shared/payouts";
import "./payments.scss";

const labels = { pending: "Awaiting payment", successful: "Paid", failed: "Failed", review: "Needs review", expired: "Not completed" };
const payoutLabels = { queued: "Payout queued", submitting: "Payout being submitted", pending: "Payout processing", successful: "Payout delivered", failed: "Payout failed", review: "Payout needs review" };

export default function OnlineCollections({ invoiceId }) {
  const query = useManagerCollections(invoiceId);
  const rows = query.data?.results || [];
  if (!query.isLoading && !query.isError && !rows.length) return null;
  return (
    <section className="dwella-surface dwella-online-collections">
      <h3>Online collections</h3>
      {query.isLoading ? <p role="status">Loading online payments…</p> : null}
      {query.isError ? <p role="alert">Could not load collection statuses. <Button size="small" onClick={() => query.refetch()}>Retry</Button></p> : null}
      <ul>{rows.map((row) => (
        <li key={row.id}>
          <div className="dwella-badge-row"><strong>{formatMoney(row.amount)}</strong><StatusBadge color={row.status === "successful" ? "success" : row.status === "failed" || row.status === "review" ? "danger" : row.status === "expired" ? "subtle" : "warning"}>{labels[row.status] || row.status}</StatusBadge></div>
          <small>{row.reference}</small>
          {row.status === "successful" ? <>
            <span>{row.settled ? `${formatMoney(row.settled_amount)} settled after collection fees` : "Awaiting settlement from Lenco"}</span>
            {row.fee !== null ? <small>Collection fee: {formatMoney(row.fee)}</small> : null}
          </> : null}
          {row.payout ? <>
            <span>{payoutLabels[row.payout.status] || row.payout.status}</span>
            {row.destination ? <small>Receiving account: {row.destination.account_name} · {destinationShort(row.destination)}</small> : null}
          </> : row.settled ? <small>Added to your balance. <Link to="/billing/payouts">Withdraw from Payouts</Link></small> : null}
          {row.status === "review" || ["failed", "review"].includes(row.payout?.status) ? <small role="status">Contact Dwella support with this collection reference. Confirmed rent remains recorded.</small> : null}
        </li>
      ))}</ul>
    </section>
  );
}
