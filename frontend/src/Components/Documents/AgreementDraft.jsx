import React from "react";
import { formatDate, formatMoney } from "../../shared/format";

/** Live wording preview; the saved PDF supplies final pagination and signing. */
export default function AgreementDraft({ lease, values, signer }) {
  return <section className="dwella-agreement-draft" aria-label="Live agreement draft">
    <div className="dwella-document-heading"><div><h3>Agreement preview</h3><p>Updates as you edit · Unsaved draft</p></div></div>
    <p className="dwella-document-fineprint">Prepare the document to review the final PDF and page breaks before signing.</p>
    <div className="dwella-paper-stage is-fit">
      <article className="dwella-draft-paper">
        <header><strong>{values.landlord_name || "Landlord legal name"}</strong><span>{values.landlord_address || "Landlord address"}</span></header>
        <h2>Lease agreement</h2>
        <p className="dwella-draft-reference">{lease.reference} · Draft</p>
        <h3>Parties and premises</h3>
        <dl>
          <div><dt>Landlord</dt><dd>{values.landlord_name || "To be supplied"}</dd></div>
          <div><dt>Tenant</dt><dd>{lease.tenant_name}</dd></div>
          <div><dt>Premises</dt><dd>{lease.unit_name}, {lease.property_name}</dd></div>
          <div><dt>Term</dt><dd>{formatDate(lease.start_date)} – {formatDate(lease.end_date)}</dd></div>
          <div><dt>Monthly rent</dt><dd>{formatMoney(lease.monthly_rent)} · Due on day {lease.rent_due_day}</dd></div>
          <div><dt>Deposit</dt><dd>{formatMoney(lease.deposit_amount)}</dd></div>
          <div><dt>Late fee</dt><dd>{Number(lease.late_fee_percent) ? `${Number(lease.late_fee_percent)}% after ${lease.late_fee_grace_days} days` : "None"}</dd></div>
          <div><dt>Notice period</dt><dd>{lease.notice_period_months} {lease.notice_period_months === 1 ? "month" : "months"}</dd></div>
        </dl>
        <h3>Agreement wording</h3>
        <p className="dwella-draft-wording">{values.agreement_text || "Your complete approved agreement wording will appear here."}</p>
        {values.schedule_text && <><h3>Schedules and additional terms</h3><p className="dwella-draft-wording">{values.schedule_text}</p></>}
        <h3>Signatures</h3>
        <div className="dwella-draft-signatures"><div><span>For the landlord</span><strong>{signer?.name || "Choose an authorised signatory"}</strong></div><div><span>Tenant</span><strong>{lease.tenant_name}</strong></div></div>
      </article>
    </div>
  </section>;
}
