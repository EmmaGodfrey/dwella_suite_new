import React from "react";
import { NavLink } from "react-router-dom";
import { Button } from "@fluentui/react-components";
import { toast } from "react-toastify";
import { StatusBadge } from "../../shared/components/StatusBadge";
import { useOutreachMutation } from "../../Services/outreach";
import { AdminDrawer, ConfirmAction } from "../Platform/AdminUI";

export const segments = [
  "influencer",
  "agent",
  "property_manager",
  "landlord",
  "partner",
  "other",
];
export const platforms = [
  "tiktok",
  "instagram",
  "facebook",
  "linkedin",
  "website",
  "referral",
  "other",
];
export const statuses = [
  "new",
  "queued",
  "contacted",
  "replied",
  "interested",
  "partner",
  "not_interested",
  "do_not_contact",
  "bounced",
];
export const label = (s) =>
  s.replaceAll("_", " ").replace(/^./, (c) => c.toUpperCase());
export const options = (values) =>
  values.map((value) => ({ value, label: label(value) }));
export function OutreachTabs() {
  return (
    <nav className="outreach-tabs" aria-label="Outreach sections">
      {[
        ["", "Contacts"],
        ["/sequences", "Sequences"],
        ["/review", "Review queue"],
        ["/outbox", "Outbox"],
        ["/settings", "Settings"],
      ].map(([path, name]) => (
        <NavLink end key={name} to={`/admin/outreach${path}`}>
          {name}
        </NavLink>
      ))}
    </nav>
  );
}
export function OutreachStatus({ value }) {
  const color = [
    "interested",
    "partner",
    "replied",
    "sent",
    "completed",
    "ready",
  ].includes(value)
    ? "success"
    : [
          "do_not_contact",
          "stopped_optout",
          "stopped_bounce",
          "bounced",
          "failed",
        ].includes(value)
      ? "danger"
      : ["pending_review", "queued", "paused", "blocked"].includes(value)
        ? "warning"
        : "informative";
  return <StatusBadge value={value} color={color} />;
}
export const contactFields = [
  {
    key: "name",
    label: "Full name",
    required: true,
    minLength: 2,
    maxLength: 150,
  },
  { key: "first_name", label: "First name", maxLength: 80 },
  { key: "salutation", label: "Salutation (optional)", maxLength: 150 },
  { key: "email", label: "Email address", type: "email", maxLength: 254 },
  {
    key: "phone",
    label: "Phone",
    maxLength: 32,
    pattern: /^\+?[\d\s()-]{7,32}$/,
  },
  {
    key: "whatsapp",
    label: "WhatsApp",
    maxLength: 32,
    pattern: /^\+?[\d\s()-]{7,32}$/,
  },
  { key: "organization", label: "Organization", maxLength: 150 },
  { key: "title", label: "Role / title", maxLength: 150 },
  {
    key: "segment",
    label: "Segment",
    type: "select",
    required: true,
    options: options(segments),
  },
  {
    key: "platform",
    label: "Platform",
    type: "select",
    required: true,
    options: options(platforms),
  },
  { key: "handle", label: "Handle", maxLength: 100 },
  { key: "town", label: "Town", maxLength: 120 },
  {
    key: "profile_url",
    label: "Public profile / source URL",
    maxLength: 200,
    pattern: /^https?:\/\/\S+$/i,
  },
  {
    key: "source",
    label: "Where did this contact come from?",
    required: true,
    maxLength: 500,
  },
  { key: "notes", label: "Notes", type: "textarea", maxLength: 5000 },
];
export function ContactDrawer({ contact, onClose }) {
  const mutation = useOutreachMutation();
  return (
    <AdminDrawer
      steps={[
        { title: "Contact", fields: ["name", "first_name", "salutation", "email", "phone", "whatsapp"] },
        { title: "Context", fields: ["organization", "title", "segment", "platform", "handle", "town"] },
        { title: "Source", fields: ["profile_url", "source", "notes"] },
      ]}
      wideFields={["name", "email", "profile_url", "source", "notes"]}
      summary={(values) => <div className="dwella-form-context"><h3>{values.name}</h3><p>{[values.email, values.organization, values.town].filter(Boolean).join(" · ")}</p><p>Saving a contact does not send an email or enroll them in a sequence.</p></div>}
      title={contact ? "Edit contact" : "Add contact"}
      submitLabel={contact ? "Save changes" : "Add contact"}
      fields={contactFields}
      initial={contact || { segment: "other", platform: "other" }}
      onClose={onClose}
      onSubmit={async (values) => {
        const body = Object.fromEntries(
          contactFields.map((f) => [f.key, values[f.key] || ""]),
        );
        await mutation.mutateAsync({
          resource: "contacts",
          id: contact?.id,
          method: contact ? "patch" : "post",
          body,
        });
        toast.success("Contact saved.");
        onClose();
      }}
    >
      <p>
        Use a public business contact or details shared with you. Suppression
        and reply history stay in place.
      </p>
    </AdminDrawer>
  );
}
export function EnrollmentDrawer({ contact, sequences, onClose }) {
  const mutation = useOutreachMutation();
  return (
    <AdminDrawer
      title={`Enroll ${contact.name}`}
      onClose={onClose}
      fields={[
        {
          key: "sequence",
          label: "Sequence",
          type: "select",
          required: true,
          options: (sequences || []).map((s) => ({
            value: s.id,
            label: s.name,
          })),
        },
        {
          key: "personal_line",
          label: "Personal opening line",
          type: "textarea",
          maxLength: 1000,
        },
      ]}
      submitLabel="Add to review queue"
      onSubmit={async (values) => {
        await mutation.mutateAsync({
          resource: "enrollments",
          body: { ...values, contact: contact.id },
        });
        toast.success("Added to review queue. No email sent.");
        onClose();
      }}
    >
      <p>Review the complete first email before approving any sending.</p>
    </AdminDrawer>
  );
}
export function EarlyAccessDialog({ contact, onClose }) {
  const mutation = useOutreachMutation();
  return (
    <ConfirmAction
      title={`Give ${contact.name} early access?`}
      label="Send access email"
      description={`Send a one-time set-password link to ${contact.email}. Countdown emails stop and tester check-ins enter the review queue.`}
      onClose={onClose}
      onConfirm={async () => {
        await mutation.mutateAsync({
          resource: "contacts",
          id: contact.id,
          action: "early-access",
        });
        toast.success("Account access delivered.");
        onClose();
      }}
    />
  );
}
export function ErrorText({ error }) {
  return error ? (
    <p role="alert" className="admin-error">
      {error.message || JSON.stringify(error)}
    </p>
  ) : null;
}
export function ActionButton({ busy, children, onClick, ...rest }) {
  return (
    <Button
      disabled={busy}
      onClick={async () => {
        try {
          await onClick();
        } catch (error) {
          toast.error(error.message);
        }
      }}
      {...rest}
    >
      {children}
    </Button>
  );
}
