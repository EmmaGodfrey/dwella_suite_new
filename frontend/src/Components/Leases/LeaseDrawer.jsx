import React, { useState } from "react";
import { Dropdown, Field, Option } from "@fluentui/react-components";
import { toast } from "react-toastify";

import { useSaveLeaseMutation } from "../../Services/mutations";
import { useTenantsQuery } from "../../Services/queries";
import { LEASE_FIELDS, emptyLease, leasePayload, leaseRules } from "../../shared/tenancy";
import { useFormErrors } from "../../shared/useFormErrors";
import LeaseFields, { LeaseStatus } from "./LeaseFields";
import { FormDrawer } from "../../shared/components/FormFlow";
import { firstErrorStep, ruleErrors } from "../../shared/formFlow";

const groups = [
  ["tenant", "unit"],
  LEASE_FIELDS.filter((name) => name !== "unit"),
];

// New lease for a tenant already on file (e.g. a renewal or a move to
// another unit). New tenants get their lease from the Add tenant drawer.
export default function LeaseDrawer({ open, onClose, onSaved }) {
  const [step, setStep] = useState(0);
  const [tenantId, setTenantId] = useState("");
  const [lease, setLease] = useState(emptyLease);
  const { errors, validate, clearError, fieldProps, showServerErrors } =
    useFormErrors();
  const tenantsQuery = useTenantsQuery({ page_size: 200, ordering: "full_name" }, { staleTime: 30_000 });
  const tenants = tenantsQuery.data?.results || [];
  const selected = tenants.find((tenant) => tenant.id === tenantId);

  const mutation = useSaveLeaseMutation({
    onSuccess: (data) => {
      toast.success(`Lease ${data.reference} created.`);
      onSaved?.(data);
    },
    onError: (error) => {
      setStep(firstErrorStep(error.data, groups, step));
      if (!showServerErrors(error.data, ["tenant", ...LEASE_FIELDS])) toast.error(error.message || "Could not create the lease.");
    },
  });

  const updateLease = (key, value) => {
    setLease((current) => ({ ...current, [key]: value }));
    clearError(key);
  };

  const submit = (event) => {
    event.preventDefault();
    if (mutation.isPending) return;
    const allRules = {
      tenant: () => (tenantId ? "" : "Choose a tenant."),
      ...leaseRules(lease),
    };
    const rules =
      step === 1
        ? allRules
        : Object.fromEntries(
            Object.entries(allRules).filter(([name]) =>
              groups[step].includes(name),
            ),
          );
    if (!validate(rules, event.currentTarget)) {
      setStep(firstErrorStep(ruleErrors(rules), groups, step));
      return;
    }
    if (step < 1) setStep(step + 1);
    else
      mutation.mutate({ payload: { tenant: tenantId, ...leasePayload(lease) } });
  };

  return (
    <FormDrawer
      open={open}
      title="New lease"
      description="Create a lease for a tenant already on file."
      steps={["Tenant and unit", "Terms"]}
      step={step}
      stepTitle={
        ["Tenant and unit", "Terms and rent"][step]
      }
      stepDescription={
        [
          "Choose a tenant and an available unit.",
          "Keep dates and financial terms together.",
        ][step]
      }
      onSubmit={submit}
      onBack={() => setStep(step - 1)}
      onClose={onClose}
      errors={errors}
      busy={mutation.isPending}
      submitLabel="Create lease"
      pendingLabel="Creating lease…"
    >
      {step === 0 ? (
        <>
          <Field label="Tenant" required {...fieldProps("tenant")}>
                <Dropdown
                  placeholder={tenantsQuery.isLoading ? "Loading tenants…" : "Choose a tenant"}
                  disabled={tenantsQuery.isLoading || !tenants.length}
                  selectedOptions={tenantId ? [tenantId] : []}
                  value={selected ? selected.full_name : ""}
                  onOptionSelect={(_, data) => {
                    setTenantId(data.optionValue);
                    clearError("tenant");
                  }}
                >
                  {tenants.map((tenant) => (
                    <Option key={tenant.id} value={tenant.id} text={tenant.full_name}>
                      <span className="dwella-option-split">
                        <span>{tenant.full_name}</span>
                        <small>{tenant.phone_number}</small>
                      </span>
                    </Option>
                  ))}
                </Dropdown>
              </Field>
          <LeaseFields
            section="unit"
            lease={lease}
            onChange={updateLease}
            fieldProps={fieldProps}
          />
        </>
      ) : (
        <>
          <LeaseFields section="terms" lease={lease} onChange={updateLease} fieldProps={fieldProps} />
          <LeaseStatus lease={lease} onChange={updateLease} />
        </>
      )}
    </FormDrawer>
  );
}
