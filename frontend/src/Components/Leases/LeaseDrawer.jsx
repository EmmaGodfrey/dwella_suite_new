import React, { useState } from "react";
import {
  Button,
  DrawerBody,
  DrawerFooter,
  DrawerHeader,
  DrawerHeaderTitle,
  Dropdown,
  Field,
  Option,
  OverlayDrawer,
} from "@fluentui/react-components";
import { Dismiss24Regular } from "@fluentui/react-icons";
import { toast } from "react-toastify";

import { useSaveLeaseMutation } from "../../Services/mutations";
import { useTenantsQuery } from "../../Services/queries";
import { LEASE_FIELDS, emptyLease, leasePayload, leaseRules } from "../../shared/tenancy";
import { useFormErrors } from "../../shared/useFormErrors";
import LeaseFields from "./LeaseFields";

// New lease for a tenant already on file (e.g. a renewal or a move to
// another unit). New tenants get their lease from the Add tenant drawer.
export default function LeaseDrawer({ open, onClose, onSaved }) {
  const [tenantId, setTenantId] = useState("");
  const [lease, setLease] = useState(emptyLease);
  const { validate, clearError, fieldProps, showServerErrors } = useFormErrors();
  const tenantsQuery = useTenantsQuery({ page_size: 200, ordering: "full_name" }, { staleTime: 30_000 });
  const tenants = tenantsQuery.data?.results || [];
  const selected = tenants.find((tenant) => tenant.id === tenantId);

  const mutation = useSaveLeaseMutation({
    onSuccess: (data) => {
      toast.success(`Lease ${data.reference} created.`);
      onSaved?.(data);
    },
    onError: (error) => {
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
    const ok = validate({ tenant: () => (tenantId ? "" : "Choose a tenant."), ...leaseRules(lease) }, event.currentTarget);
    if (ok) mutation.mutate({ payload: { tenant: tenantId, ...leasePayload(lease) } });
  };

  return (
    <OverlayDrawer open={open} position="end" size="medium" className="dwella-drawer" onOpenChange={(_, data) => !data.open && !mutation.isPending && onClose()}>
      <DrawerHeader>
        <DrawerHeaderTitle action={<Button appearance="subtle" aria-label="Close" icon={<Dismiss24Regular />} disabled={mutation.isPending} onClick={onClose} />}>
          New lease
        </DrawerHeaderTitle>
        <p className="dwella-drawer-note">For a tenant already on file. To add someone new, use Add tenant on the Tenants page.</p>
      </DrawerHeader>
      <form id="lease-form" noValidate onSubmit={submit} className="dwella-drawer-form">
        <DrawerBody>
          <fieldset disabled={mutation.isPending}>
            <section className="dwella-form-section">
              <h3>Tenant</h3>
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
            </section>
            <section className="dwella-form-section">
              <h3>Unit and terms</h3>
              <LeaseFields lease={lease} onChange={updateLease} fieldProps={fieldProps} />
            </section>
          </fieldset>
        </DrawerBody>
      </form>
      <DrawerFooter className="dwella-drawer-footer">
        <Button onClick={onClose} disabled={mutation.isPending}>Cancel</Button>
        <Button appearance="primary" type="submit" form="lease-form" disabled={mutation.isPending}>
          {mutation.isPending ? "Creating…" : "Create lease"}
        </Button>
      </DrawerFooter>
    </OverlayDrawer>
  );
}
