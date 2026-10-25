import React, { useEffect, useRef, useState } from "react";
import {
  Button,
  DrawerBody,
  DrawerFooter,
  DrawerHeader,
  DrawerHeaderTitle,
  OverlayDrawer,
} from "@fluentui/react-components";
import { ArrowDownload20Regular, ArrowUpload24Regular, Dismiss20Regular } from "@fluentui/react-icons";

import { useImportConfirm, useImportPreview, useImportTemplate } from "../../Services/imports";
import { StatusBadge } from "../../shared/components";
import { FormSteps } from "../../shared/components/FormFlow";
import "../../shared/records.scss";
import "./imports.scss";

const MAX_BYTES = 1_000_000;
const STEPS = ["Upload", "Review rows", "Done"];
const kinds = {
  units: {
    title: "Import units",
    description: "Add many units at once from a spreadsheet.",
    columns: "Required: property, unit, rent_amount. Optional: bedrooms, bathrooms, floor_area, notes. Properties must already exist in Dwella.",
    singular: "unit",
    column: "Unit",
    plural: "units",
    labelOf: (values) => [values.property, values.unit].filter(Boolean).join(" · "),
    doneNote: "They start vacant. Add a lease when a tenant moves in.",
  },
  tenants: {
    title: "Import tenants",
    description: "Add many tenants at once from a spreadsheet.",
    columns: "Required: full_name, phone_number. Optional: email, national_id, tpin, notes.",
    singular: "tenant",
    column: "Tenant",
    plural: "tenants",
    labelOf: (values) => values.full_name || values.phone_number,
    doneNote: "They start as applicants. Put each one on a lease, or invite them to the tenant portal from their profile.",
  },
};
const statusTone = { ready: ["success", "Ready"], duplicate: ["warning", "Duplicate"], invalid: ["danger", "Fix"] };
const count = (n, text) => `${n} ${n === 1 ? text.singular : text.plural}`;
const reasonOf = (row) =>
  row.message ||
  Object.entries(row.errors || {})
    .map(([field, messages]) => `${field.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase())}: ${messages.join(" ")}`)
    .join(" ");

