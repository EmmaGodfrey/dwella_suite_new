import React, { useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  Button,
  Dialog,
  DialogActions,
  DialogBody,
  DialogContent,
  DialogSurface,
  DialogTitle,
} from "@fluentui/react-components";
import { ArrowLeft20Regular, CheckmarkCircle20Regular, DocumentText24Regular, Person20Regular } from "@fluentui/react-icons";
import { toast } from "react-toastify";

import { useLeaseActionMutation } from "../../Services/mutations";
import { useCurrentUserQuery, useLeaseQuery } from "../../Services/queries";
import { getUserAccess } from "../../shared/access";
import { EmptyState, StatusBadge } from "../../shared/components";
import { daysUntil, formatDate, formatMoney } from "../../shared/format";
import { leaseBadgeProps } from "../../shared/tenancy";
import "../../shared/records.scss";
import "./leases.scss";

function History({ lease }) {
  const events = [
    { label: "Lease created", when: lease.created_at, done: true },
    lease.activated_at ? { label: "Started — unit marked occupied", when: lease.activated_at, done: true } : null,
    lease.ended_at ? { label: "Ended — unit marked vacant", when: lease.ended_at, done: true } : null,
    !lease.activated_at && lease.status !== "ended" ? { label: "Waiting to start", when: null, done: false } : null,
  ].filter(Boolean);

  return (
    <ol className="dwella-timeline">
      {events.map((event) => (
        <li key={event.label} className={event.done ? "is-done" : "is-pending"}>
          <strong>{event.label}</strong>
          <small>{event.when ? formatDate(event.when) : "Start the lease when the tenant moves in."}</small>
        </li>
      ))}
    </ol>
  );
}

export default function LeaseDetail() {
  const { id } = useParams();
  const { data: user } = useCurrentUserQuery({ staleTime: 60_000 });
  const canManage = getUserAccess(user).can_manage_properties;
  const leaseQuery = useLeaseQuery(id, { staleTime: 30_000 });
  const lease = leaseQuery.data;
  const [confirmEnd, setConfirmEnd] = useState(false);

  const action = useLeaseActionMutation({
    onSuccess: (data, variables) => {
      toast.success(variables.action === "activate" ? `${data.reference} is now active.` : `${data.reference} has ended.`);
      setConfirmEnd(false);
    },
    onError: (error) => toast.error(error.message || "Could not update the lease."),
  });

  if (leaseQuery.isLoading) {
    return (
      <div className="dwella-lease-detail" aria-busy="true">
        <span className="dwella-skeleton" style={{ height: 28, width: 220 }} />
        <span className="dwella-skeleton" style={{ height: 220, width: "100%" }} />
      </div>
    );
  }

  if (leaseQuery.isError || !lease) {
    return (
      <EmptyState
        icon={<DocumentText24Regular />}
        title="Lease not found"
        description="It may have been deleted, or it belongs to another workspace."
        actionLabel="Back to leases"
        onAction={() => window.history.back()}
      />
    );
  }

  const endsIn = daysUntil(lease.end_date);
  const canActivate = canManage && ["draft", "pending_signature"].includes(lease.status);
  const canEnd = canManage && lease.status === "active";

  return (
    <div className="dwella-lease-detail">
      <Link to="/leases" className="dwella-back-link"><ArrowLeft20Regular /> Leases</Link>

      <header className="dwella-detail-header">
        <div>
          <div className="dwella-detail-title">
            <h1>Lease {lease.reference}</h1>
            <StatusBadge {...leaseBadgeProps(lease.status)} />
          </div>
          <p>
            {lease.tenant_name} · {lease.unit_name}, {lease.property_name} · {formatDate(lease.start_date)} – {formatDate(lease.end_date)}
          </p>
        </div>
        <div className="dwella-detail-actions">
          <Button as={Link} to={`/tenants?search=${encodeURIComponent(lease.tenant_name)}`} icon={<Person20Regular />}>Tenant</Button>
          {canActivate ? (
            <Button appearance="primary" icon={<CheckmarkCircle20Regular />} disabled={action.isPending} onClick={() => action.mutate({ id: lease.id, action: "activate" })}>
              {action.isPending ? "Starting…" : "Start lease"}
            </Button>
          ) : null}
          {canEnd ? <Button disabled={action.isPending} onClick={() => setConfirmEnd(true)}>End lease</Button> : null}
        </div>
      </header>

      {lease.status === "active" && endsIn !== null && endsIn <= 60 ? (
        <p className="dwella-callout is-warning">{endsIn < 0 ? "The end date has passed. End the lease or extend it." : `Lease ends in ${endsIn} days.`}</p>
      ) : null}

      <div className="dwella-lease-grid">
        <section className="dwella-surface">
          <h3>Key terms</h3>
          <dl className="dwella-detail-list">
            <div><dt>Term</dt><dd>{formatDate(lease.start_date)} – {formatDate(lease.end_date)}</dd></div>
            <div><dt>Monthly rent</dt><dd>{formatMoney(lease.monthly_rent)}</dd></div>
            <div><dt>Due</dt><dd>Day {lease.rent_due_day} of each month</dd></div>
            <div><dt>Deposit</dt><dd>{formatMoney(lease.deposit_amount)}</dd></div>
            <div><dt>Late fee</dt><dd>{Number(lease.late_fee_percent) ? `${Number(lease.late_fee_percent)}% after ${lease.late_fee_grace_days} days` : "None"}</dd></div>
            <div><dt>Notice period</dt><dd>{lease.notice_period_months} {lease.notice_period_months === 1 ? "month" : "months"}</dd></div>
          </dl>
          {lease.notes ? <p className="dwella-muted-copy">{lease.notes}</p> : null}
        </section>
        <section className="dwella-surface">
          <h3>History</h3>
          <History lease={lease} />
        </section>
      </div>

      <Dialog open={confirmEnd} onOpenChange={(_, data) => !action.isPending && setConfirmEnd(data.open)}>
        <DialogSurface>
          <DialogBody>
            <DialogTitle>End lease {lease.reference}?</DialogTitle>
            <DialogContent>
              {lease.unit_name} at {lease.property_name} will be marked vacant, and {lease.tenant_name} becomes a past tenant unless they rent another unit. This cannot be undone.
            </DialogContent>
            <DialogActions>
              <Button disabled={action.isPending} onClick={() => setConfirmEnd(false)}>Keep lease</Button>
              <Button appearance="primary" disabled={action.isPending} onClick={() => action.mutate({ id: lease.id, action: "end" })}>
                {action.isPending ? "Ending…" : "End lease"}
              </Button>
            </DialogActions>
          </DialogBody>
        </DialogSurface>
      </Dialog>
    </div>
  );
}
