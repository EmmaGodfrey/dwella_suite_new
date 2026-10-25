import React, { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  Button,
  Dialog,
  DialogActions,
  DialogBody,
  DialogContent,
  DialogSurface,
  DialogTitle,
} from "@fluentui/react-components";
import { ArrowRepeatAll20Regular, CheckmarkCircle20Regular, DocumentText24Regular, Person20Regular } from "@fluentui/react-icons";
import { toast } from "react-toastify";

import { useLeaseActionMutation } from "../../Services/mutations";
import { useCurrentUserQuery, useLeaseQuery } from "../../Services/queries";
import { getUserAccess } from "../../shared/access";
import { EmptyState, StatusBadge } from "../../shared/components";
import { daysUntil, formatDate, formatMoney } from "../../shared/format";
import { leaseBadgeProps } from "../../shared/tenancy";
import "../../shared/records.scss";
import "./leases.scss";
import LeaseDocuments from "../Documents/LeaseDocuments";
import RenewLeaseDrawer from "./RenewLeaseDrawer";

function History({ lease }) {
  const events = [
    { label: "Lease created", when: lease.created_at, done: true },
    lease.activated_at ? { label: "Started — unit marked occupied", when: lease.activated_at, done: true } : null,
    lease.ended_at ? { label: "Ended — unit marked vacant", when: lease.ended_at, done: true } : null,
    !lease.activated_at && lease.status !== "ended"
      ? {
          label: "Waiting to start",
          when: null,
          done: false,
          // A renewal starts by itself on its start date once signed.
          note: lease.renewal_of_id
            ? `Starts on ${formatDate(lease.start_date)} once signed.`
            : "Start the lease when the tenant moves in.",
        }
      : null,
  ].filter(Boolean);

  return (
    <ol className="dwella-timeline">
      {events.map((event) => (
        <li key={event.label} className={event.done ? "is-done" : "is-pending"}>
          <strong>{event.label}</strong>
          <small>{event.when ? formatDate(event.when) : event.note}</small>
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
  const [renewing, setRenewing] = useState(false);
  const navigate = useNavigate();

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
  // The API refuses to start a renewal before its start date.
  const canActivate =
    canManage && ["draft", "pending_signature"].includes(lease.status) && !(lease.renewal_of_id && daysUntil(lease.start_date) > 0);
  const canEnd = canManage && lease.status === "active";
  const canRenew = canEnd && !lease.renewal;
  const renewal = lease.renewal;

  return (
    <div className="dwella-lease-detail">

      <header className="dwella-detail-header">
        <div>
          <div className="dwella-detail-title">
            <h1>Lease {lease.reference}</h1>
            <StatusBadge {...leaseBadgeProps(lease.status)} />
          </div>
          <p>
            {lease.tenant_name} · {lease.unit_name}, {lease.property_name} · {formatDate(lease.start_date)} – {formatDate(lease.end_date)}
            {lease.renewal_of_id ? <> · Renews <Link to={`/leases/${lease.renewal_of_id}`}>{lease.renewal_of_reference}</Link></> : null}
          </p>
        </div>
        <div className="dwella-detail-actions">
          <Button as={Link} to={`/tenants?search=${encodeURIComponent(lease.tenant_name)}`} icon={<Person20Regular />}>Tenant</Button>
          {canActivate ? (
            <Button appearance="primary" icon={<CheckmarkCircle20Regular />} disabled={action.isPending} onClick={() => action.mutate({ id: lease.id, action: "activate" })}>
              {action.isPending ? "Starting…" : "Start lease"}
            </Button>
          ) : null}
          {canRenew ? <Button icon={<ArrowRepeatAll20Regular />} disabled={action.isPending} onClick={() => setRenewing(true)}>Renew lease</Button> : null}
          {canEnd ? <Button disabled={action.isPending} onClick={() => setConfirmEnd(true)}>End lease</Button> : null}
        </div>
      </header>

      {renewal ? (
        <section className="dwella-callout is-info dwella-renewal-callout" aria-label="Renewal">
          <div>
            <strong>Renewal {renewal.reference}</strong> <StatusBadge {...leaseBadgeProps(renewal.status)} />
            <p>
              {formatDate(renewal.start_date)} – {formatDate(renewal.end_date)}.{" "}
              {renewal.status === "draft"
                ? `Prepare the agreement and send it to ${lease.tenant_name} for signing. Once signed, it starts on ${formatDate(renewal.start_date)} by itself.`
                : renewal.status === "pending_signature"
                  ? `Waiting for signatures. Once signed, it starts on ${formatDate(renewal.start_date)} by itself.`
                  : `Running since ${formatDate(renewal.start_date)}.`}
            </p>
          </div>
          <Button as={Link} to={`/leases/${renewal.id}`}>Open renewal</Button>
        </section>
      ) : null}

      {lease.status === "active" && !renewal && endsIn !== null && endsIn <= 60 ? (
        <p className="dwella-callout is-warning">{endsIn < 0 ? "The end date has passed. End the lease or renew it." : `Lease ends in ${endsIn} days.`}</p>
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

      <LeaseDocuments lease={lease} canManage={canManage} />

      {renewing ? (
        <RenewLeaseDrawer
          lease={lease}
          onClose={() => setRenewing(false)}
          onSaved={(data) => {
            setRenewing(false);
            navigate(`/leases/${data.id}`);
          }}
        />
      ) : null}

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