function RowsTable({ rows, text }) {
  return (
    <div className="dwella-table-card dwella-import-rows">
      <table className="dwella-table">
        <thead>
          <tr>
            <th scope="col">Row</th>
            <th scope="col">{text.column}</th>
            <th scope="col">Status</th>
            <th scope="col">Reason</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const [color, label] = statusTone[row.status];
            return (
              <tr key={row.row}>
                <td><strong>{row.row}</strong></td>
                <td>{row.label || text.labelOf(row.values) || "—"}</td>
                <td><StatusBadge color={color}>{label}</StatusBadge></td>
                <td className={row.status === "invalid" ? "is-danger" : "dwella-muted-copy"}>{reasonOf(row) || "—"}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// Upload → review every row → done. Nothing is saved until the manager
// confirms, and the confirmation creates every ready row or none.
export default function ImportDrawer({ kind, onClose }) {
  const text = kinds[kind];
  const fileInput = useRef(null);
  const heading = useRef(null);
  const [step, setStep] = useState(0);
  const [file, setFile] = useState(null);
  const [fileError, setFileError] = useState("");
  const [preview, setPreview] = useState(null);
  const [changed, setChanged] = useState(null);
  const [created, setCreated] = useState(0);
  const template = useImportTemplate(kind);
  const previewMutation = useImportPreview(kind, {
    onSuccess: (data) => {
      setPreview(data);
      setChanged(null);
      setStep(1);
    },
  });
  const confirm = useImportConfirm(kind, {
    onSuccess: (data) => {
      setCreated(data.created);
      setStep(2);
    },
    onError: (error) => {
      if (Array.isArray(error.data?.rows)) setChanged(error.data.rows);
    },
  });
  const busy = previewMutation.isPending || confirm.isPending;
  useEffect(() => {
    const frame = requestAnimationFrame(() => heading.current?.focus());
    return () => cancelAnimationFrame(frame);
  }, [step]);

  const choose = (chosen) => {
    previewMutation.reset();
    setFileError("");
    if (!chosen) return;
    if (!/\.csv$/i.test(chosen.name)) {
      setFile(null);
      setFileError("Choose a .csv file. In Excel or Google Sheets, save or download as CSV (UTF-8).");
      return;
    }
    if (chosen.size > MAX_BYTES) {
      setFile(null);
      setFileError("This file is larger than 1 MB. Split it into smaller files of up to 500 rows.");
      return;
    }
    setFile(chosen);
  };
  const review = async () => {
    if (!file) {
      setFileError("Choose a CSV file first.");
      return;
    }
    previewMutation.mutate(await file.text());
  };
  const restart = () => {
    setStep(0);
    setFile(null);
    setPreview(null);
    setChanged(null);
    previewMutation.reset();
    confirm.reset();
  };

  const counts = preview?.counts || { ready: 0, duplicate: 0, invalid: 0 };
  const skipped = counts.duplicate + counts.invalid;
  const previewError = previewMutation.error;
  const previewMessage = previewError
    ? (previewError.data && typeof previewError.data === "object"
      ? Object.values(previewError.data).flat().filter((item) => typeof item === "string").join(" ")
      : "") || previewError.message
    : "";

  return (
    <OverlayDrawer
      open
      position="end"
      size="medium"
      className="dwella-drawer dwella-form-drawer dwella-import-drawer"
      onOpenChange={(_, data) => !data.open && !busy && onClose()}
    >
      <DrawerHeader>
        <DrawerHeaderTitle action={<Button appearance="subtle" icon={<Dismiss20Regular />} aria-label="Close" disabled={busy} onClick={onClose} />}>
          {text.title}
        </DrawerHeaderTitle>
        <p className="dwella-drawer-note">{step === 0 ? text.description : file?.name}</p>
        <FormSteps steps={STEPS} step={step} label="Import progress" />
      </DrawerHeader>
      <DrawerBody>
        <div className="dwella-form-drawer-content" aria-busy={busy}>
          {step === 0 ? (
            <>
              <h2 ref={heading} tabIndex={-1} className="dwella-visually-hidden">Upload a file</h2>
              <section className="dwella-import-template">
                <h3>Start from the template</h3>
                <p className="dwella-muted-copy">{text.columns}</p>
                <Button icon={<ArrowDownload20Regular />} disabled={template.isPending} onClick={() => template.mutate()}>
                  {template.isPending ? "Downloading…" : "Download template"}
                </Button>
                {template.isError ? <p role="alert" className="dwella-import-error">{template.error.message || "Could not download the template."}</p> : null}
              </section>
              <label
                className={`dwella-import-drop${file ? " has-file" : ""}`}
                onDragOver={(event) => event.preventDefault()}
                onDrop={(event) => {
                  event.preventDefault();
                  choose(event.dataTransfer.files?.[0]);
                }}
              >
                <ArrowUpload24Regular aria-hidden="true" />
                <strong>{file ? file.name : "Choose a CSV file or drop it here"}</strong>
                <span>{file ? `${Math.max(1, Math.round(file.size / 1024))} KB · choose another to replace it` : "Up to 500 rows and 1 MB. Save from Excel or Google Sheets as CSV (UTF-8)."}</span>
                <input ref={fileInput} type="file" accept=".csv,text/csv" onChange={(event) => choose(event.target.files?.[0])} />
              </label>
              {fileError || previewMessage ? <p role="alert" className="dwella-import-error">{fileError || previewMessage}</p> : null}
              <p className="dwella-muted-copy">Nothing is saved until you confirm on the next step.</p>
            </>
          ) : step === 1 ? (
            <>
              <h2 ref={heading} tabIndex={-1} className="dwella-visually-hidden">Review rows</h2>
              {changed ? (
                <section className="dwella-callout is-danger" role="alert">
                  <strong>Some rows changed since the preview</strong>
                  <p>Nothing was imported. Upload the file again to see the current state.</p>
                </section>
              ) : (
                <div className="dwella-import-counts">
                  <StatusBadge color="success">{counts.ready} ready</StatusBadge>
                  {counts.duplicate ? <StatusBadge color="warning">{counts.duplicate} {counts.duplicate === 1 ? "duplicate" : "duplicates"}</StatusBadge> : null}
                  {counts.invalid ? <StatusBadge color="danger">{counts.invalid} need fixing</StatusBadge> : null}
                  {preview.ignored_columns.length ? (
                    <span className="dwella-muted-copy">Ignored {preview.ignored_columns.length === 1 ? "column" : "columns"}: {preview.ignored_columns.join(", ")}</span>
                  ) : null}
                </div>
              )}
              <RowsTable rows={changed || preview.rows} text={text} />
              {confirm.isError && !changed ? <p role="alert" className="dwella-import-error">{confirm.error.message || "Could not import the rows."}</p> : null}
              {!changed ? (
                <p className="dwella-muted-copy">
                  {counts.ready
                    ? `Only ready rows are imported${skipped ? "; fix the others in your file and import it again" : ""}. This preview stays valid for 30 minutes.`
                    : "No rows are ready to import. Fix the file and upload it again."}
                </p>
              ) : null}
            </>
          ) : (
            <>
              <h2 ref={heading} tabIndex={-1} className="dwella-visually-hidden">Import complete</h2>
              <section className="dwella-callout is-success" role="status">
                <strong>{count(created, text)} added</strong>
                <p>{text.doneNote}</p>
              </section>
              {skipped ? (
                <section className="dwella-import-template">
                  <h3>{skipped} {skipped === 1 ? "row" : "rows"} skipped</h3>
                  <p className="dwella-muted-copy">
                    {[counts.duplicate && `${counts.duplicate} already on file`, counts.invalid && `${counts.invalid} with errors`].filter(Boolean).join(", ")}.
                    {" "}Fix them in your file and import it again; {text.plural} already added are skipped.
                  </p>
                </section>
              ) : null}
            </>
          )}
        </div>
      </DrawerBody>
      <DrawerFooter className="dwella-drawer-footer">
        {step === 0 ? (
          <>
            <Button disabled={busy} onClick={onClose}>Cancel</Button>
            <Button appearance="primary" disabled={busy} onClick={review}>{previewMutation.isPending ? "Checking rows…" : "Review rows"}</Button>
          </>
        ) : step === 1 ? (
          <>
            <Button disabled={busy} onClick={restart}>{changed ? "Cancel" : "Back"}</Button>
            {changed ? (
              <Button appearance="primary" onClick={restart}>Upload again</Button>
            ) : (
              <Button appearance="primary" disabled={busy || !preview.preview_token} onClick={() => confirm.mutate(preview.preview_token)}>
                {confirm.isPending ? "Importing…" : counts.ready ? `Import ${count(counts.ready, text)}` : "Nothing to import"}
              </Button>
            )}
          </>
        ) : (
          <>
            <Button onClick={restart}>Import another file</Button>
            <Button appearance="primary" onClick={onClose}>Done</Button>
          </>
        )}
      </DrawerFooter>
    </OverlayDrawer>
  );
}
