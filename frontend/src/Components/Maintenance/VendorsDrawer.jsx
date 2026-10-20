import React, { useState } from "react";
import {
  Button,
  DrawerBody,
  DrawerHeader,
  DrawerHeaderTitle,
  Field,
  Input,
  OverlayDrawer,
} from "@fluentui/react-components";
import { Add20Regular, Archive20Regular, Dismiss24Regular, Edit20Regular } from "@fluentui/react-icons";
import { toast } from "react-toastify";

import { useArchiveVendorMutation, useSaveVendorMutation } from "../../Services/mutations";
import { useVendorsQuery } from "../../Services/queries";
import { initials } from "../../shared/format";
import { useFormErrors } from "../../shared/useFormErrors";

const blank = { name: "", trade: "", contact_name: "", phone_number: "", email: "" };
const looksLikeEmail = (value) => !value || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
const looksLikePhone = (value) => !value || /^\+?[\d\s-]{7,20}$/.test(value);

function VendorForm({ vendor, onDone }) {
  const [form, setForm] = useState(vendor ? { ...blank, ...vendor } : blank);
  const { validate, clearError, fieldProps, showServerErrors } = useFormErrors();
  const mutation = useSaveVendorMutation({
    onSuccess: (data) => {
      toast.success(vendor ? `${data.name} updated.` : `${data.name} added.`);
      onDone();
    },
    onError: (error) => {
      if (!showServerErrors(error.data, Object.keys(blank))) toast.error(error.message || "Could not save the vendor.");
    },
  });
  const update = (key, value) => {
    setForm((current) => ({ ...current, [key]: value }));
    clearError(key);
  };
  const submit = (event) => {
    event.preventDefault();
    if (mutation.isPending) return;
    const ok = validate({
      name: () => (form.name.trim() ? "" : "Enter the vendor's name."),
      phone_number: () => (looksLikePhone(form.phone_number.trim()) ? "" : "Enter a valid phone number."),
      email: () => (looksLikeEmail(form.email.trim()) ? "" : "Enter a valid email address."),
    }, event.currentTarget);
    if (!ok) return;
    const payload = Object.fromEntries(Object.keys(blank).map((key) => [key, form[key].trim()]));
    mutation.mutate({ id: vendor?.id, payload });
  };
  return (
    <form noValidate onSubmit={submit} className="dwella-vendor-form">
      <fieldset disabled={mutation.isPending}>
        <div className="dwella-form-grid">
          <Field label="Business name" required {...fieldProps("name")}>
            <Input maxLength={180} value={form.name} onChange={(_, d) => update("name", d.value)} />
          </Field>
          <Field label="Trade" {...fieldProps("trade")}>
            <Input maxLength={80} placeholder="e.g. Plumbing" value={form.trade} onChange={(_, d) => update("trade", d.value)} />
          </Field>
          <Field label="Contact person" {...fieldProps("contact_name")}>
            <Input maxLength={180} value={form.contact_name} onChange={(_, d) => update("contact_name", d.value)} />
          </Field>
          <Field label="Phone" {...fieldProps("phone_number")}>
            <Input type="tel" maxLength={20} placeholder="+260 97…" value={form.phone_number} onChange={(_, d) => update("phone_number", d.value)} />
          </Field>
          <Field label="Email" {...fieldProps("email")}>
            <Input type="email" value={form.email} onChange={(_, d) => update("email", d.value)} />
          </Field>
        </div>
        <div className="dwella-vendor-form-actions">
          <Button onClick={onDone}>Cancel</Button>
          <Button appearance="primary" type="submit">{mutation.isPending ? "Saving…" : vendor ? "Save vendor" : "Add vendor"}</Button>
        </div>
      </fieldset>
    </form>
  );
}

export default function VendorsDrawer({ onClose }) {
  const [editing, setEditing] = useState(null); // null | "new" | vendor
  const vendorsQuery = useVendorsQuery({ page_size: 200, is_active: "true", ordering: "name" });
  const vendors = vendorsQuery.data?.results || [];
  const archive = useArchiveVendorMutation({
    onSuccess: () => toast.success("Vendor removed."),
    onError: (error) => toast.error(error.message || "Could not remove the vendor."),
  });

  return (
    <OverlayDrawer open position="end" size="medium" className="dwella-drawer" onOpenChange={(_, data) => !data.open && onClose()}>
      <DrawerHeader>
        <DrawerHeaderTitle action={<Button appearance="subtle" aria-label="Close" icon={<Dismiss24Regular />} onClick={onClose} />}>
          Vendors
        </DrawerHeaderTitle>
        <p className="dwella-drawer-note">The contractors you send work to. Removing one keeps their past jobs on record.</p>
      </DrawerHeader>
      <DrawerBody>
        {editing ? (
          <VendorForm key={editing === "new" ? "new" : editing.id} vendor={editing === "new" ? null : editing} onDone={() => setEditing(null)} />
        ) : (
          <Button icon={<Add20Regular />} onClick={() => setEditing("new")}>Add vendor</Button>
        )}
        {vendorsQuery.isLoading ? <span className="dwella-skeleton" style={{ height: 120, marginTop: 16 }} /> : null}
        {!vendorsQuery.isLoading && !vendors.length && !editing ? (
          <p className="dwella-muted-copy dwella-vendor-empty">No vendors yet. Add the plumbers, electricians and handymen you use.</p>
        ) : null}
        <ul className="dwella-vendor-list">
          {vendors.map((vendor) => (
            <li key={vendor.id}>
              <span className="dwella-avatar is-navy" aria-hidden="true">{initials(vendor.name)}</span>
              <div>
                <strong>{vendor.name}</strong>
                <small>{[vendor.trade, vendor.contact_name, vendor.phone_number].filter(Boolean).join(" · ") || "No contact details"}</small>
              </div>
              <small className="dwella-vendor-jobs">{vendor.open_jobs ? `${vendor.open_jobs} open` : ""}</small>
              <Button appearance="subtle" aria-label={`Edit ${vendor.name}`} icon={<Edit20Regular />} onClick={() => setEditing(vendor)} />
              <Button
                appearance="subtle"
                aria-label={`Remove ${vendor.name}`}
                icon={<Archive20Regular />}
                disabled={archive.isPending}
                onClick={() => archive.mutate({ id: vendor.id })}
              />
            </li>
          ))}
        </ul>
      </DrawerBody>
    </OverlayDrawer>
  );
}
