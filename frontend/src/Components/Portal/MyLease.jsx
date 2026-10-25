import React, { useState } from "react";
import { Button } from "@fluentui/react-components";
import { ArrowDownload20Regular, Dismiss20Regular } from "@fluentui/react-icons";
import { toast } from "react-toastify";

import { downloadPortalFile, portalDocuments, usePortalLeaseDocuments, usePortalLeases } from "../../Services/portal";
import { StatusBadge } from "../../shared/components";
import { formatDate, formatMoney } from "../../shared/format";
import { leaseBadgeProps } from "../../shared/tenancy";
import { PaperPreview } from "../Documents/DocumentPreview";
import PortalState from "./PortalState";

const versionStatus = {
  signing: ["warning", "Awaiting signatures"],
  signed: ["success", "Fully signed"],
};

function Documents({ lease }) {
  const query = usePortalLeaseDocuments(lease.id);
  const [open, setOpen] = useState(null);
  if (query.isLoading) return <span className="dwella-skeleton" style={{ height: 80, width: "100%" }} />;
  if (query.isError) return <p role="alert">Could not load documents. <Button size="small" onClick={() => query.refetch()}>Retry</Button></p>;
  const { versions, originals } = query.data;
  if (!versions.length && !originals.length) {
    return <p className="dwella-muted-copy">No agreement has been shared yet. It appears here once your property manager sends it for signing.</p>;
  }
  return (
    <>
      <ul className="dwella-portal-list">
        {versions.map((doc) => {
          const [color, label] = versionStatus[doc.status] || ["subtle", doc.status];
          return (
            <li key={doc.id}>
              <span>
                <strong>Lease agreement · version {doc.version}</strong>
                <small>
                  {doc.awaiting_your_signature
                    ? "Waiting for your signature. Use the link in your email to sign."
                    : doc.signatures.map((signature) => `${signature.signer_name} signed ${formatDate(signature.signed_at)}`).join(" · ") || `Shared ${formatDate(doc.created_at)}`}
                </small>
              </span>
              <span className="dwella-badge-row">
                <StatusBadge color={doc.awaiting_your_signature ? "danger" : color}>{doc.awaiting_your_signature ? "Awaiting your signature" : label}</StatusBadge>
                <Button size="small" onClick={() => setOpen(doc)}>View</Button>
              </span>
            </li>
          );
        })}
        {originals.map((original) => (
          <li key={original.id}>
            <span>
              <strong>{original.filename}</strong>
              <small>Signed original · {original.page_count} {original.page_count === 1 ? "page" : "pages"} · added {formatDate(original.created_at)}</small>
            </span>
            <Button
              size="small"
              icon={<ArrowDownload20Regular />}
              onClick={() => downloadPortalFile(`originals/${original.id}/pdf/`, original.filename).catch((error) => toast.error(error.message || "Could not download the file."))}
            >
              Download
            </Button>
          </li>
        ))}
      </ul>
      {open ? (
        <section className="dwella-document-workspace" aria-label="Lease agreement">
          <div className="dwella-document-heading">
            <div>
              <h2>Lease agreement</h2>
              <p>{lease.reference} · version {open.version}</p>
            </div>
            <Button appearance="subtle" icon={<Dismiss20Regular />} aria-label="Close agreement" onClick={() => setOpen(null)} />
          </div>
          <PaperPreview doc={{ ...open, snapshot: { reference: lease.reference } }} client={portalDocuments} accessKey="portal" />
        </section>
      ) : null}
    </>
  );
}

function Terms({ lease }) {
  return (
    <dl className="dwella-detail-list">
      <div><dt>Home</dt><dd>{lease.property_name} · {lease.unit_name}</dd></div>
      {lease.property_address ? <div><dt>Address</dt><dd>{lease.property_address}</dd></div> : null}
      <div><dt>Term</dt><dd>{formatDate(lease.start_date)} – {formatDate(lease.end_date)}</dd></div>
      <div><dt>Monthly rent</dt><dd>{formatMoney(lease.monthly_rent)}</dd></div>
      <div><dt>Due</dt><dd>Day {lease.rent_due_day} of each month</dd></div>
      <div><dt>Deposit</dt><dd>{formatMoney(lease.deposit_amount)}</dd></div>
      <div><dt>Late fee</dt><dd>{Number(lease.late_fee_percent) ? `${Number(lease.late_fee_percent)}% after ${lease.late_fee_grace_days} days` : "None"}</dd></div>
      <div><dt>Notice period</dt><dd>{lease.notice_period_months} {lease.notice_period_months === 1 ? "month" : "months"}</dd></div>
    </dl>
  );
}

export default function PortalLease() {
  const query = usePortalLeases();
  return (
    <PortalState query={query} label="your lease">
      {(data) => {
        const leases = data.results || [];
        const current = leases.filter((lease) => ["active", "pending_signature"].includes(lease.status));
        const earlier = leases.filter((lease) => !current.includes(lease));
        if (!leases.length) {
          return <p className="dwella-muted-copy">No lease has been shared with you yet.</p>;
        }
        return (
          <div className="dwella-portal">
            {current.map((lease) => (
              <div key={lease.id} className="dwella-portal-grid">
                <section className="dwella-surface">
                  <div className="dwella-portal-heading">
                    <h3>Lease {lease.reference}</h3>
                    <StatusBadge {...leaseBadgeProps(lease.status)} />
                  </div>
                  <Terms lease={lease} />
                </section>
                <section className="dwella-surface">
                  <h3>Documents</h3>
                  <Documents lease={lease} />
                </section>
              </div>
            ))}
            {earlier.length ? (
              <section className="dwella-surface">
                <h3>{current.length ? "Earlier and upcoming leases" : "Your leases"}</h3>
                <ul className="dwella-portal-list">
                  {earlier.map((lease) => (
                    <li key={lease.id}>
                      <span>
                        <strong>{lease.reference} · {lease.property_name} · {lease.unit_name}</strong>
                        <small>{formatDate(lease.start_date)} – {formatDate(lease.end_date)} · {formatMoney(lease.monthly_rent)} a month</small>
                      </span>
                      <StatusBadge {...leaseBadgeProps(lease.status)} />
                    </li>
                  ))}
                </ul>
              </section>
            ) : null}
          </div>
        );
      }}
    </PortalState>
  );
}
