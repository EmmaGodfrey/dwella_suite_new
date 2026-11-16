import React, { useId, useState } from "react";
import { Checkbox, Field, Input, Select, Textarea } from "@fluentui/react-components";
import { toast } from "react-toastify";

import { usePropertiesQuery } from "../../Services/queries";
import { useInviteMember, useStartCover, useUpdateMember } from "../../Services/team";
import { FormDrawer } from "../../shared/components/FormFlow";
import { useFormErrors } from "../../shared/useFormErrors";

export const ROLES = [
  { value: "manager", label: "Property manager", note: "Works only on the properties you assign." },
  { value: "landlord", label: "Property admin", note: "Sees every property, the team, payouts and workspace settings." },
];
const roleNote = (role) => ROLES.find((item) => item.value === role)?.note;
const looksLikeEmail = (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);

function RoleField({ value, onChange, disabled, fieldProps }) {
  return (
    <Field label="Role" hint={roleNote(value)} {...fieldProps}>
      <Select value={value} disabled={disabled} onChange={(_, data) => onChange(data.value)}>
        {ROLES.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
      </Select>
    </Field>
  );
}

// Not a Fluent Field: a Field hands one control id to everything inside it, and
// each checkbox here needs its own so its label ticks the right box.
function PropertyPicker({ selected, onChange, error }) {
  const id = useId();
  const query = usePropertiesQuery({ page_size: 200, ordering: "name" });
  const properties = query.data?.results || [];
  const toggle = (property, checked) => onChange(checked ? [...selected, property] : selected.filter((item) => item !== property));
  return (
    <div className="team-picker">
      <span className="team-picker-label" id={`${id}-label`}>Properties</span>
      {query.isPending ? <p role="status" className="dwella-muted-copy">Loading properties…</p>
        : query.isError ? <p role="alert" className="admin-error">Could not load properties. Close and try again.</p>
          : !properties.length ? <p className="dwella-muted-copy">No properties yet. You can assign them after adding one.</p>
            : (
              <div className="team-property-picker" role="group" aria-labelledby={`${id}-label`} aria-describedby={`${id}-hint`}>
                {properties.map((property) => (
                  <Checkbox
                    key={property.id}
                    label={property.name}
                    checked={selected.includes(property.id)}
                    onChange={(_, data) => toggle(property.id, data.checked === true)}
                  />
                ))}
              </div>
            )}
      {error ? <p role="alert" className="admin-error team-picker-hint">{error}</p> : null}
      <small className="team-picker-hint" id={`${id}-hint`}>{selected.length} selected. Assign whole properties; you can change this at any time.</small>
    </div>
  );
}

export function InviteDrawer({ onClose }) {
  const [form, setForm] = useState({ email: "", full_name: "", role: "manager", properties: [] });
  const errors = useFormErrors();
  const invite = useInviteMember();
  const change = (key, value) => { setForm((current) => ({ ...current, [key]: value })); errors.clearError(key); };
  const submit = (event) => {
    event.preventDefault();
    if (invite.isPending) return;
    const email = form.email.trim();
    if (!errors.validate({ email: () => (looksLikeEmail(email) ? "" : "Enter a valid email address.") }, event.currentTarget)) return;
    invite.mutate(
      { email, full_name: form.full_name.trim(), role: form.role, properties: form.role === "manager" ? form.properties : [] },
      {
        onSuccess: () => { toast.success(`Invitation sent to ${email}.`); onClose(); },
        onError: (error) => {
          if (!errors.showServerErrors(error.data, ["email", "full_name", "role", "properties"])) toast.error(error.message || "Could not send the invitation.");
        },
      },
    );
  };
  return (
    <FormDrawer
      title="Invite a team member"
      description="They get an email link that lasts 3 days. Access starts when they accept."
      onSubmit={submit}
      onClose={onClose}
      busy={invite.isPending}
      errors={errors.errors}
      submitLabel="Send invitation"
      pendingLabel="Sending…"
    >
      <div className="admin-fields">
        <Field label="Email" required {...errors.fieldProps("email")}>
          <Input type="email" maxLength={254} autoComplete="off" value={form.email} onChange={(_, data) => change("email", data.value)} />
        </Field>
        <Field label="Full name" {...errors.fieldProps("full_name")}>
          <Input maxLength={180} value={form.full_name} onChange={(_, data) => change("full_name", data.value)} />
        </Field>
        <RoleField value={form.role} onChange={(value) => change("role", value)} fieldProps={errors.fieldProps("role")} />
        {form.role === "manager" ? (
          <PropertyPicker selected={form.properties} onChange={(value) => change("properties", value)} error={errors.errors.properties} />
        ) : null}
      </div>
    </FormDrawer>
  );
}

export function MemberDrawer({ member, onClose }) {
  const [role, setRole] = useState(member.role);
  const [properties, setProperties] = useState(member.properties.map((item) => item.id));
  const errors = useFormErrors();
  const update = useUpdateMember();
  const submit = (event) => {
    event.preventDefault();
    if (update.isPending) return;
    update.mutate(
      { id: member.id, ...(role !== member.role ? { role } : {}), ...(role === "manager" ? { properties } : {}) },
      {
        onSuccess: () => { toast.success(`${member.name} updated.`); onClose(); },
        onError: (error) => {
          if (!errors.showServerErrors(error.data, ["role", "properties"])) toast.error(error.message || "Could not save this change.");
        },
      },
    );
  };
  return (
    <FormDrawer
      title={member.name}
      description={member.email || undefined}
      onSubmit={submit}
      onClose={onClose}
      busy={update.isPending}
      errors={errors.errors}
      submitLabel="Save changes"
    >
      <div className="admin-fields">
        <RoleField
          value={role}
          disabled={member.is_you}
          onChange={(value) => { setRole(value); errors.clearError("role"); }}
          fieldProps={errors.fieldProps("role")}
        />
        {member.is_you ? <p className="dwella-muted-copy">Ask another property admin to change your own role.</p> : null}
        {role === "manager" ? (
          <PropertyPicker
            selected={properties}
            onChange={(value) => { setProperties(value); errors.clearError("properties"); }}
            error={errors.errors.properties}
          />
        ) : <p className="dwella-muted-copy">A property admin sees every property, so nothing needs assigning.</p>}
      </div>
    </FormDrawer>
  );
}

const HOURS = [[2, "2 hours"], [4, "4 hours"], [8, "8 hours"], [24, "1 day"], [48, "2 days"], [72, "3 days"]];

export function CoverDrawer({ teammates, onClose }) {
  const [form, setForm] = useState({ teammate: teammates[0]?.id || "", reason: "", hours: "8" });
  const errors = useFormErrors();
  const start = useStartCover();
  const change = (key, value) => { setForm((current) => ({ ...current, [key]: value })); errors.clearError(key); };
  const chosen = teammates.find((item) => item.id === form.teammate);
  const submit = (event) => {
    event.preventDefault();
    if (start.isPending) return;
    const reason = form.reason.trim();
    const ok = errors.validate({
      teammate: () => (form.teammate ? "" : "Choose a teammate."),
      reason: () => (reason.length >= 5 ? "" : "Say why in at least 5 characters."),
    }, event.currentTarget);
    if (!ok) return;
    start.mutate(
      { teammate: form.teammate, reason, hours: Number(form.hours) },
      {
        onSuccess: () => { toast.success(`You are now covering for ${chosen?.name || "your teammate"}.`); onClose(); },
        onError: (error) => {
          if (!errors.showServerErrors(error.data, ["teammate", "reason", "hours"])) toast.error(error.message || "Could not start the cover.");
        },
      },
    );
  };
  return (
    <FormDrawer
      title="Cover for a teammate"
      description="You work on their properties as well as your own until the cover ends. Every change you make there is recorded under your name."
      onSubmit={submit}
      onClose={onClose}
      busy={start.isPending}
      errors={errors.errors}
      submitLabel="Start cover"
      pendingLabel="Starting…"
    >
      <div className="admin-fields">
        <Field
          label="Teammate"
          required
          hint={chosen ? (chosen.properties.length ? chosen.properties.map((item) => item.name).join(", ") : "No properties assigned yet.") : undefined}
          {...errors.fieldProps("teammate")}
        >
          <Select value={form.teammate} onChange={(_, data) => change("teammate", data.value)}>
            {teammates.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </Select>
        </Field>
        <Field label="Reason" required {...errors.fieldProps("reason")}>
          <Textarea maxLength={300} placeholder="e.g. On leave until Friday" value={form.reason} onChange={(_, data) => change("reason", data.value)} />
        </Field>
        <Field label="For how long" {...errors.fieldProps("hours")}>
          <Select value={form.hours} onChange={(_, data) => change("hours", data.value)}>
            {HOURS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </Select>
        </Field>
      </div>
    </FormDrawer>
  );
}
