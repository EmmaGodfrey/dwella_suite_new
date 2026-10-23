import React, { useState } from "react";
import { Button, Field, Textarea } from "@fluentui/react-components";
import { toast } from "react-toastify";
import { useOutreachList, useOutreachMutation } from "../../Services/outreach";
import { AdminHeader, AdminState } from "../Platform/AdminUI";
import {
  ActionButton,
  EarlyAccessDialog,
  ErrorText,
  OutreachStatus,
  OutreachTabs,
} from "./OutreachUI";
import "./outreach.scss";

const reviewError = (errors) => {
  if (errors?.missing_fields)
    return `Missing ${errors.missing_fields.map((field) => field.replaceAll("_", " ")).join(", ")}. Update the contact or outreach settings, then refresh the preview.`;
  if (Array.isArray(errors)) return errors.join(" ");
  if (errors && typeof errors === "object")
    return Object.entries(errors)
      .map(
        ([key, value]) =>
          `${key.replaceAll("_", " ")}: ${Array.isArray(value) ? value.join(" ") : value}`,
      )
      .join(" ");
  return String(errors || "Refresh this preview before approving.");
};

export default function ReviewQueue() {
  const [page, setPage] = useState(1);
  const query = useOutreachList("enrollments", {
    status: "pending_review",
    page,
    page_size: 30,
  });
  const settings = useOutreachList("settings");
  const [selected, setSelected] = useState(null);
  const [draft, setDraft] = useState(null);
  const [early, setEarly] = useState(false);
  const mutation = useOutreachMutation();
  const entry =
    query.data?.results.find((e) => e.id === selected) ||
    query.data?.results[0];
  const changed = draft !== null && draft !== entry?.personal_line;
  const ready = query.data?.results.filter((e) => e.review?.ready) || [];
  const approve = async (ids) => {
    const entries = query.data.results.filter((e) => ids.includes(e.id));
    await mutation.mutateAsync({
      resource: "enrollments",
      action: "approve-many",
      body: {
        ids,
        tokens: Object.fromEntries(
          entries.map((e) => [e.id, e.review.preview_token]),
        ),
      },
    });
    setDraft(null);
    toast.success("Approved. Messages will use the configured sending window.");
  };
  return (
    <div className="admin-screen outreach-screen">
      <AdminHeader
        title="Review queue"
        description="Check each rendered first email. Follow-ups stop on reply or opt-out."
      >
        <ActionButton
          appearance="primary"
          busy={mutation.isPending || !ready.length || changed}
          onClick={() => approve(ready.map((e) => e.id))}
        >
          Approve ready on this page ({ready.length})
        </ActionButton>
      </AdminHeader>
      <OutreachTabs />
      <AdminState
        query={query}
        empty={!query.data?.results.length}
        title="No emails awaiting review"
      >
        <div className="outreach-review-grid">
          <section className="admin-card outreach-review-list">
            <h2>{query.data?.pagination.count} awaiting approval</h2>
            {query.data?.results.map((e) => (
              <button
                key={e.id}
                type="button"
                className={e.id === entry?.id ? "is-selected" : ""}
                onClick={() => {
                  setSelected(e.id);
                  setDraft(null);
                }}
              >
                <strong>{e.contact_name}</strong>
                <OutreachStatus value={e.review?.ready ? "ready" : "blocked"} />
                <span className="admin-note">{e.sequence_name}</span>
              </button>
            ))}
            <div className="admin-card-actions">
              <Button
                disabled={!query.data?.pagination.previous}
                onClick={() => setPage(page - 1)}
              >
                Previous
              </Button>
              <Button
                disabled={!query.data?.pagination.next}
                onClick={() => setPage(page + 1)}
              >
                Next
              </Button>
            </div>
          </section>
          <section className="admin-card outreach-preview" key={entry?.id}>
            <h2>
              {entry?.contact_name} · {entry?.contact_email}
            </h2>
            {entry?.review?.ready ? (
              <>
                <OutreachStatus value="ready" />
                {entry.review.messages.map((m, i) => (
                  <details key={m.step} open={i === 0}>
                    <summary>
                      {i === 0
                        ? "First email"
                        : `Follow-up ${i} · ${m.wait_days} days after previous step`}
                    </summary>
                    <h3>{m.subject}</h3>
                    <pre>{m.body}</pre>
                    <p className="admin-note">
                      An opt-out link is appended to every sent message.
                    </p>
                  </details>
                ))}
              </>
            ) : (
              <div role="alert" className="admin-error">
                Cannot approve: {reviewError(entry?.review?.errors)}
              </div>
            )}
            <Field label="Personal opening line">
              <Textarea
                value={draft ?? entry?.personal_line ?? ""}
                maxLength={1000}
                onChange={(_, d) => setDraft(d.value)}
              />
            </Field>
            <div className="admin-card-actions">
              <ActionButton
                busy={mutation.isPending || !changed}
                onClick={async () => {
                  await mutation.mutateAsync({
                    resource: "enrollments",
                    id: entry.id,
                    method: "patch",
                    body: { personal_line: draft },
                  });
                  setDraft(null);
                }}
              >
                Save & preview opening line
              </ActionButton>
              <ActionButton
                busy={mutation.isPending}
                onClick={() =>
                  mutation.mutateAsync({
                    resource: "enrollments",
                    id: entry.id,
                    action: "state",
                    body: { action: "stop" },
                  })
                }
              >
                Remove
              </ActionButton>
              <Button
                disabled={mutation.isPending}
                onClick={() => setEarly(true)}
              >
                Give early access
              </Button>
              <ActionButton
                appearance="primary"
                busy={mutation.isPending || !entry?.review?.ready || changed}
                onClick={() => approve([entry.id])}
              >
                Approve email
              </ActionButton>
            </div>
            <ErrorText error={mutation.error} />
            <p className="admin-note">
              {settings.data?.enabled && !settings.data?.paused
                ? "After approval: next eligible weekday window."
                : "Sending is disabled or paused. Approval saves the message; it will not send yet."}{" "}
              {settings.data?.send_from_hour}:00–
              {settings.data?.send_until_hour}:00 Lusaka · Daily cap{" "}
              {settings.data?.daily_cap}
            </p>
          </section>
        </div>
      </AdminState>
      {early && entry && (
        <EarlyAccessDialog
          contact={{
            id: entry.contact,
            name: entry.contact_name,
            email: entry.contact_email,
          }}
          onClose={() => setEarly(false)}
        />
      )}
    </div>
  );
}
