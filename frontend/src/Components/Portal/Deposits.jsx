import React, { useState } from "react";
import { Button, Field, Textarea } from "@fluentui/react-components";
import { toast } from "react-toastify";
import { useRespondToDeduction, useTenantDeposits } from "../../Services/payments";
import { StatusBadge } from "../../shared/components";
import { formatDate, formatMoney } from "../../shared/format";
import { DepositHistory, DepositSummary, EvidenceList, PaysInvoice } from "../Billing/DepositDrawer";
import "../Billing/deposits.scss";

const tone = { proposed: "warning", accepted: "informative", disputed: "danger", applied: "success" };

function Deduction({ row }) {
  const respond = useRespondToDeduction();
  const [disputing, setDisputing] = useState(false);
  const [note, setNote] = useState("");
  const send = async (decision) => {
    try {
      await respond.mutateAsync({ id: row.id, decision, note });
      toast.success(decision === "accept" ? "You accepted this deduction." : "Your dispute was sent to your property manager.");
      setDisputing(false);
    } catch (error) {
      toast.error(error.data?.note?.[0] || error.message || "Could not send your answer.");
    }
  };
  const waiting = row.status === "proposed";
  return <article className="dwella-deposit-deduction">
    <div className="dwella-deposit-deduction-head"><strong>{row.reason}</strong><strong>{formatMoney(row.amount)}</strong></div>
    <p className="dwella-deposit-muted">Proposed {formatDate(row.proposed_on)}{row.details ? ` · ${row.details}` : ""}</p>
    <PaysInvoice row={row} />
    <div className="dwella-deposit-status">
      <StatusBadge color={tone[row.status] || "subtle"}>{row.status_label}</StatusBadge>
      {row.tenant_note && <span>Your note: “{row.tenant_note}”</span>}
      {row.resolution_note && <span>Resolution: {row.resolution_note}</span>}
    </div>
    <EvidenceList items={row.evidence} scope="portal" />
    {row.can_respond && <div className="dwella-deposit-row-actions">
      {disputing ? <>
        <Field label="Why do you disagree?" className="dwella-deposit-resolution">
          <Textarea value={note} maxLength={1000} onChange={(_, d) => setNote(d.value)}
            placeholder="For example: the damage was there when I moved in, or it is normal wear and tear." />
        </Field>
        <Button size="small" appearance="primary" disabled={respond.isPending || !note.trim()} onClick={() => send("dispute")}>Send dispute</Button>
        <Button size="small" appearance="subtle" disabled={respond.isPending} onClick={() => setDisputing(false)}>Back</Button>
      </> : <>
        {waiting || row.status === "disputed" ? <Button size="small" appearance="primary" disabled={respond.isPending} onClick={() => send("accept")}>Accept</Button> : null}
        {row.status !== "disputed" && <Button size="small" disabled={respond.isPending} onClick={() => setDisputing(true)}>Dispute</Button>}
      </>}
    </div>}
  </article>;
}

/** The tenant's deposits: what is held for them, deductions to answer, history. */
export default function TenantDeposits() {
  const query = useTenantDeposits();
  if (query.isPending || query.isError || !query.data?.length) return null;
  return query.data.map((deposit) => <section key={deposit.lease.id} className="dwella-surface" aria-label={`Security deposit for lease ${deposit.lease.reference}`}>
    <h3>Security deposit · Lease {deposit.lease.reference}</h3>
    <div className="dwella-deposit">
      <DepositSummary deposit={deposit} />
      {deposit.deductions.length > 0 && <section aria-label="Deductions">
        <h3>Deductions</h3>
        <p className="dwella-deposit-muted dwella-deposit-intro">Nothing is taken from your deposit until you accept or a dispute is resolved.</p>
        {deposit.deductions.map((row) => <Deduction key={row.id} row={row} />)}
      </section>}
      <section aria-label="Deposit history">
        <h3>History</h3>
        <DepositHistory entries={deposit.entries} />
      </section>
    </div>
  </section>);
}
