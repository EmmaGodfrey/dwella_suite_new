import React, { useState } from "react";
import {
  Button,
  DrawerBody,
  DrawerFooter,
  DrawerHeader,
  DrawerHeaderTitle,
  Dropdown,
  Field,
  Input,
  Option,
  OverlayDrawer,
  Textarea,
} from "@fluentui/react-components";
import { Add20Regular, Delete20Regular, Dismiss24Regular } from "@fluentui/react-icons";
import { toast } from "react-toastify";

import { useSaveInvoiceMutation } from "../../Services/mutations";
import { useTenantsQuery } from "../../Services/queries";
import { lineKinds } from "../../shared/billing";
import { formatMoney, toIsoDate } from "../../shared/format";
import { useFormErrors } from "../../shared/useFormErrors";

let lineSeq = 0;
const newLine = () => ({ key: `line-${(lineSeq += 1)}`, kind: "utility", description: "", amount: "" });
const cleanAmount = (value) => String(value).replace(/,/g, "").trim();
const isAmount = (value) => /^\d+(\.\d{1,2})?$/.test(cleanAmount(value)) && Number(cleanAmount(value)) > 0;

// One-off charges (water, a repair the tenant caused, a deposit top-up).
// Monthly rent is invoiced by "Generate rent invoices" instead.
export default function ChargeDrawer({ tenantId: presetTenant, onClose, onSaved }) {
  const in14 = new Date();
  in14.setDate(in14.getDate() + 14);
  const [tenantId, setTenantId] = useState(presetTenant || "");
  const [dueDate, setDueDate] = useState(toIsoDate(in14));
  const [notes, setNotes] = useState("");
  const [lines, setLines] = useState([newLine()]);
  const { validate, clearError, fieldProps, showServerErrors } = useFormErrors();
  const tenantsQuery = useTenantsQuery({ page_size: 200, ordering: "full_name" }, { staleTime: 30_000 });
  const tenants = tenantsQuery.data?.results || [];
  const tenant = tenants.find((item) => item.id === tenantId);
  const total = lines.reduce((sum, line) => sum + (isAmount(line.amount) ? Number(cleanAmount(line.amount)) : 0), 0);

  const mutation = useSaveInvoiceMutation({
    onSuccess: (data) => {
      toast.success(`${data.reference} issued to ${data.tenant_name}.`);
      onSaved?.(data);
    },
    onError: (error) => {
      if (!showServerErrors(error.data, ["tenant", "due_date", "lines"])) toast.error(error.message || "Could not issue the charge.");
    },
  });

  const updateLine = (key, field, value) => {
    setLines((current) => current.map((line) => (line.key === key ? { ...line, [field]: value } : line)));
    clearError(`line.${key}.${field}`);
  };

  const submit = (event) => {
    event.preventDefault();
    if (mutation.isPending) return;
    const rules = {
      tenant: () => (tenantId ? "" : "Choose a tenant."),
      due_date: () => (dueDate ? "" : "Choose a due date."),
    };
    lines.forEach((line) => {
      rules[`line.${line.key}.description`] = () => (line.description.trim() ? "" : "Describe the charge.");
      rules[`line.${line.key}.amount`] = () => (isAmount(line.amount) ? "" : "Enter an amount.");
    });
    if (!validate(rules, event.currentTarget)) return;
    mutation.mutate({
      payload: {
        tenant: tenantId,
        lease: tenant?.current_lease?.status === "active" ? tenant.current_lease.id : null,
        due_date: dueDate,
        notes: notes.trim(),
        lines: lines.map(({ kind, description, amount }) => ({ kind, description: description.trim(), amount: cleanAmount(amount) })),
      },
    });
  };

  return (
    <OverlayDrawer open position="end" size="medium" className="dwella-drawer" onOpenChange={(_, data) => !data.open && !mutation.isPending && onClose()}>
      <DrawerHeader>
        <DrawerHeaderTitle action={<Button appearance="subtle" aria-label="Close" icon={<Dismiss24Regular />} disabled={mutation.isPending} onClick={onClose} />}>
          New charge
        </DrawerHeaderTitle>
        <p className="dwella-drawer-note">A one-off invoice. Monthly rent is billed with Generate rent invoices.</p>
      </DrawerHeader>
      <form id="charge-form" noValidate onSubmit={submit} className="dwella-drawer-form">
        <DrawerBody>
          <fieldset disabled={mutation.isPending}>
            <section className="dwella-form-section">
              <div className="dwella-form-grid">
                <Field label="Tenant" required {...fieldProps("tenant")}>
                  <Dropdown
                    placeholder={tenantsQuery.isLoading ? "Loading tenants…" : "Choose a tenant"}
                    disabled={tenantsQuery.isLoading}
                    selectedOptions={tenantId ? [tenantId] : []}
                    value={tenant?.full_name || ""}
                    onOptionSelect={(_, data) => {
                      setTenantId(data.optionValue);
                      clearError("tenant");
                    }}
                  >
                    {tenants.map((item) => (
                      <Option key={item.id} value={item.id} text={item.full_name}>{item.full_name}</Option>
                    ))}
                  </Dropdown>
                </Field>
                <Field label="Due date" required {...fieldProps("due_date")}>
                  <Input type="date" value={dueDate} min={toIsoDate(new Date())} onChange={(_, d) => { setDueDate(d.value); clearError("due_date"); }} />
                </Field>
              </div>
            </section>
            <section className="dwella-form-section">
              <h3>Charges</h3>
              {fieldProps("lines").validationMessage ? <p className="dwella-field-error">{fieldProps("lines").validationMessage}</p> : null}
              <div className="dwella-charge-lines">
                {lines.map((line, index) => (
                  <div className="dwella-charge-line" key={line.key}>
                    <Field label={index === 0 ? "Type" : undefined}>
                      <Dropdown
                        aria-label="Charge type"
                        selectedOptions={[line.kind]}
                        value={lineKinds.find((kind) => kind.value === line.kind)?.label}
                        onOptionSelect={(_, d) => updateLine(line.key, "kind", d.optionValue)}
                      >
                        {lineKinds.filter((kind) => kind.value !== "late_fee").map((kind) => (
                          <Option key={kind.value} value={kind.value}>{kind.label}</Option>
                        ))}
                      </Dropdown>
                    </Field>
                    <Field label={index === 0 ? "Description" : undefined} {...fieldProps(`line.${line.key}.description`)}>
                      <Input aria-label="Description" maxLength={200} placeholder="e.g. Water · October" value={line.description} onChange={(_, d) => updateLine(line.key, "description", d.value)} />
                    </Field>
                    <Field label={index === 0 ? "Amount" : undefined} {...fieldProps(`line.${line.key}.amount`)}>
                      <Input aria-label="Amount" inputMode="decimal" placeholder="0.00" value={line.amount} onChange={(_, d) => updateLine(line.key, "amount", d.value)} />
                    </Field>
                    <Button
                      appearance="subtle"
                      icon={<Delete20Regular />}
                      aria-label="Remove charge"
                      disabled={lines.length === 1}
                      onClick={() => setLines((current) => current.filter((item) => item.key !== line.key))}
                    />
                  </div>
                ))}
              </div>
              <div className="dwella-charge-total">
                <Button appearance="subtle" icon={<Add20Regular />} onClick={() => setLines((current) => [...current, newLine()])}>Add a charge</Button>
                <span>Total <strong>{formatMoney(total)}</strong></span>
              </div>
            </section>
            <section className="dwella-form-section">
              <Field label="Note for the tenant">
                <Textarea rows={2} value={notes} onChange={(_, d) => setNotes(d.value)} />
              </Field>
            </section>
          </fieldset>
        </DrawerBody>
      </form>
      <DrawerFooter className="dwella-drawer-footer">
        <Button onClick={onClose} disabled={mutation.isPending}>Cancel</Button>
        <Button appearance="primary" type="submit" form="charge-form" disabled={mutation.isPending}>
          {mutation.isPending ? "Issuing…" : "Issue invoice"}
        </Button>
      </DrawerFooter>
    </OverlayDrawer>
  );
}
