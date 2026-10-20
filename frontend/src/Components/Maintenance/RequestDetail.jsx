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
  Dropdown,
  Field,
  Input,
  Option,
  Switch,
  Textarea,
} from "@fluentui/react-components";
import { Camera20Regular, CheckmarkCircle20Regular, Play20Regular, Wrench24Regular } from "@fluentui/react-icons";
import { toast } from "react-toastify";

import { resolveMediaUrl } from "../../Services/apiClient";
import {
  useMaintenanceActionMutation,
  useMaintenancePhotoMutation,
  useMaintenanceUpdateMutation,
} from "../../Services/mutations";
import { useCurrentUserQuery, useMaintenanceRequestQuery, useVendorsQuery } from "../../Services/queries";
import { getUserAccess } from "../../shared/access";
import { EmptyState, StatusBadge } from "../../shared/components";
import { formatMoney, initials } from "../../shared/format";
import {
  ageLabel,
  categoryLabel,
  formatVisit,
  locationLabel,
  priorityBadgeProps,
  sourceLabel,
  statusBadgeProps,
  toLocalInput,
} from "../../shared/maintenance";
import { MAX_PHOTOS, PHOTO_TYPES, checkPhotos } from "./RequestDrawer";
import "../../shared/records.scss";
import "./maintenance.scss";

const steps = [
  { label: "Reported", reached: () => true },
  { label: "Assigned", reached: (r) => Boolean(r.vendor_id) || ["in_progress", "completed"].includes(r.status) },
  { label: "In progress", reached: (r) => ["in_progress", "completed"].includes(r.status) },
  { label: "Resolved", reached: (r) => r.status === "completed" },
];
const stamp = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
const cleanAmount = (value) => String(value ?? "").replace(/,/g, "").trim();
const isAmount = (value) => !cleanAmount(value) || /^\d+(\.\d{1,2})?$/.test(cleanAmount(value));

function Progress({ request }) {
  if (request.status === "cancelled") {
    return <p className="dwella-callout is-warning">This request was cancelled.</p>;
  }
  return (
    <ol className="dwella-progress" aria-label="Progress">
      {steps.map((step) => {
        const reached = step.reached(request);
        return (
          <li key={step.label} className={reached ? "is-reached" : undefined} aria-current={undefined}>
            <span aria-hidden="true" />
            {step.label}
            <span className="dwella-progress-state">{reached ? " (done)" : " (not yet)"}</span>
          </li>
        );
      })}
    </ol>
  );
}

function Photos({ request, canManage }) {
  const mutation = useMaintenancePhotoMutation();
  const [uploading, setUploading] = useState(false);
  const room = MAX_PHOTOS - request.photos.length;
  const add = async (event) => {
    const { accepted, problem } = checkPhotos(Array.from(event.target.files || []), room);
    event.target.value = "";
    if (problem) toast.error(problem);
    if (!accepted.length) return;
    setUploading(true);
    for (const file of accepted) {
      try {
        await mutation.mutateAsync({ id: request.id, file });
      } catch (error) {
        toast.error(error.data?.image?.[0] || error.message || "Could not upload the photo.");
      }
    }
    setUploading(false);
  };
  if (!request.photos.length && !canManage) return null;
  return (
    <div className="dwella-request-photos">
      {request.photos.map((photo, index) => (
        <a key={photo.id} href={resolveMediaUrl(photo.image)} target="_blank" rel="noreferrer">
          <img src={resolveMediaUrl(photo.image)} alt={`Photo ${index + 1} of ${request.title}`} loading="lazy" />
        </a>
      ))}
      {canManage && room > 0 ? (
        <label className={`dwella-photo-tile ${uploading ? "is-busy" : ""}`}>
          <Camera20Regular />
          {uploading ? "Uploading…" : "Add photo"}
          <input type="file" accept={PHOTO_TYPES.join(",")} multiple disabled={uploading} onChange={add} />
        </label>
      ) : null}
    </div>
  );
}

