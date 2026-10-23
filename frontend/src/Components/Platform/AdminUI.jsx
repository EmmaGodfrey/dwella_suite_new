import React, { useState } from "react";
import {
  Button, Dialog, DialogActions, DialogBody, DialogContent, DialogSurface, DialogTitle,
  Field, Input, Select, Textarea,
} from "@fluentui/react-components";
import { EmptyState } from "../../shared/components/EmptyState";
import { useFormErrors } from "../../shared/useFormErrors";
import "./platform.scss";
import { FormDrawer } from "../../shared/components/FormFlow";
import { firstErrorStep, ruleErrors } from "../../shared/formFlow";

export const nameOf = (user) => `${user?.first_name || ""} ${user?.last_name || ""}`.trim()
  || user?.email || user?.username || "Deleted user";
export const money = (value) => new Intl.NumberFormat("en-ZM", {
  style: "currency", currency: "ZMW", maximumFractionDigits: 2,
}).format(Number(value || 0));
export const when = (value) => value ? new Date(value).toLocaleString("en-GB", {
  day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit",
}) : "—";
export const workspaceName = (workspace) => workspace?.display_name || workspace?.name || "Platform";
export const roles = ["landlord", "tenant"];
export const choice = (value) => ({ value, label: value.replaceAll("_", " ") });

export function AdminHeader({ title, description, children, badge, initials }) {
  return <header className="dwella-page-header">
    <div className="admin-title">
      {initials && <span className="admin-initials" aria-hidden="true">{initials}</span>}
      <div className="dwella-page-header-copy"><h1>{title}</h1>{description && <p>{description}</p>}{badge}</div>
    </div>
    <div className="dwella-page-actions">{children}</div>
  </header>;
}

export function AdminState({ query, empty = false, title = "No results", children }) {
  if (query.isPending) return <div className="admin-loading" role="status" aria-label="Loading">
    {[0, 1, 2, 3].map((i) => <div className="dwella-skeleton" key={i} />)}
  </div>;
  if (query.isError) return <EmptyState title="Couldn’t load this page"
    description={query.error.message} actionLabel="Try again" onAction={() => query.refetch()} />;
  if (empty) return <EmptyState title={title} description="Adjust your filters or add a record to begin." />;
  return children;
}

export function AdminTable({ columns, rows, pagination, setPage }) {
  return <div className="dwella-table-card admin-table-card">
    <div className="admin-table-scroll"><table className="dwella-table">
      <thead><tr>{columns.map((column) => <th key={column.key} scope="col">{column.label}</th>)}</tr></thead>
      <tbody>{rows.map((row) => <tr key={row.id}>
        {columns.map((column) => <td key={column.key} data-label={column.label}>
          <div>{column.render ? column.render(row) : row[column.key] ?? "—"}</div>
        </td>)}
      </tr>)}</tbody>
    </table></div>
    {pagination && <footer className="dwella-table-footer">
      <span>{pagination.count} results · Page {pagination.page} of {pagination.total_pages || 1}</span>
      <div className="dwella-table-pager">
        <Button disabled={!pagination.previous} onClick={() => setPage(pagination.page - 1)}>Previous</Button>
        <Button disabled={!pagination.next} onClick={() => setPage(pagination.page + 1)}>Next</Button>
      </div>
    </footer>}
  </div>;
}

export function Filter({ label, value, onChange, options }) {
  return <Field label={label}><Select value={value} onChange={(_, d) => onChange(d.value)}>
    <option value="">All</option>{options.map((option) => <option key={option.value}
      value={option.value}>{option.label}</option>)}
  </Select></Field>;
}

