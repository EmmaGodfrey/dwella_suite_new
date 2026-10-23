import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Button, Field, Input } from "@fluentui/react-components";
import { useOutreachChoices, useOutreachList } from "../../Services/outreach";
import {
  AdminHeader,
  AdminState,
  AdminTable,
  Filter,
} from "../Platform/AdminUI";
import {
  ContactDrawer,
  EarlyAccessDialog,
  EnrollmentDrawer,
  OutreachStatus,
  OutreachTabs,
  options,
  platforms,
  segments,
  statuses,
} from "./OutreachUI";
import ImportContacts from "./ImportContacts";
import "./outreach.scss";

export default function Outreach() {
  const [filters, setFilters] = useState({ page: 1 });
  const [draft, setDraft] = useState({
    search: "",
    segment: "",
    status: "",
    platform: "",
  });
  const [dialog, setDialog] = useState(null);
  const query = useOutreachList("contacts", filters);
  const summary = useOutreachList("summary");
  const sequences = useOutreachChoices(
    "sequences",
    { active: true },
    { enabled: dialog?.type === "enroll" },
  );
  return (
    <div className="admin-screen outreach-screen">
      <AdminHeader
        title="Outreach"
        description="Personal partnerships and early tester invitations, from EG Labs."
      >
        <Button onClick={() => setDialog({ type: "import" })}>
          Import CSV
        </Button>
        <Button appearance="primary" onClick={() => setDialog({ type: "add" })}>
          Add contact
        </Button>
      </AdminHeader>
      <OutreachTabs />
      <AdminState query={summary}>
        <section className="admin-card">
          <dl className="admin-metrics">
            {[
              ["Contacts", summary.data?.contacts],
              ["Awaiting review", summary.data?.awaiting_review],
              [
                "Sent today",
                `${summary.data?.sent_today} of ${summary.data?.daily_cap}`,
              ],
              ["Replies", summary.data?.replies],
            ].map(([key, value]) => (
              <div key={key}>
                <dt>{key}</dt>
                <dd>{value}</dd>
              </div>
            ))}
          </dl>
        </section>
      </AdminState>
      <form
        className="admin-filters"
        onSubmit={(e) => {
          e.preventDefault();
          setFilters({ ...draft, page: 1 });
        }}
      >
        <Field label="Search contacts">
          <Input
            value={draft.search}
            placeholder="Name, organization or email"
            onChange={(_, d) => setDraft({ ...draft, search: d.value })}
          />
        </Field>
        {[
          ["segment", segments],
          ["status", statuses],
          ["platform", platforms],
        ].map(([key, choices]) => (
          <Filter
            key={key}
            label={key[0].toUpperCase() + key.slice(1)}
            value={draft[key]}
            options={options(choices)}
            onChange={(value) => setDraft({ ...draft, [key]: value })}
          />
        ))}
        <Button type="submit">Apply filters</Button>
      </form>
      <AdminState
        query={query}
        empty={!query.data?.results?.length}
        title="No contacts match this view"
      >
        <AdminTable
          rows={query.data?.results || []}
          pagination={query.data?.pagination}
          setPage={(page) => setFilters({ ...filters, page })}
          columns={[
            {
              key: "name",
              label: "Contact / organization",
              render: (c) => (
                <>
                  <Link
                    className="dwella-table-link"
                    to={`/admin/outreach/contacts/${c.id}`}
                  >
                    {c.name}
                  </Link>
                  <span className="admin-note">
                    {[c.organization, c.email].filter(Boolean).join(" · ")}
                  </span>
                </>
              ),
            },
            {
              key: "segment",
              label: "Segment / source",
              render: (c) => (
                <>
                  {c.segment.replaceAll("_", " ")}
                  <span className="admin-note">
                    {c.platform} · {c.source}
                  </span>
                </>
              ),
            },
            {
              key: "status",
              label: "Status",
              render: (c) => (
                <OutreachStatus
                  value={c.suppressed ? "do_not_contact" : c.status}
                />
              ),
            },
            {
              key: "action",
              label: "Next step",
              render: (c) =>
                c.suppressed ? (
                  <span className="admin-note">Suppressed permanently</span>
                ) : (
                  <div className="admin-card-actions">
                    <Button
                      appearance="subtle"
                      onClick={() => setDialog({ type: "enroll", contact: c })}
                    >
                      Enroll in sequence
                    </Button>
                    <Button
                      appearance="subtle"
                      disabled={!c.email}
                      onClick={() => setDialog({ type: "early", contact: c })}
                    >
                      Give early access
                    </Button>
                  </div>
                ),
            },
          ]}
        />
      </AdminState>
      {dialog?.type === "add" && (
        <ContactDrawer onClose={() => setDialog(null)} />
      )}
      {dialog?.type === "enroll" && (
        <EnrollmentDrawer
          contact={dialog.contact}
          sequences={sequences.data?.results}
          onClose={() => setDialog(null)}
        />
      )}
      {dialog?.type === "early" && (
        <EarlyAccessDialog
          contact={dialog.contact}
          onClose={() => setDialog(null)}
        />
      )}
      {dialog?.type === "import" && (
        <ImportContacts onClose={() => setDialog(null)} />
      )}
    </div>
  );
}
