import React, { useEffect, useState } from "react";
import { Button, Dropdown, Field, Input, Option, Switch, Textarea } from "@fluentui/react-components";
import {
  Call20Regular,
  CheckmarkCircle16Filled,
  Circle16Regular,
  FormMultiple24Regular,
  KeyMultiple20Regular,
  Mail20Regular,
  PersonAdd20Regular,
  Search20Regular,
} from "@fluentui/react-icons";
import { toast } from "react-toastify";

import { useSendBetaAccessMutation, useUpdateBetaApplicationMutation } from "../../Services/mutations";
import { useBetaApplicationsQuery, useBetaEmailSettingsQuery } from "../../Services/queries";
import { EmptyState, PageActions, SegmentedFilter, StatusBadge } from "../../shared/components";
import AddSignupDrawer, { roles } from "./AddSignupDrawer";
import "../../shared/records.scss";
import "./betaSignups.scss";

const PAGE_SIZE = 30;
const statusOptions = [
  { value: "all", label: "All" },
  { value: "new", label: "New" },
  { value: "contacted", label: "Contacted" },
  { value: "accepted", label: "Accepted" },
  { value: "declined", label: "Declined" },
];
const workflowStatuses = statusOptions.slice(1);
const statusColor = {
  new: "informative",
  contacted: "warning",
  accepted: "success",
  declined: "danger",
};
const dateTime = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});
const shortDate = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short" });
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// Mirrors the backend sequence in apps/marketing/emails.py.
function emailSteps(betaOpenDate) {
  const opens = betaOpenDate ? new Date(`${betaOpenDate}T08:00:00`) : null;
  const daysBefore = (days) => {
    if (!opens) return null;
    const day = new Date(opens);
    day.setDate(day.getDate() - days);
    return day;
  };
  return [
    { kind: "welcome", label: "Welcome", planned: null },
    { kind: "two_weeks", label: "Two weeks to go", planned: daysBefore(14) },
    { kind: "one_week", label: "One week to go", planned: daysBefore(7) },
    { kind: "eve", label: "Beta tomorrow", planned: daysBefore(1) },
    { kind: "access", label: "Sign-in details", planned: opens },
  ];
}

function EmailTimeline({ application, settings }) {
  const sent = Object.fromEntries((application.emails || []).map((email) => [email.kind, email]));
  const sendAccess = useSendBetaAccessMutation({
    onSuccess: (data) => toast.success(`Sign-in details sent to ${data.email}.`),
    onError: (error) => toast.error(error.message || "Could not send the sign-in details."),
  });
  let blocked = "";
  if (!application.email) blocked = "Add an email address to send beta emails.";
  else if (application.status === "declined") blocked = "Declined signups get no further emails.";
  else if (!settings?.enabled) blocked = "Beta emails are turned off on this server.";

  return (
    <section className="dwella-beta-emails" aria-label="Beta emails">
      <h3>Beta emails</h3>
      <ol>
        {emailSteps(settings?.beta_open_date).map((step) => {
          const email = sent[step.kind];
          let when = "On signup";
          if (email) when = `Sent ${dateTime.format(new Date(email.sent_at))}`;
          else if (step.planned) when = shortDate.format(step.planned);
          return (
            <li key={step.kind} className={email ? "is-sent" : undefined}>
              {email ? <CheckmarkCircle16Filled aria-hidden="true" /> : <Circle16Regular aria-hidden="true" />}
              <span>{step.label}</span>
              <span className="dwella-cell-note">{when}</span>
            </li>
          );
        })}
      </ol>
      {application.unsubscribed_at ? (
        <p className="dwella-cell-note">Stopped countdown emails. They still get their sign-in details.</p>
      ) : null}
      {application.account_email ? <p className="dwella-cell-note">Account: {application.account_email}</p> : null}
      {blocked ? <p className="dwella-cell-note">{blocked}</p> : null}
      <Button
        icon={<KeyMultiple20Regular />}
        disabled={Boolean(blocked) || sendAccess.isPending}
        onClick={() => sendAccess.mutate(application.id)}
      >
        {sendAccess.isPending ? "Sending…" : sent.access ? "Resend sign-in link" : "Send sign-in details now"}
      </Button>
    </section>
  );
}