export function AdminDrawer({
  title,
  initial = {},
  fields,
  submitLabel = "Save changes",
  onSubmit,
  onClose,
  children,
  steps,
  wideFields = [],
  summary,
}) {
  const [values, setValues] = useState(initial);
  const [step, setStep] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const { errors, validate, fieldProps, clearError, showServerErrors } =
    useFormErrors();
  const visible = typeof fields === "function" ? fields(values) : fields;
  const groups = steps?.map((item) => item.fields);
  const activeFields = steps
    ? visible.filter((field) => groups[step].includes(field.key))
    : visible;
  const submit = async (event) => {
    event.preventDefault();
    if (busy) return;
    const allRules = Object.fromEntries(
      visible.map((field) => [
        field.key,
        () => {
          const value = String(values[field.key] ?? "").trim();
          if (field.required && !value) return `Enter ${field.label.toLowerCase()}.`;
          if (field.minLength && value.length < field.minLength) return `Use at least ${field.minLength} characters.`;
          if (field.type === "email" && value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return "Enter a valid email.";
          if (field.pattern && value && !field.pattern.test(value)) return "Enter a valid value.";
          if (field.confirmation && value !== field.confirmation) return `Type ${field.confirmation} to continue.`;
          return "";
        },
      ]),
    );
    const last = !steps || step === steps.length - 1;
    const rules = last
      ? allRules
      : Object.fromEntries(
          Object.entries(allRules).filter(([key]) =>
            groups[step].includes(key),
          ),
        );
    if (!validate(rules, event.currentTarget)) {
      if (steps) setStep(firstErrorStep(ruleErrors(rules), groups, step));
      return;
    }
    if (!last) {
      setStep(step + 1);
      return;
    }
    setBusy(true);
    setError("");
    try {
      await onSubmit(values);
    } catch (failure) {
      if (steps) setStep(firstErrorStep(failure.data, groups, step));
      showServerErrors(
        failure.data,
        visible.map((f) => f.key),
      );
      setError(failure.message);
    } finally {
      setBusy(false);
    }
  };
  const renderedFields = (
    <div
      className={
        visible.length >= 5 ? "dwella-form-grid" : "admin-fields"
      }
    >
      {activeFields.map((field) => {
        const controlProps = {
          name: field.key,
          value: String(values[field.key] ?? ""),
          disabled: busy || field.disabled,
          onChange: (_, d) => { setValues((v) => ({ ...v, [field.key]: d.value })); clearError(field.key); },
        };
        const wide =
          wideFields.includes(field.key) || field.type === "textarea";
        return (
          <Field
            key={field.key}
            label={field.label}
            required={field.required}
            {...fieldProps(field.key)}
            className={`${wide ? "dwella-field-wide" : ""} ${fieldProps(field.key).className || ""}`}
          >
            {field.type === "select" ? (
              <Select {...controlProps}>
                <option value="">Choose…</option>
                {field.options.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </Select>
            ) : field.type === "textarea" ? (
              <Textarea {...controlProps} maxLength={field.maxLength || 300} />
            ) : (
              <Input {...controlProps} type={field.type === "email" ? "email" : "text"} maxLength={field.maxLength || 300} />
            )}
          </Field>
        );
      })}
    </div>
  );
  return (
    <FormDrawer
      compact={!steps && visible.length < 5}
      title={title}
      description={activeFields.some((field) => field.required) ? "Fields marked * are required." : undefined}
      steps={steps?.map((item) => item.title)}
      step={step}
      stepTitle={steps?.[step].title || "Details"}
      stepDescription={steps?.[step].description}
      onSubmit={submit}
      onBack={() => setStep(step - 1)}
      onClose={onClose}
      busy={busy}
      errors={errors}
      submitLabel={submitLabel}
      notice={
        error && (
          <p className="admin-error" role="alert">
            {error}
          </p>
        )
      }
    >
      {(!steps || step === 0) && children}
      {renderedFields}
      {summary && (!steps || step === steps.length - 1) && summary(values)}
    </FormDrawer>
  );
}

export function ConfirmAction({ title, description, confirmation, label = "Confirm", onConfirm, onClose }) {
  const [value, setValue] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  return <Dialog open onOpenChange={(_, d) => { if (!d.open && !busy) onClose(); }}>
    <DialogSurface><DialogBody><DialogTitle>{title}</DialogTitle><DialogContent>
      <p>{description}</p>{error && <p role="alert" className="admin-error">{error}</p>}
      {confirmation && <Field label={`Type ${confirmation} to confirm`}>
        <Input value={value} onChange={(_, d) => setValue(d.value)} /></Field>}
    </DialogContent><DialogActions>
      <Button disabled={busy} onClick={onClose}>Cancel</Button>
      <Button appearance="primary" disabled={busy || Boolean(confirmation && value !== confirmation)}
        onClick={async () => { setBusy(true); try { await onConfirm(value); }
          catch (e) { setError(e.message); } finally { setBusy(false); } }}>
        {busy ? "Working…" : label}</Button>
    </DialogActions></DialogBody></DialogSurface>
  </Dialog>;
}