function Conversation({ request, canManage }) {
  const [body, setBody] = useState("");
  const [internal, setInternal] = useState(false);
  const mutation = useMaintenanceUpdateMutation({
    onSuccess: () => {
      setBody("");
      setInternal(false);
    },
    onError: (error) => toast.error(error.data?.body?.[0] || error.message || "Could not send."),
  });
  const send = (event) => {
    event.preventDefault();
    const text = body.trim();
    if (!text || mutation.isPending) return;
    mutation.mutate({ id: request.id, payload: { body: text, is_internal: internal } });
  };
  return (
    <section className="dwella-surface">
      <div>
        <h3>Conversation</h3>
        <p className="dwella-muted-copy">Replies are for the tenant; internal notes stay with your team.</p>
      </div>
      <ul className="dwella-thread">
        {request.updates.map((update) =>
          update.kind === "status" ? (
            <li key={update.id} className="is-status">
              <span>{update.body}</span>
              <small>{update.author_name ? `${update.author_name} · ` : ""}{stamp.format(new Date(update.created_at))}</small>
            </li>
          ) : (
            <li key={update.id} className={update.is_internal ? "is-internal" : undefined}>
              <span className="dwella-avatar is-navy" aria-hidden="true">{initials(update.author_name || "")}</span>
              <div>
                <p className="dwella-thread-meta">
                  <strong>{update.author_name || "Someone"}</strong>
                  <small>{stamp.format(new Date(update.created_at))}</small>
                  {update.is_internal ? <StatusBadge color="warning">Internal note</StatusBadge> : null}
                </p>
                <p className="dwella-thread-body">{update.body}</p>
              </div>
            </li>
          ),
        )}
      </ul>
      {canManage ? (
        <form className="dwella-reply" onSubmit={send}>
          <Textarea
            aria-label={internal ? "Write an internal note" : "Write a reply"}
            placeholder={internal ? "Write an internal note…" : "Write a reply…"}
            rows={2}
            maxLength={2000}
            value={body}
            onChange={(_, d) => setBody(d.value)}
          />
          <div className="dwella-reply-actions">
            <Switch checked={internal} onChange={(_, d) => setInternal(d.checked)} label="Internal note" />
            <Button appearance="primary" type="submit" disabled={!body.trim() || mutation.isPending}>
              {mutation.isPending ? "Sending…" : internal ? "Add note" : "Send"}
            </Button>
          </div>
        </form>
      ) : null}
    </section>
  );
}

function AssignPanel({ request }) {
  const vendorsQuery = useVendorsQuery({ page_size: 200, is_active: "true", ordering: "name" }, { staleTime: 60_000 });
  const vendors = vendorsQuery.data?.results || [];
  const [form, setForm] = useState({
    vendor: request.vendor_id || "",
    scheduled_for: toLocalInput(request.scheduled_for),
    estimated_cost: request.estimated_cost || "",
    charge_to_tenant: request.charge_to_tenant,
  });
  const [errors, setErrors] = useState({});
  const mutation = useMaintenanceActionMutation({
    onSuccess: (data) => toast.success(`Assigned to ${data.vendor_name}.`),
    onError: (error) => {
      if (error.data && typeof error.data === "object") setErrors(error.data);
      toast.error(error.message || "Could not assign the request.");
    },
  });
  const update = (key, value) => {
    setForm((current) => ({ ...current, [key]: value }));
    setErrors((current) => ({ ...current, [key]: undefined }));
  };
  const submit = (event) => {
    event.preventDefault();
    const found = {};
    if (!form.vendor) found.vendor = ["Choose a vendor."];
    if (!isAmount(form.estimated_cost)) found.estimated_cost = ["Enter an amount like 350.00."];
    setErrors(found);
    if (Object.keys(found).length) return;
    mutation.mutate({
      id: request.id,
      action: "assign",
      payload: {
        vendor: form.vendor,
        scheduled_for: form.scheduled_for ? new Date(form.scheduled_for).toISOString() : null,
        estimated_cost: cleanAmount(form.estimated_cost) || null,
        charge_to_tenant: form.charge_to_tenant,
      },
    });
  };
  const field = (key) => (errors[key] ? { validationState: "error", validationMessage: errors[key][0] } : {});
  const vendor = vendors.find((item) => item.id === form.vendor);
  return (
    <section className="dwella-surface">
      <h3>Assign and schedule</h3>
      <form noValidate className="dwella-assign-form" onSubmit={submit}>
        <fieldset disabled={mutation.isPending}>
          <Field label="Vendor" required {...field("vendor")} hint={!vendorsQuery.isLoading && !vendors.length ? "Add vendors from the Maintenance page first." : undefined}>
            <Dropdown
              placeholder={vendorsQuery.isLoading ? "Loading…" : "Choose a vendor"}
              value={vendor?.name || ""}
              selectedOptions={form.vendor ? [form.vendor] : []}
              onOptionSelect={(_, d) => update("vendor", d.optionValue)}
            >
              {vendors.map((item) => <Option key={item.id} value={item.id} text={item.name}>{item.name}{item.trade ? ` · ${item.trade}` : ""}</Option>)}
            </Dropdown>
          </Field>
          <Field label="Visit" {...field("scheduled_for")}>
            <Input type="datetime-local" value={form.scheduled_for} onChange={(_, d) => update("scheduled_for", d.value)} />
          </Field>
          <Field label="Estimated cost (ZMW)" {...field("estimated_cost")}>
            <Input inputMode="decimal" placeholder="0.00" value={form.estimated_cost} onChange={(_, d) => update("estimated_cost", d.value)} />
          </Field>
          <div className="dwella-option-split">
            <div>
              <strong>Charge to tenant</strong>
              <small>{request.tenant_name ? `Bills ${request.tenant_name} when the job is done.` : "Needs a tenant on the request."}</small>
            </div>
            <Switch
              aria-label="Charge to tenant"
              disabled={!request.tenant_name}
              checked={form.charge_to_tenant}
              onChange={(_, d) => update("charge_to_tenant", d.checked)}
            />
          </div>
          {errors.charge_to_tenant ? <p className="dwella-field-error">{errors.charge_to_tenant[0]}</p> : null}
          <Button appearance="primary" type="submit">
            {mutation.isPending ? "Saving…" : request.vendor_id ? "Update assignment" : "Assign"}
          </Button>
        </fieldset>
      </form>
    </section>
  );
}