function SignupDetail({ application, settings }) {
  const [status, setStatus] = useState(application.status);
  const [notes, setNotes] = useState(application.internal_notes || "");
  const [email, setEmail] = useState(application.email || "");
  const [emailError, setEmailError] = useState("");
  const updateMutation = useUpdateBetaApplicationMutation({
    onSuccess: () => toast.success("Signup follow-up updated."),
    onError: (error) => toast.error(error.data?.email?.[0] || error.message || "Could not update the signup."),
  });

  useEffect(() => {
    setStatus(application.status);
    setNotes(application.internal_notes || "");
    setEmail(application.email || "");
    setEmailError("");
  }, [application]);

  const emailChanged = email.trim().toLowerCase() !== (application.email || "");
  const dirty = status !== application.status || notes !== (application.internal_notes || "") || emailChanged;
  const save = () => {
    if (emailChanged && !EMAIL_PATTERN.test(email.trim())) {
      setEmailError("Enter a valid email address.");
      return;
    }
    updateMutation.mutate({
      id: application.id,
      payload: { status, internal_notes: notes, ...(emailChanged ? { email: email.trim().toLowerCase() } : {}) },
    });
  };

  return (
    <aside className="dwella-beta-detail" aria-label={`${application.name} signup details`}>
      <header>
        <div>
          <span className="dwella-beta-eyebrow">Applicant</span>
          <h2>{application.name}</h2>
          <p>{application.role} · {application.units} units</p>
        </div>
        <StatusBadge value={application.status} color={statusColor[application.status]} />
      </header>

      <div className="dwella-contact-actions">
        <Button as="a" href={`tel:${application.phone}`} icon={<Call20Regular />}>Call</Button>
        <Button
          as="a"
          href={application.email ? `mailto:${application.email}` : undefined}
          disabled={!application.email}
          icon={<Mail20Regular />}
        >
          Email
        </Button>
      </div>

      <dl className="dwella-detail-list">
        <div><dt>Phone</dt><dd>{application.phone}</dd></div>
        <div><dt>Email</dt><dd>{application.email || "Not provided"}</dd></div>
        <div><dt>Town</dt><dd>{application.town || "Not provided"}</dd></div>
        <div><dt>Applied</dt><dd>{dateTime.format(new Date(application.created_at))}</dd></div>
        <div><dt>Source</dt><dd>{application.source === "admin" ? "Added by Dwella" : "Website"}</dd></div>
      </dl>

      <EmailTimeline application={application} settings={settings} />

      <div className="dwella-beta-follow-up">
        <h3>Follow-up</h3>
        <Field label="Status">
          <Dropdown
            value={workflowStatuses.find((item) => item.value === status)?.label}
            selectedOptions={[status]}
            onOptionSelect={(_, data) => setStatus(data.optionValue)}
          >
            {workflowStatuses.map((item) => <Option key={item.value} value={item.value}>{item.label}</Option>)}
          </Dropdown>
        </Field>
        <Field
          label="Email"
          validationState={emailError ? "error" : "none"}
          validationMessage={emailError || undefined}
          hint={application.account_email ? "Their account exists, so this can no longer change." : undefined}
        >
          <Input
            type="email"
            value={email}
            disabled={Boolean(application.account_email)}
            onChange={(_, data) => { setEmail(data.value); setEmailError(""); }}
            placeholder="name@example.com"
          />
        </Field>
        <Field label="Private notes" hint="Only platform administrators can see these notes.">
          <Textarea
            rows={5}
            maxLength={2000}
            value={notes}
            onChange={(_, data) => setNotes(data.value)}
            placeholder="Demo preference, portfolio context, next call..."
          />
        </Field>
        <Button appearance="primary" disabled={!dirty || updateMutation.isPending} onClick={save}>
          {updateMutation.isPending ? "Saving..." : "Save follow-up"}
        </Button>
      </div>
    </aside>
  );
}

function TableSkeleton() {
  return [0, 1, 2, 3, 4].map((row) => (
    <tr key={row} className="is-loading" aria-hidden="true">
      <td><span className="dwella-skeleton" style={{ height: 12, width: 140 }} /></td>
      <td><span className="dwella-skeleton" style={{ height: 12, width: 100 }} /></td>
      <td><span className="dwella-skeleton" style={{ height: 12, width: 80 }} /></td>
      <td><span className="dwella-skeleton" style={{ height: 18, width: 66 }} /></td>
    </tr>
  ));
}

