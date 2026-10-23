import React, { useState } from "react";
import {
  Field,
  Input,
  Switch,
  Textarea,
} from "@fluentui/react-components";
import { toast } from "react-toastify";

import { useSaveTenantMutation } from "../../Services/mutations";
import { LEASE_FIELDS, emptyLease, leasePayload, leaseRules } from "../../shared/tenancy";
import { useFormErrors } from "../../shared/useFormErrors";
import LeaseFields from "../Leases/LeaseFields";
import { FormDrawer, FormReview } from "../../shared/components/FormFlow";
import { firstErrorStep, ruleErrors } from "../../shared/formFlow";
import { formatDate, formatMoney } from "../../shared/format";

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
  const [step, setStep] = useState(0);
  const [withLease, setWithLease] = useState(!editing);
  const [lease, setLease] = useState(emptyLease);
  const { errors, validate, clearError, fieldProps, showServerErrors } =
    useFormErrors();

  const mutation = useSaveTenantMutation({
    onSuccess: (data) => {
      toast.success(editing ? "Tenant updated." : data.current_lease ? "Tenant and lease added." : "Tenant added.");
      onSaved?.(data);
    },
    onError: (error) => {
      if (!editing)
        setStep(
          firstErrorStep(
            error.data,
            [
              TENANT_FIELDS,
              ...(withLease
                ? [LEASE_FIELDS.map((name) => `lease.${name}`)]
                : []),
              [],
            ],
            step,
          ),
        );
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
    const allRules = {
      full_name: () =>
        form.full_name.trim().length >= 2
          ? ""
          : "Enter the tenant's full name.",
      phone_number: () =>
        looksLikePhone(form.phone_number)
          ? ""
          : "Enter a valid phone number, for example 097 123 4567.",
      email: () =>
        !form.email.trim() || /^\S+@\S+\.\S+$/.test(form.email.trim())
          ? ""
          : "Enter a valid email address.",
      ...(withLease ? leaseRules(lease, "lease.") : {}),
    };
    const groups = [
      TENANT_FIELDS,
      ...(withLease ? [LEASE_FIELDS.map((name) => `lease.${name}`)] : []),
      [],
    ];
    const last = groups.length - 1;
    const rules =
      editing || step === last
        ? allRules
        : Object.fromEntries(
            Object.entries(allRules).filter(([name]) =>
              groups[step].includes(name),
            ),
          );
    if (!validate(rules, event.currentTarget)) {
      if (!editing) setStep(firstErrorStep(ruleErrors(rules), groups, step));
      return;
    }
    if (!editing && step < last) {
      setStep(step + 1);
      return;
    }
    const payload = Object.fromEntries(TENANT_FIELDS.map((key) => [key, form[key].trim()]));
    if (withLease) payload.lease = leasePayload(lease);
    mutation.mutate({ id: tenant?.id, payload });
  };

  const tenantFields = (
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
  );
  if (!editing)
    return (
      <FormDrawer
        open={open}
        title="Add tenant"
        description="Add contact details, then choose whether to create a lease."
        steps={withLease ? ["Tenant", "Lease", "Review"] : ["Tenant", "Review"]}
        step={step}
        stepTitle={
          step === 0
            ? "Tenant details"
            : withLease && step === 1
              ? "Unit and lease"
              : "Review tenant and lease"
        }
        stepDescription={
          step === 0
            ? "Fields marked * are required."
            : withLease && step === 1
              ? "Select a vacant unit. Asking rent fills in automatically and can be adjusted."
              : "Check these details before adding the tenant."
        }
        onSubmit={submit}
        onBack={() => setStep(step - 1)}
        onClose={onClose}
        busy={mutation.isPending}
        errors={errors}
        submitLabel={withLease ? "Add tenant and lease" : "Add tenant"}
      >
        {step === 0 ? (
          <>
            {tenantFields}
            <section className="dwella-form-section">
              <h3>Create a lease with this tenant</h3>
              <Switch
                checked={withLease}
                onChange={(_, data) => setWithLease(data.checked)}
                label={withLease ? "Assign now" : "Add tenant only"}
              />
              <p className="dwella-muted-copy">
                Add tenant only skips the Lease step. Nothing is saved until you
                confirm.
              </p>
            </section>
          </>
        ) : withLease && step === 1 ? (
          <LeaseFields lease={lease} onChange={updateLease} fieldProps={fieldProps} prefix="lease." />
        ) : (
          <FormReview
            onEdit={setStep}
            items={[
              { label: "Tenant", value: form.full_name, step: 0 },
              { label: "Phone", value: form.phone_number, step: 0 },
              { label: "Email", value: form.email, step: 0 },
              { label: "NRC or passport", value: form.national_id, step: 0 },
              ...(form.notes
                ? [{ label: "Notes", value: form.notes, step: 0 }]
                : []),
              ...(withLease
                ? [
                    { label: "Unit", value: lease._unitLabel, step: 1 },
                    {
                      label: "Lease dates",
                      value: `${formatDate(lease.start_date)} – ${formatDate(lease.end_date)}`,
                      step: 1,
                    },
                    {
                      label: "Rent and deposit",
                      value: `${formatMoney(lease.monthly_rent)} / month · ${formatMoney(lease.deposit_amount || 0)} deposit`,
                      step: 1,
                    },
                    {
                      label: "Due and status",
                      value: `Day ${lease.rent_due_day} · ${lease.activate ? "Start now" : "Save as draft"}`,
                      step: 1,
                    },
                  ]
                : []),
            ]}
          />
        )}
      </FormDrawer>
    );

  return <FormDrawer open={open} title="Edit tenant"
    description="Update contact details. Lease terms live on the lease."
    onSubmit={submit} onClose={onClose} errors={errors} busy={mutation.isPending}
    submitLabel="Save changes">{tenantFields}</FormDrawer>;
}