function CloseDialog({ request, mode, onClose }) {
  const [value, setValue] = useState(mode === "complete" ? request.actual_cost || request.estimated_cost || "" : "");
  const [error, setError] = useState("");
  const mutation = useMaintenanceActionMutation({
    onSuccess: (data) => {
      toast.success(mode === "complete" ? (data.invoice_reference ? `Done. ${data.invoice_reference} issued to the tenant.` : "Marked as done.") : "Request cancelled.");
      onClose();
    },
    onError: (err) => toast.error(err.message || "Could not update the request."),
  });
  const submit = () => {
    if (mode === "complete" && !isAmount(value)) {
      setError("Enter an amount like 420.00.");
      return;
    }
    mutation.mutate({
      id: request.id,
      action: mode,
      payload: mode === "complete" ? { actual_cost: cleanAmount(value) || null } : { reason: value.trim() },
    });
  };
  const charging = mode === "complete" && request.charge_to_tenant && request.tenant_name;
  return (
    <Dialog open onOpenChange={(_, data) => !data.open && !mutation.isPending && onClose()}>
      <DialogSurface>
        <DialogBody>
          <DialogTitle>{mode === "complete" ? "Mark as done" : `Cancel ${request.reference}?`}</DialogTitle>
          <DialogContent className="dwella-dialog-copy">
            {mode === "complete" ? (
              <>
                <p>{charging ? `${request.tenant_name} will be invoiced for the final cost, due in 14 days.` : "Record what the job finally cost."}</p>
                <Field label="Final cost (ZMW)" validationState={error ? "error" : "none"} validationMessage={error}>
                  <Input inputMode="decimal" placeholder="0.00" value={value} onChange={(_, d) => { setValue(d.value); setError(""); }} />
                </Field>
              </>
            ) : (
              <>
                <p>The request is closed without the work being done. It stays on record.</p>
                <Field label="Reason (optional)">
                  <Input maxLength={300} value={value} onChange={(_, d) => setValue(d.value)} />
                </Field>
              </>
            )}
          </DialogContent>
          <DialogActions>
            <Button disabled={mutation.isPending} onClick={onClose}>{mode === "complete" ? "Not yet" : "Keep request"}</Button>
            <Button appearance="primary" disabled={mutation.isPending} onClick={submit}>
              {mutation.isPending ? "Saving…" : mode === "complete" ? "Mark as done" : "Cancel request"}
            </Button>
          </DialogActions>
        </DialogBody>
      </DialogSurface>
    </Dialog>
  );
}

