import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Button, Checkbox, Field, Input, Select, Textarea } from "@fluentui/react-components";
import { toast } from "react-toastify";
import { useCurrentUserQuery } from "../../Services/queries";
import { useMessageAction, useMessageDetail, useMessageHistory, useMessageRecipients } from "../../Services/messages";
import { getUserAccess } from "../../shared/access";
import { EmptyState, StatusBadge } from "../../shared/components";
import { FormDrawer } from "../../shared/components/FormFlow";
import { AdminHeader, AdminState, AdminTable, when } from "../Platform/AdminUI";
import "./messages.scss";

const channelNames = { email: "Email", sms: "SMS", whatsapp: "WhatsApp" };
const statusNames = { held: "Held", queued: "Queued", sending: "Sending", sent: "Accepted by provider", delivered: "Delivered", read: "Read", failed: "Failed", cancelled: "Cancelled", review: "Needs review" };
const reasonLabel = (reason) => ({ delivery_not_connected: "Delivery is not connected", send_outcome_unknown: "Send outcome needs review", recipient_opted_out: "Recipient opted out", invoice_no_longer_due: "Invoice paid, cancelled or reminder expired", permission_removed: "Access no longer available", missing_contact: "No contact for this channel", smtp_accepted: "Accepted by email server; delivery unconfirmed" }[reason] || reason?.replaceAll("_", " ") || "—");

