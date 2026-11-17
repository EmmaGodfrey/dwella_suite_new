import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Button, Checkbox, Field, Input, Switch } from "@fluentui/react-components";
import { useSaveSetupMutation } from "../../Services/mutations";
import { useSettingsResource } from "../../Services/settings";
import { usePaymentInstructions } from "../../Services/payments";
import { useFormErrors } from "../../shared/useFormErrors";
import { FormPage, FormReview } from "../../shared/components/FormFlow";
import WhatsAppConnection from "../../shared/components/WhatsAppConnection";
import PaymentInstructions from "../Billing/PaymentInstructions";

const methodLabels = { bank: "Bank transfer", mobile_money: "Mobile money", cash: "Cash" };
const steps = ["Business", "How tenants pay", "Billing", "Review"];
const businessLimits = { business_name: 180, email: 254, phone_number: 40, address: 2000, town: 120, country: 80 };
const businessLabels = { business_name: "Business or property manager name", email: "Business email", phone_number: "Contact number", address: "Business address", town: "Town or city", country: "Country" };
const numberFields = { before_due_days: ["Remind before due (days)", 0, 30], due_hour: ["Send at (hour, 0–23)", 0, 23], overdue_every_days: ["Overdue reminder interval (days)", 1, 30], overdue_repeats: ["Maximum overdue reminders", 0, 3] };

