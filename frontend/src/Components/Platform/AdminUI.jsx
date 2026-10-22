import React, { useState } from "react";
import {
  Button, Dialog, DialogActions, DialogBody, DialogContent, DialogSurface, DialogTitle,
  DrawerBody, DrawerFooter, DrawerHeader, DrawerHeaderTitle, Field, Input,
  OverlayDrawer, Select, Textarea,
} from "@fluentui/react-components";
import { Dismiss24Regular } from "@fluentui/react-icons";
import { EmptyState } from "../../shared/components";
import { useFormErrors } from "../../shared/useFormErrors";
import "./platform.scss";

export const nameOf = (user) => `${user?.first_name || ""} ${user?.last_name || ""}`.trim()
  || user?.email || user?.username || "Deleted user";
export const money = (value) => new Intl.NumberFormat("en-ZM", {
  style: "currency", currency: "ZMW", maximumFractionDigits: 2,
}).format(Number(value || 0));
export const when = (value) => value ? new Date(value).toLocaleString("en-GB", {
  day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit",
}) : "—";
export const workspaceName = (workspace) => workspace?.display_name || workspace?.name || "Platform";
export const roles = ["owner", "admin", "manager", "staff", "viewer", "tenant"];
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

export function AdminDrawer({ title, initial = {}, fields, submitLabel = "Save changes", onSubmit,
  onClose, children }) {
  const [values, setValues] = useState(initial);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const { validate, fieldProps, clearError, showServerErrors } = useFormErrors();
  const visible = typeof fields === "function" ? fields(values) : fields;
  const submit = async (event) => {
    event.preventDefault();
    if (busy) return;
    const rules = Object.fromEntries(visible.map((field) => [field.key, () => {
      const value = String(values[field.key] ?? "").trim();
      if (field.required && !value) return `Enter ${field.label.toLowerCase()}.`;
      if (field.minLength && value.length < field.minLength) return `Use at least ${field.minLength} characters.`;
      if (field.type === "email" && value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return "Enter a valid email.";
      if (field.pattern && value && !field.pattern.test(value)) return "Enter a valid value.";
      if (field.confirmation && value !== field.confirmation) return `Type ${field.confirmation} to continue.`;
      return "";
    }]));
    if (!validate(rules, event.currentTarget)) return;
    setBusy(true); setError("");
    try { await onSubmit(values); }
    catch (failure) { showServerErrors(failure.data, visible.map((f) => f.key)); setError(failure.message); }
    finally { setBusy(false); }
  };
  return <OverlayDrawer open position="end" className="admin-drawer"
    onOpenChange={(_, d) => { if (!d.open && !busy) onClose(); }}>
    <DrawerHeader><DrawerHeaderTitle action={<Button appearance="subtle" aria-label="Close"
      disabled={busy} icon={<Dismiss24Regular />} onClick={onClose} />}>{title}</DrawerHeaderTitle></DrawerHeader>
    <DrawerBody><form id="admin-drawer-form" onSubmit={submit} noValidate>
      {children}{error && <p className="admin-error" role="alert">{error}</p>}
      {visible.map((field) => {
        const controlProps = {
          value: String(values[field.key] ?? ""), disabled: busy || field.disabled,
          onChange: (_, d) => { setValues((v) => ({ ...v, [field.key]: d.value })); clearError(field.key); },
        };
        return <Field key={field.key} label={field.label} required={field.required} {...fieldProps(field.key)}>
          {field.type === "select" ? <Select {...controlProps}><option value="">Choose…</option>
            {field.options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </Select> : field.type === "textarea" ? <Textarea {...controlProps} maxLength={field.maxLength || 300} />
            : <Input {...controlProps} type={field.type === "email" ? "email" : "text"} maxLength={field.maxLength || 300} />}
        </Field>;
      })}
    </form></DrawerBody>
    <DrawerFooter><Button disabled={busy} onClick={onClose}>Cancel</Button>
      <Button appearance="primary" form="admin-drawer-form" type="submit" disabled={busy}>
        {busy ? "Saving…" : submitLabel}</Button></DrawerFooter>
  </OverlayDrawer>;
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
