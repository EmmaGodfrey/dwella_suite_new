import React, { useState } from "react";
import { Button, Field, Input, Select } from "@fluentui/react-components";
import { toast } from "react-toastify";
import { readContactCSV, useOutreachMutation } from "../../Services/outreach";
import { AdminDrawer, AdminTable } from "../Platform/AdminUI";
import { ErrorText, OutreachStatus } from "./OutreachUI";

export default function ImportContacts({ onClose }) {
  const mutation = useOutreachMutation();
  const [csv, setCSV] = useState("");
  const [preview, setPreview] = useState(null);
  const [mapping, setMapping] = useState({
    name: "name",
    email: "email",
    source: "source",
    organization: "organization",
    phone: "phone",
  });
  const [changed, setChanged] = useState(false);
  const [error, setError] = useState(null);
  const check = async (text = csv, map = mapping) => {
    setError(null);
    try {
      const data = await mutation.mutateAsync({
        resource: "contacts",
        action: "import-preview",
        body: { csv: text, mapping: map },
      });
      setPreview(data);
      setChanged(false);
    } catch (e) {
      setError(e);
    }
  };
  return (
    <AdminDrawer
      title="Import contacts from CSV"
      fields={[]}
      onClose={onClose}
      submitLabel="Close"
      onSubmit={async () => onClose()}
    >
      <p>Preview up to 500 contacts. Nothing is saved until you confirm.</p>
      <Field label="CSV file">
        <Input
          type="file"
          accept=".csv,text/csv"
          disabled={mutation.isPending}
          onChange={async (e) => {
            const file = e.target.files?.[0];
            if (!file) return;
            try {
              const text = await readContactCSV(file);
              setCSV(text);
              setPreview(null);
              setChanged(true);
              await check(text);
            } catch (e) {
              setError(e);
            }
          }}
        />
      </Field>
      {preview?.columns && (
        <>
          <h3>Column mapping</h3>
          {Object.keys(mapping).map((key) => (
            <Field key={key} label={key[0].toUpperCase() + key.slice(1)}>
              <Select
                value={mapping[key]}
                onChange={(_, d) => {
                  setMapping({ ...mapping, [key]: d.value });
                  setChanged(true);
                }}
              >
                <option value="">Skip column</option>
                {preview.columns.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </Select>
            </Field>
          ))}
          <Button disabled={mutation.isPending} onClick={() => check()}>
            Preview mapping
          </Button>
          <p>
            {preview.ready} ready · {preview.rows.length - preview.ready}{" "}
            invalid, duplicate or suppressed
          </p>
          <AdminTable
            rows={preview.rows.map((r) => ({ ...r, id: r.row }))}
            columns={[
              { key: "row", label: "Row" },
              { key: "name", label: "Name" },
              {
                key: "status",
                label: "Result",
                render: (r) => (
                  <>
                    <OutreachStatus value={r.status} />
                    {r.errors && (
                      <span className="admin-note">
                        {Object.entries(r.errors)
                          .map(([key, val]) => `${key}: ${val}`)
                          .join(" · ")}
                      </span>
                    )}
                  </>
                ),
              },
            ]}
          />
          <Button
            appearance="primary"
            disabled={mutation.isPending || changed || !preview.ready}
            onClick={async () => {
              setError(null);
              try {
                const result = await mutation.mutateAsync({
                  resource: "contacts",
                  action: "import-confirm",
                  body: { preview_token: preview.preview_token },
                });
                toast.success(
                  `${result.created} contacts imported; ${result.skipped} skipped.`,
                );
                onClose();
              } catch (e) {
                setError(e);
              }
            }}
          >
            Import {preview.ready} contacts
          </Button>
        </>
      )}
      <ErrorText error={error} />
    </AdminDrawer>
  );
}
