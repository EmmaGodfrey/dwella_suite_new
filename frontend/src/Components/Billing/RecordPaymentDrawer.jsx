import React, { useState } from "react";
import {
  Button,
  Dropdown,
  DrawerBody,
  DrawerFooter,
  DrawerHeader,
  DrawerHeaderTitle,
  Field,
  Input,
  Option,
  OverlayDrawer,
  Textarea,
} from "@fluentui/react-components";
import { Dismiss24Regular } from "@fluentui/react-icons";
import { toast } from "react-toastify";

import { useRecordPaymentMutation } from "../../Services/mutations";
import { paymentMethodLabel, paymentMethods } from "../../shared/billing";
import { formatMoney, toIsoDate } from "../../shared/format";
import { useFormErrors } from "../../shared/useFormErrors";

const FIELDS = ["amount", "method", "paid_on", "reference", "notes"];

// For money that reached the landlord outside Dwella: cash, a cheque, or a
// transfer without a reference. In-app payments record themselves.
export default function RecordPaymentDrawer({ invoice, onClose, onSaved }) {
  const balance = Number(invoice.balance);
  const [form, setForm] = useState({
    amount: balance.toFixed(2),
    method: "mobile_money",
    paid_on: toIsoDate(new Date()),
    reference: "",
    notes: "",
  });
  const { validate, clearError, fieldProps, showServerErrors } = useFormErrors();
  const mutation = useRecordPaymentMutation({
    onSuccess: (data) => {
      const receipt = data.recorded_payment?.receipt_number;
      toast.success(receipt ? `Payment recorded · ${receipt}` : "Payment recorded.");
      onSaved?.(data);
    },
    onError: (error) => {
      if (!showServerErrors(error.data, FIELDS)) toast.error(error.message || "Could not record the payment.");
    },
  });

  const update = (key, value) => {
    setForm((current) => ({ ...current, [key]: value }));
    clearError(key);
  };

  const submit = (event) => {
    event.preventDefault();
    if (mutation.isPending) return;
    const amount = Number(String(form.amount).replace(/,/g, ""));
    const ok = validate(
      {
        amount: () =>
          !/^\d+(\.\d{1,2})?$/.test(String(form.amount).replace(/,/g, "").trim()) || amount <= 0
            ? "Enter the amount received."
            : amount > balance
              ? `Only ${formatMoney(balance)} is owed on this invoice.`
              : "",
        paid_on: () => (!form.paid_on ? "Choose the date it was paid." : form.paid_on > toIsoDate(new Date()) ? "Payment date cannot be in the future." : ""),
      },
      event.currentTarget,
    );
    if (!ok) return;
    mutation.mutate({
      id: invoice.id,
      payload: { ...form, amount: amount.toFixed(2), reference: form.reference.trim(), notes: form.notes.trim() },
    });
  };

  return (
    <OverlayDrawer open position="end" size="small" className="dwella-drawer" onOpenChange={(_, data) => !data.open && !mutation.isPending && onClose()}>
      <DrawerHeader>
        <DrawerHeaderTitle action={<Button appearance="subtle" aria-label="Close" icon={<Dismiss24Regular />} disabled={mutation.isPending} onClick={onClose} />}>
          Record payment
        </DrawerHeaderTitle>
        <p className="dwella-drawer-note">
          {invoice.reference} · {invoice.tenant_name} · {formatMoney(balance)} owed
        </p>
      </DrawerHeader>
      <form id="payment-form" noValidate onSubmit={submit} className="dwella-drawer-form">
        <DrawerBody>
          <fieldset disabled={mutation.isPending}>
            <div className="dwella-form-grid is-single">
              <Field label="Amount received (ZMW)" required {...fieldProps("amount")}>
                <Input inputMode="decimal" value={form.amount} onChange={(_, d) => update("amount", d.value)} />
              </Field>
              <Field label="Paid by" required>
                <Dropdown
                  selectedOptions={[form.method]}
                  value={paymentMethodLabel(form.method)}
                  onOptionSelect={(_, d) => update("method", d.optionValue)}
                >
                  {paymentMethods.map((method) => (
                    <Option key={method.value} value={method.value}>{method.label}</Option>
                  ))}
                </Dropdown>
              </Field>
              <Field label="Date paid" required {...fieldProps("paid_on")}>
                <Input type="date" value={form.paid_on} max={toIsoDate(new Date())} onChange={(_, d) => update("paid_on", d.value)} />
              </Field>
              <Field label="Reference" hint="Transaction ID, bank reference or cheque number." {...fieldProps("reference")}>
                <Input maxLength={80} value={form.reference} onChange={(_, d) => update("reference", d.value)} />
              </Field>
              <Field label="Note" {...fieldProps("notes")}>
                <Textarea rows={2} value={form.notes} onChange={(_, d) => update("notes", d.value)} />
              </Field>
            </div>
          </fieldset>
        </DrawerBody>
      </form>
      <DrawerFooter className="dwella-drawer-footer">
        <Button onClick={onClose} disabled={mutation.isPending}>Cancel</Button>
        <Button appearance="primary" type="submit" form="payment-form" disabled={mutation.isPending}>
          {mutation.isPending ? "Recording…" : "Record payment"}
        </Button>
      </DrawerFooter>
    </OverlayDrawer>
  );
}