export default function AccountSetup({ status, onComplete, onClose }) {
  const firstMissing = status.account_steps.findIndex(item => !item.done);
  const [step, setStep] = useState(firstMissing < 0 ? 0 : firstMissing);
  const [business, setBusiness] = useState({ ...status.business, email: status.business.email || status.email });
  const [methods, setMethods] = useState(status.payment_methods);
  const [billing, setBilling] = useState(status.billing);
  const [message, setMessage] = useState("");
  const instructions = usePaymentInstructions({ enabled: step === 1 && !status.needs_setup });
  const reminderQuery = useSettingsResource("reminders", { enabled: step === 2 && !status.needs_setup });
  const { errors, validate, fieldProps, clearError, clearAll, showServerErrors } = useFormErrors();
  const save = useSaveSetupMutation();
  const changeBusiness = (key, value) => {
    setBusiness(current => ({ ...current, [key]: value })); clearError(key); setMessage("");
  };
  const changeReminder = (key, value) => {
    setBilling(current => ({ ...current, reminders: { ...current.reminders, [key]: value } }));
    clearError(`reminders.${key}`); setMessage("");
  };
  const go = (value) => { setStep(value); clearAll(); setMessage(""); };
  const submit = async (event) => {
    event.preventDefault();
    if (save.isPending) return;
    const rules = step === 0 ? {
      ...Object.fromEntries(Object.entries(businessLimits).map(([key, limit]) => [key, () => !business[key]?.trim() || business[key].trim().length > limit ? `Enter ${businessLabels[key].toLowerCase()} (up to ${limit} characters).` : ""])),
      email: () => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(business.email) ? "" : "Enter a valid business email.",
      phone_number: () => /^\+?[0-9 ()-]{7,40}$/.test(business.phone_number) ? "" : "Enter a valid contact number.",
      confirm_region: () => business.confirm_region ? "" : "Confirm the currency and time zone.",
    } : step === 1 ? {
      payment_methods: () => !methods.length ? "Choose at least one way tenants can pay." : instructions.isPending || instructions.isError ? "Wait for your payment details to load, or retry." : methods.some(kind => kind !== "cash" && !instructions.data?.some(item => item.kind === kind)) ? "Add payment details for each selected bank or mobile-money method." : instructions.data?.some(item => !methods.includes(item.kind)) ? "Select your saved payment methods, or remove their details first." : "",
    } : step === 2 ? {
      invoice_lead_days: () => /^\d+$/.test(String(billing.invoice_lead_days)) && Number(billing.invoice_lead_days) <= 28 ? "" : "Enter 0 to 28 days.",
      ...Object.fromEntries(Object.entries(numberFields).map(([key, [, min, max]]) => [`reminders.${key}`, () => /^\d+$/.test(String(billing.reminders[key])) && Number(billing.reminders[key]) >= min && Number(billing.reminders[key]) <= max ? "" : `Enter ${min} to ${max}.`])),
    } : {};
    if (!validate(rules, event.currentTarget)) return;
    const stage = ["business", "payments", "billing", "complete"][step];
    const body = step === 0 ? Object.fromEntries(Object.entries(business).map(([key, value]) => [key, typeof value === "string" ? value.trim() : value])) : step === 1 ? { payment_methods: methods } : step === 2 ? billing : {};
    setMessage("");
    try {
      const result = await save.mutateAsync({ stage, ...body });
      if (step === 3) onComplete(result);
      else go(step + 1);
    } catch (error) {
      showServerErrors(error.data, [...Object.keys(businessLimits), "confirm_region", "payment_methods", "invoice_lead_days", ...Object.keys(numberFields).map(key => `reminders.${key}`)]);
      setMessage(error.message || "Could not save this step. Your entries are kept.");
    }
  };
  const reminders = billing.reminders;
  return <>
    <FormPage title="Get your account ready" description="Set up your business and how tenants pay before adding your portfolio. Each step is saved when you continue."
      steps={steps} step={step} stepTitle={steps[step]} onSubmit={submit} onBack={() => go(step - 1)} onClose={onClose}
      submitLabel="Finish account setup" pendingLabel="Saving…" busy={save.isPending} errors={errors}
      notice={message && <p role="alert" className="dwella-alert danger">{message}</p>}>
      {step === 0 && <div className="dwella-form-grid">
        {Object.entries(businessLimits).map(([key, limit]) => <Field key={key} label={businessLabels[key]} required {...fieldProps(key)} className={key === "address" ? "dwella-field-wide" : undefined}>
          <Input name={key} value={business[key]} maxLength={limit} type={key === "email" ? "email" : key === "phone_number" ? "tel" : "text"} onChange={(_, data) => changeBusiness(key, data.value)} />
        </Field>)}
        <p className="dwella-field-wide dwella-muted-copy">Your business details appear on invoices and receipts. Currency: {status.currency}. Time zone: {status.timezone}.</p>
        <Field {...fieldProps("confirm_region")} className="dwella-field-wide">
          <Checkbox checked={business.confirm_region} label={`I have checked the currency (${status.currency}) and time zone (${status.timezone}).`} onChange={(_, data) => changeBusiness("confirm_region", data.checked === true)} />
        </Field>
        <p className="dwella-field-wide dwella-muted-copy">Review your <Link to="/settings?tab=account">personal profile</Link> and <Link to="/settings?tab=security">account security</Link>. Email verification and required security checks still apply.</p>
      </div>}
      {step === 1 && <div className="dwella-setup-account-section">
        <p>Choose every method you accept. You can use cash only, or combine cash with bank transfers and mobile money.</p>
        <fieldset className="dwella-setup-payment-choice" aria-describedby={errors.payment_methods ? "setup-payment-error" : undefined}>
          <legend>Accepted payment methods (choose at least one)</legend>
          <div className="dwella-setup-methods">{Object.entries(methodLabels).map(([key, label]) => <Checkbox key={key} label={label} checked={methods.includes(key)} onChange={(_, data) => { setMethods(current => data.checked ? [...current, key] : current.filter(value => value !== key)); clearError("payment_methods"); }} />)}</div>
          {errors.payment_methods && <p id="setup-payment-error" role="alert" className="dwella-alert danger">{errors.payment_methods}</p>}
        </fieldset>
        <PaymentInstructions required={methods.filter((kind) => kind !== "cash")} />
        {methods.includes("cash") && <p className="dwella-muted-copy">Record cash received in Dwella. A tenant can also report a cash payment through WhatsApp; a manager must confirm receipt before it changes the balance.</p>}
        <p className="dwella-muted-copy">These details tell tenants how to pay you directly. A Dwella withdrawal receiving account is separate and is not required for manual payments.</p>
      </div>}
      {step === 2 && <div className="dwella-setup-account-section">
        <Field label="Automatic rent invoices"><Switch checked={billing.auto_invoice} label={billing.auto_invoice ? "Requested" : "Off"} onChange={(_, data) => setBilling(current => ({ ...current, auto_invoice: data.checked }))} /></Field>
        <Field label="Create invoices before due (days)" required {...fieldProps("invoice_lead_days")}><Input type="number" min={0} max={28} value={String(billing.invoice_lead_days)} onChange={(_, data) => { setBilling(current => ({ ...current, invoice_lead_days: data.value })); clearError("invoice_lead_days"); }} /></Field>
        <p className="dwella-muted-copy">Automatic billing also depends on Dwella enabling scheduled billing. Saving this step does not create an invoice or send a message.</p>
        <h3>Rent reminders</h3>
        {reminderQuery.isPending ? <p role="status">Checking message availability…</p> : reminderQuery.isError ? <p role="alert">Could not check message availability. Your preferences can still be saved. <Button onClick={() => reminderQuery.refetch()}>Retry</Button></p> : <p className="dwella-muted-copy">Delivery available: {Object.entries(reminderQuery.data?.channels || {}).filter(([, available]) => available).map(([channel]) => channel === "whatsapp" ? "WhatsApp" : channel).join(", ") || "none currently"}. Preferences are separate from availability.</p>}
        <Field label="Email reminders"><Switch checked={reminders.email_enabled} onChange={(_, data) => changeReminder("email_enabled", data.checked)} /></Field>
        <Field label="WhatsApp reminders" hint="Only opted-in tenants can receive WhatsApp reminders, when the channel is available."><Switch checked={reminders.whatsapp_enabled} onChange={(_, data) => changeReminder("whatsapp_enabled", data.checked)} /></Field>
        <p className="dwella-muted-copy">SMS remains subject to sender approval and platform availability. You can review it later in Notifications.</p>
        <div className="dwella-form-grid">{Object.entries(numberFields).map(([key, [label, min, max]]) => <Field key={key} label={label} required {...fieldProps(`reminders.${key}`)}>
          <Input name={`reminders.${key}`} type="number" min={min} max={max} value={String(reminders[key])} onChange={(_, data) => changeReminder(key, data.value)} />
        </Field>)}</div>
      </div>}
      {step === 3 && <div className="dwella-setup-account-section">
        <FormReview items={[
          { label: "Business", value: business.business_name, step: 0 },
          { label: "Business address", value: `${business.address}, ${business.town}, ${business.country}`, step: 0 },
          { label: "Contact", value: `${business.email} · ${business.phone_number}`, step: 0 },
          { label: "Currency and time zone", value: `${status.currency} · ${status.timezone}`, step: 0 },
          { label: "How tenants pay", value: methods.map(key => methodLabels[key]).join(", "), step: 1 },
          { label: "Automatic invoices", value: billing.auto_invoice ? `${billing.invoice_lead_days} days before due, when scheduled billing is enabled` : "Off", step: 2 },
          { label: "Reminders requested", value: [reminders.email_enabled && "Email", reminders.whatsapp_enabled && "WhatsApp (opted-in tenants)"].filter(Boolean).join(", ") || "None", step: 2 },
        ]} onEdit={go} />
        <p>Next, add your properties and units, then tenants and leases. You choose when to create the first invoice and invite tenants.</p>
      </div>}
    </FormPage>
    {step === 3 && <div className="dwella-setup-optional"><WhatsAppConnection onboarding /></div>}
  </>;
}
