import React, { useCallback, useLayoutEffect, useRef, useState } from "react";
import { Button, Select } from "@fluentui/react-components";
import { formatDate, formatMoney } from "../../shared/format";

/** Live wording preview; the saved PDF supplies final pagination and signing. */
export default function AgreementDraft({ lease, values, signer }) {
  const viewport = useRef(null);
  const paper = useRef(null);
  const flow = useRef(null);
  const [page, setPage] = useState(1);
  const [layout, setLayout] = useState({ scale: 1, step: 0, count: 1 });
  const measure = useCallback(() => {
    if (!viewport.current || !paper.current || !flow.current) return;
    const width = flow.current.clientWidth;
    if (!width || !paper.current.offsetWidth || !viewport.current.clientWidth) return;
    // Fixed-size CSS columns keep draft pagination stable as the preview scales.
    const gap = parseFloat(getComputedStyle(flow.current).columnGap) || 0;
    const next = {
      scale: Math.min(1, viewport.current.clientWidth / paper.current.offsetWidth),
      step: width + gap,
      count: Math.max(1, Math.ceil((flow.current.scrollWidth + gap - 1) / (width + gap))),
    };
    setLayout(current => current.scale === next.scale && current.step === next.step
      && current.count === next.count ? current : next);
    setPage(current => Math.min(current, next.count));
  }, []);
  useLayoutEffect(() => {
    let active = true;
    const observer = new ResizeObserver(measure);
    observer.observe(viewport.current);
    observer.observe(paper.current);
    document.fonts.ready.then(() => { if (active) measure(); });
    measure();
    return () => { active = false; observer.disconnect(); };
  }, [measure]);
  useLayoutEffect(measure, [measure, lease, signer, values.landlord_name,
    values.landlord_address, values.agreement_text, values.schedule_text]);
  const currentPage = Math.min(page, layout.count);
  return <section className="dwella-agreement-draft" aria-label="Live agreement draft">
    <div className="dwella-document-heading"><div><h3>Agreement preview</h3><p>Updates as you edit · Unsaved draft</p></div></div>
    <div className="dwella-document-toolbar">
      <div className="dwella-document-actions">
        <Button disabled={currentPage <= 1} onClick={() => setPage(value => value - 1)}>Previous</Button>
        <Select aria-label="Draft preview page" value={String(currentPage)} onChange={(_, data) => setPage(Number(data.value))}>
          {Array.from({ length: layout.count }, (_, index) => <option key={index + 1} value={index + 1}>Page {index + 1} of {layout.count}</option>)}
        </Select>
        <Button disabled={currentPage >= layout.count} onClick={() => setPage(value => value + 1)}>Next</Button>
      </div>
    </div>
    <p className="dwella-document-fineprint">A4 draft · Approximate page breaks. Prepare the document to review the final PDF before signing.</p>
    <div className="dwella-paper-stage is-fit">
      <div className="dwella-draft-viewport" ref={viewport}>
        <article className="dwella-draft-paper" ref={paper} style={{ transform: `scale(${layout.scale})` }}>
          <div className="dwella-draft-content">
            <div className="dwella-draft-flow" ref={flow} style={{ transform: `translateX(-${(currentPage - 1) * layout.step}px)` }}>
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
            </div>
          </div>
          <footer className="dwella-draft-footer"><span>{lease.reference} · Unsaved draft</span><span>Page {currentPage} of {layout.count}</span></footer>
        </article>
      </div>
    </div>
    <p className="dwella-document-fineprint" role="status">Draft page {currentPage} of {layout.count}</p>
  </section>;
}