export default function BetaSignups() {
  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState(null);
  const [adding, setAdding] = useState(false);
  const settingsQuery = useBetaEmailSettingsQuery();
  const [filters, setFilters] = useState({
    search: "",
    status: "",
    role: "",
    page: 1,
    page_size: PAGE_SIZE,
    ordering: "-created_at",
  });

  useEffect(() => {
    const timeout = setTimeout(() => {
      setFilters((current) => current.search === search ? current : { ...current, search, page: 1 });
    }, 300);
    return () => clearTimeout(timeout);
  }, [search]);

  const listQuery = useBetaApplicationsQuery(filters, { staleTime: 20_000 });
  const applications = listQuery.data?.results || [];
  const pagination = listQuery.data?.pagination;
  const activeId = selectedId && applications.some((item) => item.id === selectedId)
    ? selectedId
    : applications[0]?.id;
  const selected = applications.find((item) => item.id === activeId);
  const filtered = Boolean(filters.search || filters.status || filters.role || filters.early_access);
  const clearFilters = () => {
    setSearch("");
    setSelectedId(null);
    setFilters((current) => ({ ...current, search: "", status: "", role: "", early_access: "", page: 1 }));
  };

  return (
    <div className="dwella-beta-page">
      <div className="dwella-page-toolbar">
        <SegmentedFilter
          label="Filter beta signups by status"
          options={statusOptions}
          value={filters.status || "all"}
          onChange={(value) => {
            setSelectedId(null);
            setFilters((current) => ({ ...current, status: value === "all" ? "" : value, page: 1 }));
          }}
        />
        <Dropdown
          className="dwella-beta-role-filter"
          aria-label="Filter by applicant role"
          value={filters.role || "All roles"}
          selectedOptions={[filters.role]}
          onOptionSelect={(_, data) => {
            setSelectedId(null);
            setFilters((current) => ({ ...current, role: data.optionValue, page: 1 }));
          }}
        >
          <Option value="">All roles</Option>
          {roles.map((role) => <Option key={role} value={role}>{role}</Option>)}
        </Dropdown>
        <Switch label="Early access only" checked={filters.early_access === "true"} onChange={(_, data) => {
          setSelectedId(null); setFilters(current => ({...current, early_access: data.checked ? "true" : "", page: 1}));
        }} />
        <Input
          className="dwella-toolbar-search"
          aria-label="Search beta signups"
          contentBefore={<Search20Regular />}
          placeholder="Search name, phone, email, town"
          value={search}
          onChange={(_, data) => {
            setSearch(data.value);
            setSelectedId(null);
          }}
        />
        <span className="dwella-beta-count">
          <strong>{pagination?.count ?? applications.length}</strong> signups
        </span>
        <PageActions>
          <Button appearance="primary" icon={<PersonAdd20Regular />} onClick={() => setAdding(true)}>Add signup</Button>
        </PageActions>
      </div>

      {settingsQuery.data && !settingsQuery.data.enabled ? (
        <div className="dwella-alert">
          Beta emails are turned off on this server. Signups are still saved, and missed welcome emails go out once emails are turned on.
        </div>
      ) : null}

      {listQuery.isError ? (
        <div className="dwella-alert danger">
          Unable to load beta signups. <Button size="small" onClick={() => listQuery.refetch()}>Retry</Button>
        </div>
      ) : null}

      {!listQuery.isLoading && !applications.length ? (
        <EmptyState
          icon={<FormMultiple24Regular />}
          title={filtered ? "No matching signups" : "No beta signups yet"}
          description={filtered ? "Try another status, role, or search." : "Applications from the Dwella website will appear here."}
          actionLabel={filtered ? "Clear filters" : undefined}
          onAction={filtered ? clearFilters : undefined}
        />
      ) : (
        <div className="dwella-beta-workspace">
          <div className="dwella-table-card" aria-busy={listQuery.isFetching}>
            <table className="dwella-table">
              <thead>
                <tr>
                  <th scope="col">Applicant</th>
                  <th scope="col">Portfolio</th>
                  <th scope="col">Applied</th>
                  <th scope="col">Status</th>
                </tr>
              </thead>
              <tbody>
                {listQuery.isLoading ? <TableSkeleton /> : null}
                {applications.map((application) => {
                  const active = application.id === activeId;
                  return (
                    <tr
                      key={application.id}
                      className={active ? "is-selected" : undefined}
                      aria-selected={active}
                      tabIndex={0}
                      onClick={() => setSelectedId(application.id)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter" || event.key === " ") {
                          event.preventDefault();
                          setSelectedId(application.id);
                        }
                      }}
                    >
                      <td><strong>{application.name}</strong><span className="dwella-cell-note">{application.phone}</span></td>
                      <td>{application.role}<span className="dwella-cell-note">{application.units} units · {application.town || "Town not provided"}</span></td>
                      <td>{dateTime.format(new Date(application.created_at))}</td>
                      <td><StatusBadge value={application.status} color={statusColor[application.status]} />{application.early_access && <StatusBadge value="early_access" color="success" />}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            {pagination ? (
              <footer className="dwella-table-footer">
                <span>Showing {applications.length} of {pagination.count}</span>
                {pagination.total_pages > 1 ? (
                  <span className="dwella-table-pager">
                    <Button size="small" disabled={!pagination.previous} onClick={() => setFilters((value) => ({ ...value, page: value.page - 1 }))}>Previous</Button>
                    <Button size="small" disabled={!pagination.next} onClick={() => setFilters((value) => ({ ...value, page: value.page + 1 }))}>Next</Button>
                  </span>
                ) : null}
              </footer>
            ) : null}
          </div>

          {selected ? <SignupDetail key={selected.id} application={selected} settings={settingsQuery.data} /> : null}
        </div>
      )}

      {adding ? (
        <AddSignupDrawer
          emailsEnabled={Boolean(settingsQuery.data?.enabled)}
          onClose={() => setAdding(false)}
          onSaved={(data) => {
            setAdding(false);
            setSelectedId(data.id);
          }}
        />
      ) : null}
    </div>
  );
}
