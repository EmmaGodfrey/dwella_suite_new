import React, { useState } from "react";
import { Field, Input } from "@fluentui/react-components";
import { toast } from "react-toastify";

import { useRenewLeaseMutation } from "../../Services/mutations";
import { FormDrawer } from "../../shared/components/FormFlow";
import { formatDate, formatMoney, parseDate, toIsoDate } from "../../shared/format";
import { leaseRules } from "../../shared/tenancy";
import { useFormErrors } from "../../shared/useFormErrors";

const FIELDS = [
  "end_date", "monthly_rent", "deposit_amount", "rent_due_day",
  "late_fee_percent", "late_fee_grace_days", "notice_period_months",
];

const addDays = (iso, days) => {
  const date = parseDate(iso);
  date.setDate(date.getDate() + days);
  return toIsoDate(date);
};
const nextYear = (iso) => {
  const date = parseDate(iso);
  date.setFullYear(date.getFullYear() + 1);
  return toIsoDate(date);
};
const plain = (value) => String(value ?? "").replace(/,/g, "").trim();

// The renewal starts the day after this lease ends, so the drawer only asks
// for the new end date and any terms that change.
export default function RenewLeaseDrawer({ lease, onClose, onSaved }) {
  const startDate = addDays(lease.end_date, 1);
  const [form, setForm] = useState(() => ({
    end_date: nextYear(lease.end_date),
    monthly_rent: String(Number(lease.monthly_rent)),
    deposit_amount: String(Number(lease.deposit_amount)),
    rent_due_day: String(lease.rent_due_day),
    late_fee_percent: String(Number(lease.late_fee_percent)),
    late_fee_grace_days: String(lease.late_fee_grace_days),
    notice_period_months: String(lease.notice_period_months),
  }));
  const { errors, validate, clearError, fieldProps, showServerErrors } = useFormErrors();
  const mutation = useRenewLeaseMutation({
    onSuccess: (data) => {
      toast.success(`Renewal ${data.reference} drafted.`);
      onSaved?.(data);
    },
    onError: (error) => {
      if (!showServerErrors(error.data, FIELDS)) toast.error(error.message || "Could not draft the renewal.");
    },
  });
  const update = (key, value) => {
    setForm((current) => ({ ...current, [key]: value }));
    clearError(key);
  };
  const whole = (value, min, max) => {
    const number = Number(value);
    return value !== "" && Number.isInteger(number) && number >= min && number <= max;
  };

  const submit = (event) => {
    event.preventDefault();
    if (mutation.isPending) return;
    const base = leaseRules({ ...form, start_date: startDate, unit: "-" });
    const rules = {
      end_date: base.end_date,
      monthly_rent: base.monthly_rent,
      deposit_amount: base.deposit_amount,
      rent_due_day: base.rent_due_day,
      late_fee_percent: () => {
        const value = Number(plain(form.late_fee_percent));
        return plain(form.late_fee_percent) !== "" && value >= 0 && value <= 100 ? "" : "Enter a percentage from 0 to 100.";
      },
      late_fee_grace_days: () => (whole(form.late_fee_grace_days, 0, 60) ? "" : "Enter 0 to 60 days."),
      notice_period_months: () => (whole(form.notice_period_months, 0, 12) ? "" : "Enter 0 to 12 months."),
    };
    if (!validate(rules, event.currentTarget)) return;
    mutation.mutate({
      id: lease.id,
      payload: {
        end_date: form.end_date,
        monthly_rent: plain(form.monthly_rent),
        deposit_amount: plain(form.deposit_amount || "0"),
        rent_due_day: Number(form.rent_due_day),
        late_fee_percent: plain(form.late_fee_percent),
        late_fee_grace_days: Number(form.late_fee_grace_days),
        notice_period_months: Number(form.notice_period_months),
      },
    });
  };

  return (
    <FormDrawer
      title={`Renew ${lease.reference}`}
      description={`${lease.tenant_name} · ${lease.unit_name}, ${lease.property_name}`}
      onSubmit={submit}
      onClose={onClose}
      errors={errors}
      busy={mutation.isPending}
      submitLabel="Create renewal draft"
      pendingLabel="Creating…"
      notice={
        <p className="dwella-muted-copy">
          This creates a draft you prepare and send for signing like any lease. Once signed, it starts on{" "}
          {formatDate(startDate)} and {lease.reference} ends the day before.
        </p>
      }
    >
      <section className="dwella-form-section">
        <dl className="dwella-detail-list dwella-renewal-current">
          <div><dt>Current term</dt><dd>{formatDate(lease.start_date)} – {formatDate(lease.end_date)}</dd></div>
          <div><dt>Monthly rent</dt><dd>{formatMoney(lease.monthly_rent)}</dd></div>
        </dl>
      </section>
      <section className="dwella-form-section">
        <h3>New term</h3>
        <p className="dwella-muted-copy">Terms are copied from {lease.reference}; change only what is new.</p>
        <div className="dwella-form-grid">
          <Field label="Starts" hint="The day after the current lease ends, so there is no gap.">
            <Input value={formatDate(startDate)} readOnly />
          </Field>
          <Field label="Ends" required {...fieldProps("end_date")}>
            <Input type="date" value={form.end_date} min={addDays(startDate, 1)} onChange={(_, d) => update("end_date", d.value)} />
          </Field>
          <Field label="Monthly rent (ZMW)" required {...fieldProps("monthly_rent")}>
            <Input inputMode="decimal" value={form.monthly_rent} onChange={(_, d) => update("monthly_rent", d.value)} />
          </Field>
          <Field label="Deposit (ZMW)" {...fieldProps("deposit_amount")}>
            <Input inputMode="decimal" value={form.deposit_amount} onChange={(_, d) => update("deposit_amount", d.value)} />
          </Field>
          <Field label="Rent due on day" required hint="1–28" {...fieldProps("rent_due_day")}>
            <Input type="number" min={1} max={28} value={form.rent_due_day} onChange={(_, d) => update("rent_due_day", d.value)} />
          </Field>
          <Field label="Notice period (months)" {...fieldProps("notice_period_months")}>
            <Input type="number" min={0} max={12} value={form.notice_period_months} onChange={(_, d) => update("notice_period_months", d.value)} />
          </Field>
          <Field label="Late fee (%)" {...fieldProps("late_fee_percent")}>
            <Input inputMode="decimal" value={form.late_fee_percent} onChange={(_, d) => update("late_fee_percent", d.value)} />
          </Field>
          <Field label="Grace days" {...fieldProps("late_fee_grace_days")}>
            <Input type="number" min={0} max={60} value={form.late_fee_grace_days} onChange={(_, d) => update("late_fee_grace_days", d.value)} />
          </Field>
        </div>
      </section>
    </FormDrawer>
  );
}
