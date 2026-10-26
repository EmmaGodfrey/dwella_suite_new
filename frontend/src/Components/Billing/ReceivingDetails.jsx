import React, { useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { Button, Checkbox, Field, Input, Select } from "@fluentui/react-components";
import { toast } from "react-toastify";
import { useCurrentUserQuery } from "../../Services/queries";
import { useReceivingDetails, useSaveReceivingDetails } from "../../Services/payments";
import { getUserAccess } from "../../shared/access";
import { EmptyState, StatusBadge } from "../../shared/components";
import { FormDrawer } from "../../shared/components/FormFlow";
import { useFormErrors } from "../../shared/useFormErrors";
import "./receivingDetails.scss";

const networks = { mtn: "MTN Mobile Money", airtel: "Airtel Money", zamtel: "Zamtel Money" };
const fields = ["account_name", "operator", "phone", "confirm_details"];

function validPhone(value) {
  const phone = value.replace(/[\s()-]/g, "");
  return /^(?:0[79]\d{8}|\+?260[79]\d{8})$/.test(phone);
}

function ReceivingDrawer({ destination, onClose }) {
  const [form, setForm] = useState({
    account_name: destination?.account_name || "", operator: destination?.operator || "",
    phone: destination?.phone || "", confirm_details: false,
  });
  const [message, setMessage] = useState("");
  const mutation = useSaveReceivingDetails();
  const { errors, validate, clearError, fieldProps, showServerErrors } = useFormErrors();
  const change = (key, value) => {
    setForm((current) => ({ ...current, [key]: value }));
    clearError(key);
    // Any change requires the receiver to be confirmed again.
    if (key !== "confirm_details") setForm((current) => ({ ...current, confirm_details: false }));
    setMessage("");
  };
  const submit = async (event) => {
    event.preventDefault();
    if (mutation.isPending) return;
    if (!validate({
      account_name: () => form.account_name.trim().length < 2 ? "Enter the registered account-holder name." : "",
      operator: () => !networks[form.operator] ? "Choose a mobile network." : "",
      phone: () => !validPhone(form.phone) ? "Enter a valid Zambian mobile number." : "",
      confirm_details: () => !form.confirm_details ? "Confirm the receiving details." : "",
    }, event.currentTarget)) return;
    try {
      await mutation.mutateAsync({ ...form, account_name: form.account_name.trim(), phone: form.phone.trim() });
      toast.success("Receiving details saved.");
      onClose();
    } catch (error) {
      if (!showServerErrors(error.data, fields)) setMessage(error.message || "Could not save receiving details.");
    }
  };
  return <FormDrawer title="Receiving details" description="Choose the mobile-money wallet that should receive your rent."
    onClose={onClose} onSubmit={submit} busy={mutation.isPending} errors={errors}
    submitLabel="Save receiving details" pendingLabel="Saving details…">
    <div className="dwella-receiving-fields">
      {message && <p role="alert" className="dwella-alert danger">{message}</p>}
      <Field label="Account-holder name" required {...fieldProps("account_name")}>
        <Input value={form.account_name} maxLength={180} autoComplete="name"
          aria-invalid={Boolean(errors.account_name)} onChange={(_, data) => change("account_name", data.value)}
          placeholder="Full name registered on the wallet" />
      </Field>
      <Field label="Mobile network" required {...fieldProps("operator")}>
        <Select value={form.operator} aria-invalid={Boolean(errors.operator)} onChange={(_, data) => change("operator", data.value)}>
          <option value="">Choose a network</option>
          {Object.entries(networks).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
        </Select>
      </Field>
      <Field label="Receiving phone number" required {...fieldProps("phone")}>
        <Input value={form.phone} type="tel" inputMode="tel" maxLength={24} autoComplete="tel"
          aria-invalid={Boolean(errors.phone)} onChange={(_, data) => change("phone", data.value)} placeholder="e.g. 097 123 4567" />
      </Field>
      <p className="dwella-receiving-note">Use the landlord’s wallet or an authorised receiving account.</p>
      <Field {...fieldProps("confirm_details")}>
        <Checkbox checked={form.confirm_details} aria-invalid={Boolean(errors.confirm_details)}
          onChange={(_, data) => change("confirm_details", data.checked === true)}
          label="I have checked the name, network and number and confirm that this account may receive my rent." />
      </Field>
      <div className="dwella-receiving-timing"><h3>Payout timing</h3>
        <p>Rent is sent automatically after the payment settles. Network processing times and fees apply.</p>
      </div>
      {destination && <p className="dwella-receiving-note">These details apply to new payments. Payments already started keep their original receiving account.</p>}
    </div>
  </FormDrawer>;
}

export default function ReceivingDetails() {
  const user = useCurrentUserQuery();
  const allowed = getUserAccess(user.data).persona === "landlord";
  const query = useReceivingDetails({ enabled: allowed });
  const [editing, setEditing] = useState(false);
  if (user.isPending) return <p role="status">Loading receiving details…</p>;
  if (!allowed) return <Navigate to="/billing" replace />;
  const destination = query.data?.destination;
  return <div className="settings-stack">
    <section className="settings-section">
      <header><div><h2>Receiving account</h2><p>Where tenant rent is paid out after the payment settles.</p></div>
        {query.data?.self_service_enabled && <Button appearance="primary" onClick={() => setEditing(true)}>{destination ? "Edit receiving details" : "Add receiving details"}</Button>}
      </header>
      {query.isPending ? <p role="status">Loading receiving account…</p> : query.isError ? <EmptyState title="Could not load receiving details" description={query.error.message} actionLabel="Try again" onAction={() => query.refetch()} /> : <>
        <div className="settings-row"><div><strong>Status</strong></div><div><StatusBadge color={destination ? "success" : "warning"}>{destination ? "Active" : "Not added"}</StatusBadge></div></div>
        {[["Mobile network", destination ? networks[destination.operator] || destination.operator : "MTN, Airtel or Zamtel"], ["Account holder", destination?.account_name || "—"], ["Receiving number", destination?.phone || "—"], ["Payout timing", "Automatic after settlement"]].map(([label, value]) => <div className="settings-row" key={label}><div><strong>{label}</strong></div><div>{value}</div></div>)}
        {!query.data.self_service_enabled && <p className="settings-note">Receiving-number changes are unavailable until verification is configured for this environment.</p>}
        {query.data.self_service_enabled && !query.data.phone_verification_enabled && <p className="settings-note">Phone verification is off for this test. Saving receiving details does not verify ownership.</p>}
        {!query.data.collection_enabled && <p className="settings-note">Online collection is disabled in this environment.</p>}
      </>}
    </section>
    <section className="settings-section"><header><div><h2>Billing defaults</h2><p>Used when invoices are created in this workspace.</p></div><Button as={Link} to="/settings?tab=workspace">View workspace settings</Button></header><div className="settings-row"><div><strong>Currency</strong></div><div>{user.data?.memberships?.find(item => item.is_active && item.role === "landlord")?.organization?.currency || "ZMW"}</div></div></section>
    {editing && <ReceivingDrawer destination={destination} onClose={() => setEditing(false)} />}
  </div>;
}