export default function Messages() {
  const user = useCurrentUserQuery();
  const access = getUserAccess(user.data);
  const platform = access.persona === "platform_admin";
  const [filters, setFilters] = useState({ page: 1, channel: "", status: "", search: "" });
  const [compose, setCompose] = useState(false);
  const [detail, setDetail] = useState(null);
  const query = useMessageHistory(filters, platform);
  const update = (key, value) => setFilters((v) => ({ ...v, [key]: value, page: 1 }));
  return <div className="messages-page">
    <AdminHeader title="Messages" description="Send notices and track individual delivery requests.">
      <Button as={Link} to={platform ? "/settings?tab=messaging" : "/settings?tab=notifications"}>Reminder settings</Button>
      {!platform && <Button appearance="primary" onClick={() => setCompose(true)}>New message</Button>}
    </AdminHeader>
    <p className="settings-note">A held request has not been sent. Provider acceptance does not confirm delivery; delivery reports update the status when available.</p>
    <div className="messages-filters">
      <Field label="Search"><Input value={filters.search} onChange={(_, d) => update("search", d.value)} /></Field>
      <Field label="Channel"><Select value={filters.channel} onChange={(_, d) => update("channel", d.value)}><option value="">All channels</option>{Object.entries(channelNames).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</Select></Field>
      <Field label="Status"><Select value={filters.status} onChange={(_, d) => update("status", d.value)}><option value="">All statuses</option>{Object.entries(statusNames).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</Select></Field>
      <Button onClick={() => query.refetch()}>Refresh</Button>
    </div>
    <AdminState query={query}>
      {!query.data?.results?.length ? <EmptyState title="No messages yet" description="Your confirmed notices and scheduled reminders will appear here." /> : <AdminTable
        rows={query.data.results} pagination={query.data.pagination} setPage={(page) => setFilters((v) => ({ ...v, page }))}
        columns={[
          { key: "subject", label: "Notice", render: (row) => platform ? row.subject : <Button appearance="transparent" onClick={() => setDetail(row.id)}>{row.subject}</Button> },
          { key: "tenant_name", label: "Recipient" },
          ...(platform ? [{ key: "workspace_name", label: "Workspace" }] : []),
          { key: "channel", label: "Channel", render: (row) => channelNames[row.channel] },
          { key: "status", label: "Status", render: (row) => <StatusBadge color={row.status === "held" || row.status === "review" ? "warning" : "subtle"}>{statusNames[row.status]}</StatusBadge> },
          { key: "reason", label: "Details", render: (row) => <>
            {reasonLabel(row.reason)}{row.failure_code && ` (${row.failure_code})`}
          </> },
          { key: "created_at", label: "Requested", render: (row) => when(row.created_at) },
        ]} />}
    </AdminState>
    {compose && <Compose onClose={() => setCompose(false)} />}
    {detail && <MessageDetail id={detail} onClose={() => setDetail(null)} />}
  </div>;
}

function Compose({ onClose }) {
  const [draft, setDraft] = useState({ channel: "email", subject: "", body: "" });
  const [everyone, setEveryone] = useState(false);
  const [selected, setSelected] = useState({});
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [review, setReview] = useState(null);
  const [error, setError] = useState("");
  const recipients = useMessageRecipients(search, page);
  const preview = useMessageAction("preview");
  const confirm = useMessageAction("confirm");
  const busy = preview.isPending || confirm.isPending;
  const ids = Object.keys(selected);
  const change = (key, value) => {
    setDraft((v) => ({ ...v, [key]: value }));
    setError("");
  };
  const toggle = (id, name, checked) =>
    setSelected((v) => {
      const next = { ...v };
      if (checked) next[id] = name;
      else delete next[id];
      return next;
    });
  const submit = async (event) => {
    event.preventDefault();
    if (busy) return;
    const chosen = everyone || (ids.length > 0 && ids.length <= 100);
    if (!review && (!chosen || !draft.subject.trim() || /[\r\n]/.test(draft.subject) || !draft.body.trim())) {
      setError("Choose recipients and enter a subject and message.");
      return;
    }
    try {
      if (!review) {
        setReview(await preview.mutateAsync({ ...draft, tenants: everyone ? [] : ids, all_tenants: everyone }));
      } else {
        const result = await confirm.mutateAsync({ id: review.id, confirmed: true });
        toast.info(result.delivery_note);
        onClose();
      }
    } catch (e) {
      setError(e.message || "Could not save this request. Please try again.");
    }
  };
  const contact = (r) => (draft.channel === "email" ? r.email || "No email" : r.phone_number);
  return (
    <FormDrawer
      title={review ? "Review message" : "New message"}
      steps={["Message", "Review"]}
      step={review ? 1 : 0}
      onSubmit={submit}
      onBack={() => { setReview(null); setError(""); }}
      onClose={onClose}
      busy={busy}
      submitLabel="Confirm request"
      pendingLabel="Saving…"
      notice={error && <p className="dwella-alert danger" role="alert">{error}</p>}
    >
      {review ? (
        <>
          <p>
            {channelNames[review.channel]} · {review.recipients.length}{" "}
            {review.recipients.length === 1 ? "recipient" : "recipients"}
          </p>
          {review.skipped > 0 && (
            <p className="dwella-alert" role="status">
              {review.skipped} {review.skipped === 1 ? "tenant has" : "tenants have"} no contact for this
              channel and will not receive it.
            </p>
          )}
          <ul className="message-recipient-review">
            {review.recipients.map((r) => (
              <li key={r.id}><strong>{r.name}</strong><span>{r.address}</span></li>
            ))}
          </ul>
          <h3>{review.subject}</h3>
          <p className="message-body">{review.body}</p>
          <p className="dwella-alert" role="status">{review.delivery_note}</p>
          <p>Preview expires {when(review.expires_at)}. Confirming records one request for each recipient.</p>
        </>
      ) : (
        <>
          <Field label="Channel">
            <Select value={draft.channel} onChange={(_, d) => change("channel", d.value)}>
              {Object.entries(channelNames).map(([key, label]) => <option key={key} value={key}>{label}</option>)}
            </Select>
          </Field>
          <Checkbox
            label="Send to all active tenants"
            checked={everyone}
            onChange={(_, d) => { setEveryone(Boolean(d.checked)); setError(""); }}
          />
          {!everyone && (
            <>
              <Field label="Find tenants">
                <Input value={search} maxLength={100} onChange={(_, d) => { setSearch(d.value); setPage(1); }} />
              </Field>
              <p>{ids.length}/100 selected. Search to find more tenants.</p>
              {ids.length > 0 && (
                <div className="message-selected">
                  {Object.entries(selected).map(([id, name]) => (
                    <Button key={id} size="small" onClick={() => toggle(id, name, false)}>{name} ×</Button>
                  ))}
                </div>
              )}
              <AdminState query={recipients}>
                <div className="message-recipient-list">
                  {recipients.data?.results?.map((r) => (
                    <Checkbox
                      key={r.id}
                      label={`${r.full_name} · ${contact(r)}`}
                      checked={Boolean(selected[r.id])}
                      disabled={!selected[r.id] && ids.length >= 100}
                      onChange={(_, d) => toggle(r.id, r.full_name, d.checked)}
                    />
                  ))}
                  {recipients.data?.results?.length === 0 && <p>No matching tenants.</p>}
                </div>
              </AdminState>
              {recipients.data?.pagination && (
                <div className="dwella-table-pager">
                  <Button disabled={!recipients.data.pagination.previous} onClick={() => setPage((p) => p - 1)}>Previous recipients</Button>
                  <Button disabled={!recipients.data.pagination.next} onClick={() => setPage((p) => p + 1)}>More recipients</Button>
                </div>
              )}
            </>
          )}
          <Field label="Subject" required>
            <Input value={draft.subject} maxLength={160} onChange={(_, d) => change("subject", d.value)} />
          </Field>
          <Field label="Message" required>
            <Textarea rows={6} value={draft.body} maxLength={2000} onChange={(_, d) => change("body", d.value)} />
          </Field>
          <p>
            {draft.body.length}/2,000 characters. Long SMS notices may use multiple segments. WhatsApp
            requires consent and an approved template before delivery.
          </p>
        </>
      )}
    </FormDrawer>
  );
}

function MessageDetail({ id, onClose }) {
  const query = useMessageDetail(id);
  const cancel = useMessageAction("cancel");
  const [error, setError] = useState("");
  return <FormDrawer title="Message request" onClose={onClose} submitLabel="Close" onSubmit={(e) => { e.preventDefault(); onClose(); }}>
    <AdminState query={query}>{query.data && <>
      <h3>{query.data.subject}</h3><p>{query.data.tenant_name} · {query.data.recipient}</p>
      <StatusBadge color="subtle">{statusNames[query.data.status]}</StatusBadge>
      <p>{reasonLabel(query.data.reason)}</p><p className="message-body">{query.data.body}</p>
      {query.data.provider && <p>Provider: {query.data.provider}</p>}
      {query.data.delivered_at && <p>Delivered: {when(query.data.delivered_at)}</p>}
      {query.data.read_at && <p>Read: {when(query.data.read_at)}</p>}
      {query.data.failure_code && <p role="alert">Failure code: {query.data.failure_code}</p>}
      {["held", "queued"].includes(query.data.status) && <Button disabled={cancel.isPending} onClick={async () => { try { await cancel.mutateAsync({ id, confirmed: true }); toast.info("Request cancelled."); onClose(); } catch (e) { setError(e.message); } }}>Cancel this request</Button>}
      {error && <p role="alert">{error}</p>}
    </>}</AdminState>
  </FormDrawer>;
}
