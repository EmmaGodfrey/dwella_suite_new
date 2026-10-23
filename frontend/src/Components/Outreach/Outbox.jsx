import React, { useState } from "react";
import { useOutreachList, useOutreachMutation } from "../../Services/outreach";
import {
  AdminDrawer,
  AdminHeader,
  AdminState,
  AdminTable,
  Filter,
  when,
} from "../Platform/AdminUI";
import {
  ActionButton,
  OutreachStatus,
  OutreachTabs,
  options,
} from "./OutreachUI";
import "./outreach.scss";

export default function Outbox() {
  const [filters, setFilters] = useState({ page: 1, status: "" });
  const query = useOutreachList("messages", filters);
  const settings = useOutreachList("settings");
  const summary = useOutreachList("summary");
  const mutation = useOutreachMutation();
  const [selected, setSelected] = useState(null);
  return (
    <div className="admin-screen outreach-screen">
      <AdminHeader
        title="Outbox"
        description="Delivery activity and the upcoming sending schedule."
      >
        <ActionButton
          busy={mutation.isPending || !settings.data}
          appearance="primary"
          onClick={() =>
            mutation.mutateAsync({
              resource: "settings",
              method: "patch",
              body: { paused: !settings.data.paused },
            })
          }
        >
          {settings.data?.paused
            ? "Resume approved sending"
            : "Pause all sending"}
        </ActionButton>
      </AdminHeader>
      <OutreachTabs />
      <AdminState query={summary}>
        <section className="admin-card">
          <dl className="admin-metrics">
            {[
              ["Sent today", summary.data?.sent_today],
              ["Remaining today", summary.data?.remaining_today],
              ["Awaiting review", summary.data?.awaiting_review],
              [
                "Sending",
                settings.data?.enabled
                  ? settings.data.paused
                    ? "Paused"
                    : "Enabled"
                  : "Disabled",
              ],
            ].map(([key, value]) => (
              <div key={key}>
                <dt>{key}</dt>
                <dd>{value}</dd>
              </div>
            ))}
          </dl>
        </section>
      </AdminState>
      <Filter
        label="Message status"
        value={filters.status}
        options={options(["pending", "sent", "failed", "bounced"])}
        onChange={(status) => setFilters({ status, page: 1 })}
      />
      <AdminState
        query={query}
        empty={!query.data?.results.length}
        title="No approved or sent messages"
      >
        <AdminTable
          rows={query.data?.results || []}
          pagination={query.data?.pagination}
          setPage={(page) => setFilters({ ...filters, page })}
          columns={[
            { key: "contact_name", label: "Contact" },
            {
              key: "subject",
              label: "Email",
              render: (m) => (
                <button
                  type="button"
                  className="outreach-text-button"
                  onClick={() => setSelected(m)}
                >
                  {m.subject}
                </button>
              ),
            },
            {
              key: "status",
              label: "Status",
              render: (m) => (
                <OutreachStatus
                  value={
                    m.status === "pending" &&
                    !["active", "scheduled"].includes(m.enrollment_status)
                      ? m.enrollment_status
                      : m.status
                  }
                />
              ),
            },
            { key: "sent_at", label: "Sent", render: (m) => when(m.sent_at) },
            { key: "error", label: "Delivery note" },
          ]}
        />
      </AdminState>
      <p className="admin-note">
        Weekdays {settings.data?.send_from_hour}:00–
        {settings.data?.send_until_hour}:00 Africa/Lusaka. Replies and
        suppression are checked before each email.
      </p>
      {selected && (
        <AdminDrawer
          title={selected.subject}
          fields={[]}
          submitLabel="Close"
          onClose={() => setSelected(null)}
          onSubmit={async () => setSelected(null)}
        >
          <p>{selected.recipient}</p>
          <pre className="outreach-message-body">{selected.body}</pre>
          <OutreachStatus value={selected.status} />
        </AdminDrawer>
      )}
    </div>
  );
}
