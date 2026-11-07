import React, { useState } from "react";
import { Button, Field, Input, Radio, RadioGroup, Select } from "@fluentui/react-components";
import { toast } from "react-toastify";
import {
  usePaymentInstructions,
  useRemovePaymentInstruction,
  useSavePaymentInstruction,
} from "../../Services/payments";
import { EmptyState } from "../../shared/components";
import { FormDrawer } from "../../shared/components/FormFlow";
import { networks } from "../../shared/payouts";
import { useFormErrors } from "../../shared/useFormErrors";

const MAX = 3;
const fields = ["kind", "account_name", "bank_name", "branch", "account_number", "network", "phone", "note"];
const blank = { kind: "bank", account_name: "", bank_name: "", branch: "", account_number: "", network: "", phone: "", note: "" };

function summary(item) {
  return item.kind === "bank"
    ? `${item.bank_name}${item.branch ? `, ${item.branch}` : ""} · ${item.account_number} · ${item.account_name}`
    : `${networks[item.network] || item.network} · ${item.phone} · ${item.account_name}`;
}

function InstructionDrawer({ item, onClose }) {
  const [form, setForm] = useState({ ...blank, ...item });
  const [message, setMessage] = useState("");
  const save = useSavePaymentInstruction();
  const { errors, validate, clearError, fieldProps, showServerErrors } = useFormErrors();
  const bank = form.kind === "bank";
  const change = (key, value) => {
    setForm((current) => ({ ...current, [key]: value }));
    clearError(key);
    setMessage("");
  };
  const submit = async (event) => {
    event.preventDefault();
    if (save.isPending) return;
    const rules = {
      account_name: () => form.account_name.trim().length < 2 ? "Enter the name on the account." : "",
      ...(bank ? {
        bank_name: () => !form.bank_name.trim() ? "Enter the bank." : "",
        account_number: () => !/^\d{6,20}$/.test(form.account_number.replace(/\s/g, "")) ? "Enter the account number using digits only." : "",
      } : {
        network: () => !networks[form.network] ? "Choose the mobile network." : "",
        phone: () => !/^(?:0[79]\d{8}|\+?260[79]\d{8})$/.test(form.phone.replace(/[\s()-]/g, "")) ? "Enter a valid Zambian mobile number." : "",
      }),
    };
    if (!validate(rules, event.currentTarget)) return;
    const data = Object.fromEntries(fields.map((key) => [key, form[key]]));
    try {
      await save.mutateAsync({ id: item?.id, ...data });
      toast.success("Payment details saved. New invoices will show them.");
      onClose();
    } catch (error) {
      if (!showServerErrors(error.data, fields)) setMessage(error.message || "Could not save these details.");
    }
  };
  return <FormDrawer title={item ? "Edit payment details" : "Add payment details"}
    description="Printed under “How to pay” on every invoice you send."
    onClose={onClose} onSubmit={submit} busy={save.isPending} errors={errors}
    submitLabel="Save details" pendingLabel="Saving…">
    <div className="dwella-receiving-fields">
      {message && <p role="alert" className="dwella-alert danger">{message}</p>}
      <Field label="How tenants pay" {...fieldProps("kind")}>
        <RadioGroup layout="horizontal" value={form.kind} onChange={(_, d) => change("kind", d.value)}>
          <Radio value="bank" label="Bank transfer" />
          <Radio value="mobile_money" label="Mobile money" />
        </RadioGroup>
      </Field>
      {bank ? <>
        <Field label="Bank" required {...fieldProps("bank_name")}>
          <Input value={form.bank_name} maxLength={120} onChange={(_, d) => change("bank_name", d.value)} placeholder="e.g. Zanaco" />
        </Field>
        <Field label="Branch" {...fieldProps("branch")}>
          <Input value={form.branch} maxLength={120} onChange={(_, d) => change("branch", d.value)} />
        </Field>
        <Field label="Account number" required {...fieldProps("account_number")}>
          <Input value={form.account_number} inputMode="numeric" maxLength={34} onChange={(_, d) => change("account_number", d.value)} />
        </Field>
      </> : <>
        <Field label="Mobile network" required {...fieldProps("network")}>
          <Select value={form.network} onChange={(_, d) => change("network", d.value)}>
            <option value="">Choose a network</option>
            {Object.entries(networks).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </Select>
        </Field>
        <Field label="Phone number" required {...fieldProps("phone")}>
          <Input value={form.phone} type="tel" inputMode="tel" maxLength={24} onChange={(_, d) => change("phone", d.value)} placeholder="e.g. 097 123 4567" />
        </Field>
      </>}
      <Field label={bank ? "Account name" : "Registered name"} required {...fieldProps("account_name")}>
        <Input value={form.account_name} maxLength={120} onChange={(_, d) => change("account_name", d.value)} />
      </Field>
      <Field label="Note for tenants" hint="Optional, e.g. “Use your unit number as the reference.”" {...fieldProps("note")}>
        <Input value={form.note} maxLength={200} onChange={(_, d) => change("note", d.value)} />
      </Field>
      <p className="dwella-receiving-note">Check these carefully: tenants will send money here. Invoices already saved keep the details they were issued with until the invoice changes.</p>
    </div>
  </FormDrawer>;
}

export default function PaymentInstructions() {
  const query = usePaymentInstructions();
  const remove = useRemovePaymentInstruction();
  const [editing, setEditing] = useState(null); // null | {} (new) | item
  const items = query.data || [];
  return <section className="settings-section">
    <header>
      <div><h2>How tenants pay you</h2><p>Bank or mobile money details printed on every invoice, next to the Dwella online payment option.</p></div>
      {items.length < MAX && !query.isPending && !query.isError &&
        <Button appearance="primary" onClick={() => setEditing({})}>Add payment details</Button>}
    </header>
    {query.isPending ? <p role="status">Loading payment details…</p>
      : query.isError ? <EmptyState title="Could not load payment details" description={query.error.message} actionLabel="Try again" onAction={() => query.refetch()} />
        : !items.length ? <p className="settings-note">No details yet. Invoices will ask tenants to use the payment details you give them.</p>
          : items.map((item) => <div className="settings-row" key={item.id}>
            <div><strong>{item.kind === "bank" ? "Bank transfer" : "Mobile money"}</strong></div>
            <div>{summary(item)}{item.note ? <><br /><small>{item.note}</small></> : null}</div>
            <div>
              <Button size="small" onClick={() => setEditing(item)}>Edit</Button>{" "}
              <Button size="small" appearance="subtle" disabled={remove.isPending}
                onClick={async () => {
                  try {
                    await remove.mutateAsync(item.id);
                    toast.success("Payment details removed.");
                  } catch (error) {
                    toast.error(error.message || "Could not remove these details.");
                  }
                }}>Remove</Button>
            </div>
          </div>)}
    {editing && <InstructionDrawer item={editing.id ? editing : null} onClose={() => setEditing(null)} />}
  </section>;
}
