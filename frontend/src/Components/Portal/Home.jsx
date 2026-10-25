import React from "react";
import { Link } from "react-router-dom";
import { Button } from "@fluentui/react-components";

import { useCurrentUserQuery } from "../../Services/queries";
import { usePortalOverview } from "../../Services/portal";
import { paymentMethodLabel } from "../../shared/billing";
import { StatusBadge } from "../../shared/components";
import { formatDate, formatMoney } from "../../shared/format";
import { leaseBadgeProps } from "../../shared/tenancy";
import PortalState from "./PortalState";

function Balance({ overview }) {
  const overdue = Number(overview.overdue_balance) > 0;
  const next = overview.next_due;
  return (
    <section className="dwella-surface dwella-portal-stat">
      <span className="dwella-portal-stat-label">
        Balance due {overdue ? <StatusBadge color="danger">Overdue</StatusBadge> : null}
      </span>
      <strong>{formatMoney(overview.balance)}</strong>
      {next && next.days_overdue > 0 ? (
        <small className="is-danger">Overdue since {formatDate(next.due_date)} · {next.reference}</small>
      ) : Number(overview.balance) > 0 ? (
        <small>Nothing overdue</small>
      ) : (
        <small>You're all paid up.</small>
      )}
      {next ? <Button as={Link} to={`/billing?invoice=${next.id}`}>View invoice</Button> : null}
    </section>
  );
}

function NextDue({ next }) {
  return (
    <section className="dwella-surface dwella-portal-stat">
      <span className="dwella-portal-stat-label">Next payment</span>
      {next ? (
        <>
          <strong>{formatMoney(next.balance)}</strong>
          <small>Due {formatDate(next.due_date)} · {next.reference}</small>
        </>
      ) : (
        <>
          <strong>—</strong>
          <small>No invoices waiting.</small>
        </>
      )}
    </section>
  );
}

export default function PortalHome() {
  const query = usePortalOverview();
  const { data: user } = useCurrentUserQuery({ staleTime: 60_000 });
  return (
    <PortalState query={query} label="your home page">
      {(overview) => (
        <div className="dwella-portal">
          {overview.awaiting_signature.length ? (
            <section className="dwella-portal-banner" aria-label="Awaiting your signature">
              <div>
                <strong>Your lease agreement is ready to sign</strong>
                <p>We emailed the signing link{user?.email ? ` to ${user.email}` : ""}. Open it from that email to review and sign.</p>
              </div>
              <Button as={Link} to="/leases">View agreement</Button>
            </section>
          ) : null}

          <div className="dwella-portal-stats">
            <Balance overview={overview} />
            <NextDue next={overview.next_due} />
            <section className="dwella-surface dwella-portal-stat">
              <span className="dwella-portal-stat-label">Repairs</span>
              <strong>{overview.open_repairs}</strong>
              <small>{overview.open_repairs === 1 ? "Open repair" : "Open repairs"}</small>
              <Button as={Link} to="/maintenance?report=1">Report a repair</Button>
            </section>
          </div>

          <div className="dwella-portal-grid">
            <section className="dwella-surface">
              <h3>Your home</h3>
              {overview.current_leases.length ? (
                <ul className="dwella-portal-list">
                  {overview.current_leases.map((lease) => (
                    <li key={lease.id}>
                      <span>
                        <strong>{lease.property_name} · {lease.unit_name}</strong>
                        <small>{lease.reference} · until {formatDate(lease.end_date)}</small>
                      </span>
                      <StatusBadge {...leaseBadgeProps(lease.status)} />
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="dwella-muted-copy">No current lease. Earlier leases stay under My lease.</p>
              )}
            </section>

            <section className="dwella-surface">
              <div className="dwella-portal-heading">
                <h3>Recent payments</h3>
                <Link to="/billing">All payments</Link>
              </div>
              {overview.recent_payments.length ? (
                <ul className="dwella-portal-list">
                  {overview.recent_payments.map((payment) => (
                    <li key={payment.id}>
                      <span>
                        <Link to={`/billing/receipts/${payment.id}`}>{payment.receipt_number}</Link>
                        <small>{formatDate(payment.paid_on)} · {paymentMethodLabel(payment.method)} · {payment.invoice_reference}</small>
                      </span>
                      <strong>{formatMoney(payment.amount)}</strong>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="dwella-muted-copy">Payments your property manager records will appear here with a receipt.</p>
              )}
            </section>

            <section className="dwella-surface">
              <h3>Your property manager</h3>
              <dl className="dwella-detail-list">
                <div><dt>Name</dt><dd>{overview.manager.name}</dd></div>
                {overview.manager.phone_number ? <div><dt>Phone</dt><dd><a href={`tel:${overview.manager.phone_number}`}>{overview.manager.phone_number}</a></dd></div> : null}
                {overview.manager.email ? <div><dt>Email</dt><dd><a href={`mailto:${overview.manager.email}`}>{overview.manager.email}</a></dd></div> : null}
                {overview.manager.address ? <div><dt>Address</dt><dd>{[overview.manager.address, overview.manager.town].filter(Boolean).join(", ")}</dd></div> : null}
              </dl>
            </section>
          </div>
        </div>
      )}
    </PortalState>
  );
}