export default function RequestDetail() {
  const { id } = useParams();
  const { data: user } = useCurrentUserQuery({ staleTime: 60_000 });
  const canManage = getUserAccess(user).can_manage_properties;
  const requestQuery = useMaintenanceRequestQuery(id, { staleTime: 15_000 });
  const request = requestQuery.data;
  const [dialog, setDialog] = useState(null); // null | "complete" | "cancel"
  const start = useMaintenanceActionMutation({
    onSuccess: () => toast.success("Work started."),
    onError: (error) => toast.error(error.message || "Could not start the work."),
  });

  if (requestQuery.isLoading) {
    return (
      <div className="dwella-request-detail" aria-busy="true">
        <span className="dwella-skeleton" style={{ height: 28, width: 240 }} />
        <span className="dwella-skeleton" style={{ height: 320, width: "100%" }} />
      </div>
    );
  }
  if (requestQuery.isError || !request) {
    return (
      <EmptyState
        icon={<Wrench24Regular />}
        title="Request not found"
        description="It may belong to another workspace."
        actionLabel="Back to maintenance"
        onAction={() => window.history.back()}
      />
    );
  }

  const isOpen = ["new", "scheduled", "in_progress"].includes(request.status);
  const reporter = request.tenant_name || request.reported_by_name || sourceLabel(request.source);

  return (
    <div className="dwella-request-detail">
      <header className="dwella-detail-header">
        <div>
          <div className="dwella-detail-title">
            <h1>{request.title}</h1>
            <StatusBadge {...statusBadgeProps(request.status)} />
            <StatusBadge color="subtle">{categoryLabel(request.category)}</StatusBadge>
          </div>
          <p>{request.reference} · {locationLabel(request)} · reported {ageLabel(request.created_at).toLowerCase()}</p>
        </div>
        {canManage && isOpen ? (
          <div className="dwella-detail-actions">
            <Button onClick={() => setDialog("cancel")}>Cancel request</Button>
            {request.status !== "in_progress" ? (
              <Button icon={<Play20Regular />} disabled={start.isPending} onClick={() => start.mutate({ id: request.id, action: "start" })}>
                {start.isPending ? "Starting…" : "Start work"}
              </Button>
            ) : null}
            <Button appearance="primary" icon={<CheckmarkCircle20Regular />} onClick={() => setDialog("complete")}>Mark as done</Button>
          </div>
        ) : null}
      </header>

      <div className="dwella-request-grid">
        <div className="dwella-request-main">
          <section className="dwella-surface">
            <div>
              <h3>Progress</h3>
              <p className="dwella-muted-copy">Every change is logged in the conversation below.</p>
            </div>
            <Progress request={request} />
          </section>

          <section className="dwella-surface">
            <div className="dwella-who">
              <span className="dwella-avatar is-green" aria-hidden="true">{initials(reporter)}</span>
              <span>
                <strong>{reporter}</strong>
                <small>{sourceLabel(request.source)}{request.unit_name ? ` · Unit ${request.unit_name}` : ""} · {stamp.format(new Date(request.created_at))}</small>
              </span>
            </div>
            <p className="dwella-request-description">{request.description || "No details were given."}</p>
            <Photos request={request} canManage={canManage && isOpen} />
          </section>

          <Conversation request={request} canManage={canManage} />
        </div>

        <aside className="dwella-request-rail">
          <section className="dwella-surface">
            <h3>Details</h3>
            <dl className="dwella-detail-list">
              <div><dt>Priority</dt><dd><StatusBadge {...priorityBadgeProps(request.priority)} /></dd></div>
              <div><dt>Category</dt><dd>{categoryLabel(request.category)}</dd></div>
              <div><dt>Where</dt><dd>{locationLabel(request)}</dd></div>
              {request.tenant_name ? <div><dt>Tenant</dt><dd>{request.tenant_name}</dd></div> : null}
              <div><dt>Access</dt><dd>{request.access_notes || "—"}</dd></div>
              <div><dt>Permission to enter</dt><dd>{request.permission_to_enter ? "Yes" : "No"}</dd></div>
            </dl>
          </section>

          {canManage && isOpen ? (
            <AssignPanel key={`${request.vendor_id}-${request.scheduled_for}-${request.estimated_cost}`} request={request} />
          ) : (
            <section className="dwella-surface">
              <h3>Work</h3>
              <dl className="dwella-detail-list">
                <div><dt>Vendor</dt><dd>{request.vendor_name || "—"}</dd></div>
                <div><dt>Visit</dt><dd>{formatVisit(request.scheduled_for)}</dd></div>
                <div><dt>Estimate</dt><dd>{request.estimated_cost ? formatMoney(request.estimated_cost) : "—"}</dd></div>
                <div><dt>Final cost</dt><dd>{request.actual_cost ? formatMoney(request.actual_cost) : "—"}</dd></div>
                {request.invoice_id ? (
                  <div><dt>Charged on</dt><dd><Link to={`/billing/invoices/${request.invoice_id}`}>{request.invoice_reference}</Link></dd></div>
                ) : null}
              </dl>
            </section>
          )}
        </aside>
      </div>

      {dialog ? <CloseDialog request={request} mode={dialog} onClose={() => setDialog(null)} /> : null}
    </div>
  );
}
