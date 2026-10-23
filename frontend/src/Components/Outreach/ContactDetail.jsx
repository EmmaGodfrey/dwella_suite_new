import React, { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Button, Field, Select } from "@fluentui/react-components";
import { toast } from "react-toastify";
import {
  useOutreachChoices,
  useOutreachDetail,
  useOutreachList,
  useOutreachMutation,
} from "../../Services/outreach";
import {
  AdminHeader,
  AdminState,
  ConfirmAction,
  when,
} from "../Platform/AdminUI";
import {
  ActionButton,
  ContactDrawer,
  EarlyAccessDialog,
  EnrollmentDrawer,
  OutreachStatus,
  OutreachTabs,
} from "./OutreachUI";
import "./outreach.scss";

export default function ContactDetail() {
  const { id } = useParams();
  const query = useOutreachDetail("contacts", id);
  const contact = query.data;
  const [dialog, setDialog] = useState(null);
  const [page, setPage] = useState(1);
  const [template, setTemplate] = useState("");
  const messages = useOutreachList("messages", {
    enrollment__contact__public_id: id,
    page,
  });
  const activity = useOutreachList(`contacts/${id}/activity`);
  const enrollments = useOutreachList("enrollments", {
    contact__public_id: id,
  });
  const sequences = useOutreachChoices("sequences", { active: true });
  const templates = useOutreachChoices("templates", { active: true });
  const mutation = useOutreachMutation();
  const updateStatus = async (status) => {
    await mutation.mutateAsync({
      resource: "contacts",
      id,
      action: "status",
      body: { status },
    });
    toast.success("Contact updated.");
  };
  return (
    <div className="admin-screen outreach-screen">
      <Link to="/admin/outreach">← Contacts</Link>
      <OutreachTabs />
      <AdminState query={query}>
        <AdminHeader
          title={contact?.name}
          description={[contact?.organization, contact?.email, contact?.town]
            .filter(Boolean)
            .join(" · ")}
          badge={<OutreachStatus value={contact?.status || "new"} />}
        >
          <Button onClick={() => setDialog("edit")}>Edit contact</Button>
          <Button
            disabled={contact?.suppressed || !contact?.email}
            appearance="primary"
            onClick={() => setDialog("early")}
          >
            Give early access
          </Button>
        </AdminHeader>
        <div className="outreach-detail-grid">
          <div className="admin-stack">
            <section className="admin-card">
              <h2>Email history</h2>
              <AdminState
                query={messages}
                empty={!messages.data?.results.length}
                title="No approved or sent emails yet"
              >
                {messages.data?.results.map((m) => (
                  <details className="outreach-message" key={m.id}>
                    <summary>
                      {m.subject} · <OutreachStatus value={m.status} />
                    </summary>
                    <p className="admin-note">
                      {m.recipient} · {when(m.sent_at || m.created_at)}
                    </p>
                    <pre>{m.body}</pre>
                    {m.error && <p role="alert">{m.error}</p>}
                  </details>
                ))}
                <div className="admin-card-actions">
                  <Button
                    disabled={!messages.data?.pagination.previous}
                    onClick={() => setPage(page - 1)}
                  >
                    Previous
                  </Button>
                  <Button
                    disabled={!messages.data?.pagination.next}
                    onClick={() => setPage(page + 1)}
                  >
                    Next
                  </Button>
                </div>
              </AdminState>
            </section>
            <section className="admin-card">
              <h2>Activity</h2>
              <AdminState
                query={activity}
                empty={!activity.data?.results.length}
                title="No recorded activity"
              >
                <ul className="admin-activity">
                  {activity.data?.results.map((e) => (
                    <li key={e.id}>
                      <time>{when(e.created_at)}</time>
                      <span>
                        {e.action.replaceAll("_", " ").replaceAll(".", " · ")}
                        {e.status ? ` · ${e.status}` : ""}
                      </span>
                    </li>
                  ))}
                </ul>
              </AdminState>
            </section>
          </div>
          <div className="admin-stack">
            <section className="admin-card">
              <h2>Contact details</h2>
              <dl>
                {[
                  ["Segment", contact?.segment],
                  ["Source", contact?.source],
                  [
                    "Platform / handle",
                    [contact?.platform, contact?.handle]
                      .filter(Boolean)
                      .join(" · "),
                  ],
                  ["Phone", contact?.phone],
                  ["Notes", contact?.notes],
                ].map(([key, value]) => (
                  <div key={key}>
                    <dt>{key}</dt>
                    <dd>{value || "—"}</dd>
                  </div>
                ))}
              </dl>
              <div className="admin-card-actions">
                {["replied", "interested", "partner", "not_interested"].map(
                  (status) => (
                    <ActionButton
                      key={status}
                      busy={mutation.isPending || contact?.suppressed}
                      onClick={() => updateStatus(status)}
                    >
                      Mark {status.replaceAll("_", " ")}
                    </ActionButton>
                  ),
                )}
                <Button
                  disabled={contact?.suppressed}
                  onClick={() => setDialog("suppress")}
                >
                  Do not contact
                </Button>
              </div>
            </section>
            <section className="admin-card">
              <h2>Sequence</h2>
              <AdminState query={enrollments}>
                {enrollments.data?.results.map((e) => (
                  <div key={e.id} className="outreach-enrollment">
                    <strong>{e.sequence_name}</strong>
                    <p>
                      <OutreachStatus value={e.status} />
                    </p>
                    {e.next_send_at && (
                      <p className="admin-note">
                        Next eligible: {when(e.next_send_at)}
                      </p>
                    )}
                    {e.status === "pending_review" ? (
                      <Link to="/admin/outreach/review">Review email</Link>
                    ) : null}
                    <div className="admin-card-actions">
                      {[
                        ["pause", "Pause"],
                        ["resume", "Resume"],
                        ["stop", "Stop"],
                        ["send_next", "Schedule next step now"],
                      ]
                        .filter(([action]) =>
                          action === "resume"
                            ? e.status === "paused"
                            : action === "stop"
                              ? [
                                  "pending_review",
                                  "scheduled",
                                  "active",
                                  "paused",
                                ].includes(e.status)
                              : ["scheduled", "active"].includes(e.status),
                        )
                        .map(([action, name]) => (
                          <ActionButton
                            key={action}
                            busy={mutation.isPending}
                            onClick={() =>
                              mutation.mutateAsync({
                                resource: "enrollments",
                                id: e.id,
                                action: "state",
                                body: { action },
                              })
                            }
                          >
                            {name}
                          </ActionButton>
                        ))}
                    </div>
                  </div>
                ))}
                <Button
                  disabled={contact?.suppressed}
                  onClick={() => setDialog("enroll")}
                >
                  Enroll in sequence
                </Button>
              </AdminState>
              <p className="admin-note">
                Sending windows and caps apply to all scheduled messages.
              </p>
            </section>
            <section className="admin-card">
              <h2>WhatsApp</h2>
              <Field label="Message template">
                <Select
                  value={template}
                  onChange={(_, d) => setTemplate(d.value)}
                >
                  <option value="">Choose template</option>
                  {templates.data?.results.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name}
                    </option>
                  ))}
                </Select>
              </Field>
              <ActionButton
                busy={
                  !template ||
                  !contact?.whatsapp ||
                  contact?.suppressed ||
                  mutation.isPending
                }
                onClick={async () => {
                  const result = await mutation.mutateAsync({
                    resource: "templates",
                    id: template,
                    action: "whatsapp",
                    body: { contact: id },
                  });
                  await navigator.clipboard.writeText(result.body);
                  window.open(
                    `https://wa.me/${result.number.replace(/\D/g, "")}?text=${encodeURIComponent(result.body)}`,
                    "_blank",
                    "noopener,noreferrer",
                  );
                  toast.success("Message copied. Send it from WhatsApp.");
                }}
              >
                Copy WhatsApp message
              </ActionButton>
            </section>
          </div>
        </div>
      </AdminState>
      {dialog === "edit" && (
        <ContactDrawer contact={contact} onClose={() => setDialog(null)} />
      )}
      {dialog === "early" && (
        <EarlyAccessDialog contact={contact} onClose={() => setDialog(null)} />
      )}
      {dialog === "enroll" && (
        <EnrollmentDrawer
          contact={contact}
          sequences={sequences.data?.results}
          onClose={() => setDialog(null)}
        />
      )}
      {dialog === "suppress" && (
        <ConfirmAction
          title="Permanently stop outreach?"
          label="Do not contact"
          description="This email will remain suppressed even if the contact is deleted and added again."
          onClose={() => setDialog(null)}
          onConfirm={async () => {
            await updateStatus("do_not_contact");
            setDialog(null);
          }}
        />
      )}
    </div>
  );
}
