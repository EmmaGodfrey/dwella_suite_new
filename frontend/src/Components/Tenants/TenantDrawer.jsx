import React, { useState } from "react";
import {
  Button,
  DrawerBody,
  DrawerFooter,
  DrawerHeader,
  DrawerHeaderTitle,
  Field,
  Input,
  OverlayDrawer,
  Switch,
  Textarea,
} from "@fluentui/react-components";
import { Dismiss24Regular } from "@fluentui/react-icons";
import { toast } from "react-toastify";

import { useSaveTenantMutation } from "../../Services/mutations";
import { LEASE_FIELDS, emptyLease, leasePayload, leaseRules } from "../../shared/tenancy";
import { useFormErrors } from "../../shared/useFormErrors";
import LeaseFields from "../Leases/LeaseFields";

const TENANT_FIELDS = ["full_name", "phone_number", "email", "national_id", "notes"];
const SERVER_FIELDS = [...TENANT_FIELDS, ...LEASE_FIELDS.map((name) => `lease.${name}`)];

// Same shape the API accepts: local Zambian numbers or +<country><number>.
const looksLikePhone = (value) => {
  const digits = value.replace(/\D/g, "");
  if (value.trim().startsWith("+")) return digits.length >= 8 && digits.length <= 15;
  return digits.length === 10 ? digits.startsWith("0") : digits.length === 9 || (digits.length === 12 && digits.startsWith("260"));
};

export default function TenantDrawer({ open, tenant, onClose, onSaved }) {
  const editing = Boolean(tenant);
  const [form, setForm] = useState(() => Object.fromEntries(TENANT_FIELDS.map((key) => [key, tenant?.[key] || ""])));
  const [withLease, setWithLease] = useState(!editing);
  const [lease, setLease] = useState(emptyLease);
  const { validate, clearError, fieldProps, showServerErrors } = useFormErrors();

  const mutation = useSaveTenantMutation({
    onSuccess: (data) => {
      toast.success(editing ? "Tenant updated." : data.current_lease ? "Tenant and lease added." : "Tenant added.");
      onSaved?.(data);
    },
    onError: (error) => {
      if (!showServerErrors(error.data, SERVER_FIELDS)) toast.error(error.message || "Could not save the tenant.");
    },
  });

  const update = (key, value) => {
    setForm((current) => ({ ...current, [key]: value }));
    clearError(key);
  };
  const updateLease = (key, value) => {
    setLease((current) => ({ ...current, [key]: value }));
    clearError(`lease.${key}`);
  };

  const submit = (event) => {
    event.preventDefault();
    if (mutation.isPending) return;
    const ok = validate(
      {
        full_name: () => (form.full_name.trim().length >= 2 ? "" : "Enter the tenant's full name."),
        phone_number: () => (looksLikePhone(form.phone_number) ? "" : "Enter a valid phone number, for example 097 123 4567."),
        email: () => (!form.email.trim() || /^\S+@\S+\.\S+$/.test(form.email.trim()) ? "" : "Enter a valid email address."),
        ...(withLease ? leaseRules(lease, "lease.") : {}),
      },
      event.currentTarget,
    );
    if (!ok) return;
    const payload = Object.fromEntries(TENANT_FIELDS.map((key) => [key, form[key].trim()]));
    if (withLease) payload.lease = leasePayload(lease);
    mutation.mutate({ id: tenant?.id, payload });
  };

  return (
    <OverlayDrawer
      open={open}
      position="end"
      size="medium"
      className="dwella-drawer"
      onOpenChange={(_, data) => !data.open && !mutation.isPending && onClose()}
    >
      <DrawerHeader>
        <DrawerHeaderTitle
          action={<Button appearance="subtle" aria-label="Close" icon={<Dismiss24Regular />} disabled={mutation.isPending} onClick={onClose} />}
        >
          {editing ? "Edit tenant" : "Add tenant"}
        </DrawerHeaderTitle>
        <p className="dwella-drawer-note">
          {editing ? "Update contact details. Lease terms live on the lease." : "Add who is renting, and optionally the unit and lease in one step."}
        </p>
      </DrawerHeader>

      <form id="tenant-form" noValidate onSubmit={submit} className="dwella-drawer-form">
        <DrawerBody>
          <fieldset disabled={mutation.isPending}>
            <section className="dwella-form-section">
              <h3>Tenant</h3>
              <div className="dwella-form-grid">
                <Field label="Full name" required {...fieldProps("full_name")} className={`dwella-field-wide ${fieldProps("full_name").className || ""}`}>
                  <Input maxLength={180} value={form.full_name} placeholder="e.g. Bwalya Kasonde" onChange={(_, d) => update("full_name", d.value)} />
                </Field>
                <Field label="Phone" required hint="Used for mobile money and reminders." {...fieldProps("phone_number")}>
                  <Input type="tel" inputMode="tel" value={form.phone_number} placeholder="097 123 4567" onChange={(_, d) => update("phone_number", d.value)} />
                </Field>
                <Field label="Email" {...fieldProps("email")}>
                  <Input type="email" value={form.email} placeholder="Optional" onChange={(_, d) => update("email", d.value)} />
                </Field>
                <Field label="NRC or passport" {...fieldProps("national_id")}>
                  <Input maxLength={40} value={form.national_id} placeholder="Optional" onChange={(_, d) => update("national_id", d.value)} />
                </Field>
                <Field label="Notes" className="dwella-field-wide">
                  <Textarea rows={2} value={form.notes} onChange={(_, d) => update("notes", d.value)} />
                </Field>
              </div>
            </section>

            {!editing ? (
              <section className="dwella-form-section">
                <div className="dwella-form-section-head">
                  <div>
                    <h3>Unit and lease</h3>
                    <p>Rent is filled in from the unit. You can generate the contract later.</p>
                  </div>
                  <Switch checked={withLease} onChange={(_, d) => setWithLease(d.checked)} label={withLease ? "Assign now" : "Later"} />
                </div>
                {withLease ? <LeaseFields lease={lease} onChange={updateLease} fieldProps={fieldProps} prefix="lease." /> : null}
              </section>
            ) : null}
          </fieldset>
        </DrawerBody>
      </form>

      <DrawerFooter className="dwella-drawer-footer">
        <Button onClick={onClose} disabled={mutation.isPending}>Cancel</Button>
        <Button appearance="primary" type="submit" form="tenant-form" disabled={mutation.isPending}>
          {mutation.isPending ? "Saving…" : editing ? "Save changes" : "Add tenant"}
        </Button>
      </DrawerFooter>
    </OverlayDrawer>
  );
}
