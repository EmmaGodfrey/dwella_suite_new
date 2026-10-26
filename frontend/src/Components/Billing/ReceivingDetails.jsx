import React, { useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { Button, Checkbox, Field, Input, Radio, RadioGroup, Select } from "@fluentui/react-components";
import { toast } from "react-toastify";
import { useCurrentUserQuery } from "../../Services/queries";
import { useBanks, useCheckReceivingAccount, useReceivingDetails, useSaveReceivingDetails } from "../../Services/payments";
import { getUserAccess } from "../../shared/access";
import { EmptyState, StatusBadge } from "../../shared/components";
import { FormDrawer } from "../../shared/components/FormFlow";
import { networks } from "../../shared/payouts";
import { useFormErrors } from "../../shared/useFormErrors";
import "./receivingDetails.scss";

const fields = ["kind", "operator", "phone", "bank_id", "account_number", "account_name", "confirm_details", "password", "code"];
const detailKeys = ["kind", "operator", "phone", "bank_id", "account_number"];

function validPhone(value) {
  const phone = value.replace(/[\s()-]/g, "");
  return /^(?:0[79]\d{8}|\+?260[79]\d{8})$/.test(phone);
}

const details = (form) => form.kind === "bank-account"
  ? { kind: form.kind, bank_id: form.bank_id, account_number: form.account_number.replace(/\s/g, "") }
  : { kind: form.kind, operator: form.operator, phone: form.phone.trim() };

export function ReceivingDrawer({ destination, onClose }) {
  const user = useCurrentUserQuery();
  const twoFactor = Boolean(user.data?.has_two_factor);
  const settings = useReceivingDetails();
  const bypass = Boolean(settings.data?.lookup_bypass);
  const [form, setForm] = useState({
    kind: destination?.kind || "mobile-money", operator: destination?.operator || "", phone: "",
    bank_id: "", account_number: "", account_name: "", confirm_details: false, password: "", code: "",
  });
  const [lookup, setLookup] = useState(null); // null | { found: true|false|null, account_name, detail }
  const [message, setMessage] = useState("");
  const banks = useBanks({ enabled: form.kind === "bank-account" });
  const check = useCheckReceivingAccount();
  const mutation = useSaveReceivingDetails();
  const { errors, validate, clearError, fieldProps, showServerErrors } = useFormErrors();
  const bank = form.kind === "bank-account";

  const change = (key, value) => {
    setForm((current) => ({
      ...current, [key]: value,
      // New account details must be checked and confirmed again.
      ...(detailKeys.includes(key) ? { confirm_details: false } : {}),
    }));
    if (detailKeys.includes(key)) setLookup(null);
    clearError(key);
    setMessage("");
  };
  const detailRules = bank ? {
    bank_id: () => !form.bank_id ? "Choose the bank." : "",
    account_number: () => !/^\d{6,20}$/.test(form.account_number.replace(/\s/g, "")) ? "Enter the account number using digits only." : "",
  } : {
    operator: () => !networks[form.operator] ? "Choose a mobile network." : "",
    phone: () => !validPhone(form.phone) ? "Enter a valid Zambian mobile number." : "",
  };
  const runCheck = async () => {
    if (check.isPending || !validate(detailRules)) return;
    setMessage("");
    try {
      setLookup(await check.mutateAsync(details(form)));
    } catch (error) {
      if (!showServerErrors(error.data, fields)) setMessage(error.message || "Could not check this account.");
    }
  };
  const submit = async (event) => {
    event.preventDefault();
    if (mutation.isPending) return;
    if (!validate({
      ...detailRules,
      account_name: () => lookup?.found === null && form.account_name.trim().length < 2 ? "Enter the registered account-holder name." : "",
      confirm_details: () => !form.confirm_details ? "Confirm the receiving account." : "",
      password: () => !form.password ? "Enter your password." : "",
      code: () => twoFactor && !/^\d{6}$/.test(form.code) ? "Enter the 6-digit code from your authenticator app." : "",
    }, event.currentTarget)) return;
    if (!lookup?.found && lookup?.found !== null) {
      setMessage("Check the account with Lenco before saving.");
      return;
    }
    try {
      await mutation.mutateAsync({
        ...details(form), confirm_details: true, password: form.password,
        ...(twoFactor ? { code: form.code } : {}),
        ...(lookup.found === null ? { account_name: form.account_name.trim() } : {}),
      });
      toast.success("Receiving account saved.");
      onClose();
    } catch (error) {
      if (!showServerErrors(error.data, fields)) setMessage(error.message || "Could not save the receiving account.");
    }
  };
  const ready = lookup?.found === true || lookup?.found === null;
  return <FormDrawer title="Receiving account" description="Where your withdrawals are sent."
    onClose={onClose} onSubmit={submit} busy={mutation.isPending} errors={errors}
    submitLabel="Save receiving account" pendingLabel="Saving…">
    <div className="dwella-receiving-fields">
      {message && <p role="alert" className="dwella-alert danger">{message}</p>}
      <Field label="Account type" {...fieldProps("kind")}>
        <RadioGroup layout="horizontal" value={form.kind} onChange={(_, data) => change("kind", data.value)}>
          <Radio value="mobile-money" label="Mobile money" />
          <Radio value="bank-account" label="Bank account" />
        </RadioGroup>
      </Field>
      {bank ? <>
        <Field label="Bank" required {...fieldProps("bank_id")}>
          <Select value={form.bank_id} aria-invalid={Boolean(errors.bank_id)} disabled={banks.isLoading}
            onChange={(_, data) => change("bank_id", data.value)}>
            <option value="">{banks.isLoading ? "Loading banks…" : "Choose your bank"}</option>
            {(banks.data?.results || []).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </Select>
        </Field>
        {banks.isError && <p role="alert" className="dwella-receiving-note">Could not load banks. <Button size="small" onClick={() => banks.refetch()}>Retry</Button></p>}
        <Field label="Account number" required {...fieldProps("account_number")}>
          <Input value={form.account_number} inputMode="numeric" maxLength={24} aria-invalid={Boolean(errors.account_number)}
            onChange={(_, data) => change("account_number", data.value)} placeholder="Enter the bank account number" />
        </Field>
      </> : <>
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
      </>}
      <Button className="dwella-receiving-check" onClick={runCheck} disabled={check.isPending}>
        {check.isPending ? "Checking with Lenco…" : "Check account"}
      </Button>
      {lookup?.found === true && <div className="dwella-receiving-result is-found" role="status">
        <strong>Lenco found this account</strong>
        <span>{lookup.account_name}{lookup.bank_name ? ` · ${lookup.bank_name}` : ""}</span>
      </div>}
      {lookup?.found === false && <div className="dwella-receiving-result is-missing" role="alert">
        <strong>Lenco could not find this account</strong>
        <span>Check the {bank ? "bank and account number" : "network and number"}, then check again.</span>
      </div>}
      {lookup?.found === null && <>
        <div className="dwella-receiving-result" role="status">
          <strong>Lenco could not be asked</strong>
          <span>In this test environment you can enter the registered name yourself.</span>
        </div>
        <Field label="Account-holder name" required {...fieldProps("account_name")}>
          <Input value={form.account_name} maxLength={180} autoComplete="name" aria-invalid={Boolean(errors.account_name)}
            onChange={(_, data) => change("account_name", data.value)} placeholder="Full name registered on the account" />
        </Field>
      </>}
      {ready && <>
        <Field {...fieldProps("confirm_details")}>
          <Checkbox checked={form.confirm_details} aria-invalid={Boolean(errors.confirm_details)}
            onChange={(_, data) => change("confirm_details", data.checked === true)}
            label="This account belongs to me, or to someone I authorise to receive my rent." />
        </Field>
        <Field label="Your password" required hint="Needed to change where your rent is sent." {...fieldProps("password")}>
          <Input type="password" value={form.password} autoComplete="current-password" aria-invalid={Boolean(errors.password)}
            onChange={(_, data) => change("password", data.value)} />
        </Field>
        {twoFactor && <Field label="Authenticator code" required {...fieldProps("code")}>
          <Input value={form.code} inputMode="numeric" autoComplete="one-time-code" maxLength={6} aria-invalid={Boolean(errors.code)}
            onChange={(_, data) => change("code", data.value.replace(/\D/g, ""))} />
        </Field>}
      </>}
      <p className="dwella-receiving-note">
        {bank ? "Bank withdrawals can take until the next working day. " : ""}
        Withdrawals already sent keep their original account. We email you whenever this account changes.
      </p>
    </div>
  </FormDrawer>;
}

function accountRows(destination) {
  if (!destination) return [["Account", "—"], ["Account holder", "—"]];
  const bank = destination.kind === "bank-account";
  return [
    ["Type", bank ? "Bank account" : "Mobile money"],
    [bank ? "Bank" : "Mobile network", bank ? destination.bank_name : networks[destination.operator] || destination.operator],
    ["Account holder", destination.account_name],
    [bank ? "Account number" : "Receiving number", bank ? `Ending ${destination.account_suffix}` : destination.phone],
  ];
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
      <header><div><h2>Receiving account</h2><p>Where your rent is sent when you withdraw it.</p></div>
        {query.data?.self_service_enabled && <Button appearance="primary" onClick={() => setEditing(true)}>{destination ? "Change receiving account" : "Add receiving account"}</Button>}
      </header>
      {query.isPending ? <p role="status">Loading receiving account…</p> : query.isError ? <EmptyState title="Could not load receiving details" description={query.error.message} actionLabel="Try again" onAction={() => query.refetch()} /> : <>
        <div className="settings-row"><div><strong>Status</strong></div><div>
          <StatusBadge color={destination ? "success" : "warning"}>{destination ? destination.checked_with_lenco ? "Active · checked with Lenco" : "Active" : "Not added"}</StatusBadge>
        </div></div>
        {accountRows(destination).map(([label, value]) => <div className="settings-row" key={label}><div><strong>{label}</strong></div><div>{value}</div></div>)}
        <div className="settings-row"><div><strong>Withdrawals</strong></div><div>You choose when. <Link to="/billing/payouts">Open Payouts</Link></div></div>
        {!query.data.self_service_enabled && <p className="settings-note">Receiving accounts cannot be changed until Lenco is configured for this environment.</p>}
        {!query.data.collection_enabled && <p className="settings-note">Online collection is disabled in this environment.</p>}
      </>}
    </section>
    <section className="settings-section"><header><div><h2>Billing defaults</h2><p>Used when invoices are created in this workspace.</p></div><Button as={Link} to="/settings?tab=workspace">View workspace settings</Button></header><div className="settings-row"><div><strong>Currency</strong></div><div>{user.data?.memberships?.find(item => item.is_active && item.role === "landlord")?.organization?.currency || "ZMW"}</div></div></section>
    {editing && <ReceivingDrawer destination={destination} onClose={() => setEditing(false)} />}
  </div>;
}
