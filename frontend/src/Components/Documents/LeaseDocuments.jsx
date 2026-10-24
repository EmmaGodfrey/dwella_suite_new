import React, { useState } from "react";
import { Button, Checkbox, Field, Input, Select, Textarea } from "@fluentui/react-components";
import { documentError, useAttachOriginal, useDocumentSigners, useLeaseDocuments, useOriginalDocuments, useOriginalDownload, usePrepareDocument } from "../../Services/documents";
import { FormDrawer, FormModal } from "../../shared/components/FormFlow";
import { formatDate } from "../../shared/format";
import DocumentPreview, { documentStatus } from "./DocumentPreview";
import "./documents.scss";

function PrepareAgreement({ lease, previous, onClose, onPrepared }) {
  const [step, setStep] = useState(0);
  const signers = useDocumentSigners();
  const [values, setValues] = useState({ landlord_name: previous?.snapshot.landlord_name || "", landlord_address: previous?.snapshot.landlord_address || "",
    landlord_signer: previous?.landlord_signer_id || "", agreement_text: previous?.snapshot.agreement_text || "", schedule_text: previous?.snapshot.schedule_text || "", terms_approved: false });
  const [error, setError] = useState("");
  const mutation = usePrepareDocument({ onSuccess: onPrepared, onError: e => setError(documentError(e)) });
  function update(key, value) { setValues(current => ({ ...current, [key]: value })); setError(""); }
  function submit(event) {
    event.preventDefault();
    if (step === 0 && (!values.landlord_name.trim() || !values.landlord_address.trim() || !values.landlord_signer)) { setError("Enter the landlord's legal name, address and authorised signatory."); return; }
    if (step === 1 && values.agreement_text.trim().length < 200) { setError("Add the complete approved agreement wording (at least 200 characters)."); return; }
    if (step < 2) { setStep(current => current + 1); setError(""); return; }
    if (!values.terms_approved) { setError("Confirm the wording and signatory authority before preparing this version."); return; }
    mutation.mutate({ ...values, lease: lease.id, landlord_name: values.landlord_name.trim(), landlord_address: values.landlord_address.trim(), landlord_signer: Number(values.landlord_signer) });
  }
  return <FormDrawer title="Prepare lease agreement" description={`${lease.reference} · ${lease.tenant_name}`}
    steps={["Parties", "Agreement wording", "Review"]} step={step} onBack={() => { setStep(current => current - 1); setError(""); }}
    onClose={onClose} onSubmit={submit} submitLabel="Prepare document" pendingLabel="Preparing PDF…" busy={mutation.isPending}
    errors={error ? { form: error } : undefined} notice={error && <p className="dwella-document-error" role="alert">{error}</p>}>
    {step === 0 && <>
      <Field label="Landlord legal name" required><Input value={values.landlord_name} maxLength={180} onChange={(_, d) => update("landlord_name", d.value)} /></Field>
      <Field label="Landlord address" required><Textarea rows={3} value={values.landlord_address} maxLength={2000} onChange={(_, d) => update("landlord_address", d.value)} /></Field>
      <Field label="Authorised signatory" required hint="This active property manager signs using their own account.">
        <Select value={String(values.landlord_signer)} onChange={(_, d) => update("landlord_signer", d.value)}>
          <option value="">Choose property manager</option>{signers.data?.map(signer => <option key={signer.id} value={signer.id}>{signer.name} · {signer.email}</option>)}
        </Select>
      </Field>
      {signers.isLoading && <p role="status">Loading authorised accounts…</p>}
      {signers.isError && <p role="alert">{documentError(signers.error)} <Button onClick={() => signers.refetch()}>Retry</Button></p>}
      <p className="dwella-document-fineprint">Tenant, premises and financial terms come from this lease. Confirm the tenant email is correct before preparing.</p>
    </>}
    {step === 1 && <>
      <Field label="Complete agreement wording" required hint="Paste your approved lease clauses. Dwella formats this text; it does not supply a legal agreement.">
        <Textarea rows={15} resize="vertical" value={values.agreement_text} maxLength={30000} onChange={(_, d) => update("agreement_text", d.value)} />
      </Field>
      <Field label="Schedules and additional terms" hint="Include the inventory, rules and any agreed additions that form part of this agreement.">
        <Textarea rows={6} resize="vertical" value={values.schedule_text} maxLength={10000} onChange={(_, d) => update("schedule_text", d.value)} />
      </Field>
    </>}
    {step === 2 && <>
      <dl className="dwella-detail-list"><div><dt>Landlord</dt><dd>{values.landlord_name}</dd></div><div><dt>Tenant</dt><dd>{lease.tenant_name}</dd></div><div><dt>Premises</dt><dd>{lease.unit_name}, {lease.property_name}</dd></div><div><dt>Version</dt><dd>New fixed document version</dd></div></dl>
      <p>Review the generated PDF before inviting anyone to sign. A new version replaces any earlier pending signing version; completed documents stay saved.</p>
      <Checkbox checked={values.terms_approved} onChange={(_, d) => update("terms_approved", d.checked === true)} label="I confirm the full agreement wording is approved, the lease details are correct, and the selected account is authorised to sign for the landlord." />
    </>}
  </FormDrawer>;
}

function OriginalUpload({ lease, onClose }) {
  const [file, setFile] = useState(null);
  const [note, setNote] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [error, setError] = useState("");
  const mutation = useAttachOriginal({ onSuccess: onClose, onError: e => setError(documentError(e)) });
  function submit(event) {
    event.preventDefault();
    if (!file || file.size > 4 * 1024 ** 2 || !/\.pdf$/i.test(file.name) || note.trim().length < 5 || !confirmed) {
      setError("Choose a PDF up to 4 MB, describe its source, and confirm it is the signed original."); return;
    }
    const body = new FormData(); body.append("lease", lease.id); body.append("file", file); body.append("note", note.trim()); body.append("confirmed_original", "true"); mutation.mutate(body);
  }
  return <FormModal title="Attach signed original" description="Keep an agreement signed outside Dwella exactly as supplied. Its existing signatures are not independently verified by Dwella."
    onClose={onClose} onSubmit={submit} submitLabel="Save signed original" busy={mutation.isPending} errors={error ? { form: error } : undefined}
    notice={error && <p role="alert" className="dwella-document-error">{error}</p>}>
    <Field label="Signed PDF" required hint="Up to 4 MB; unencrypted PDF, at most 50 pages."><Input type="file" accept=".pdf" onChange={event => setFile(event.target.files?.[0])} /></Field>
    <Field label="Source and context" required><Textarea value={note} maxLength={500} onChange={(_, d) => setNote(d.value)} placeholder="Who supplied this file, and when?" /></Field>
    <Checkbox checked={confirmed} onChange={(_, d) => setConfirmed(d.checked === true)} label="This is the original signed PDF. Keep it unchanged." />
  </FormModal>;
}

export default function LeaseDocuments({ lease, canManage }) {
  const documents = useLeaseDocuments(lease.id);
  const originals = useOriginalDocuments(lease.id);
  const download = useOriginalDownload();
  const [preparing, setPreparing] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [preview, setPreview] = useState(null);
  const rows = documents.data?.results || [];
  const attachments = originals.data?.results || [];
  return <section className="dwella-surface dwella-lease-documents">
    <div className="dwella-document-section-heading"><div><h3>Documents and signatures</h3><p>Agreement versions, signing records and signed originals.</p></div>
      {canManage && <div className="dwella-document-actions"><Button onClick={() => setUploading(true)}>Attach signed original</Button>{lease.status !== "ended" && <Button onClick={() => setPreparing(true)}>Prepare agreement</Button>}</div>}
    </div>
    {documents.isLoading ? <p role="status">Loading document versions…</p> : documents.isError ? <p role="alert">{documentError(documents.error)} <Button onClick={() => documents.refetch()}>Retry</Button></p>
      : !rows.length ? <p className="dwella-muted-copy">No agreement prepared yet. Add the complete approved wording to create a document for review and signing.</p>
        : <ul className="dwella-document-list">{rows.map(doc => <li key={doc.id}><div><strong>Lease agreement · v{doc.version}</strong><span>{documentStatus[doc.status]} · {doc.signatures.length}/2 signatures · {formatDate(doc.created_at)}</span>{!doc.current_terms && <small>Lease details have changed since this version.</small>}</div><Button onClick={() => setPreview(doc)}>Preview agreement</Button></li>)}</ul>}
    {originals.isError && <p role="alert">Could not load original attachments. <Button onClick={() => originals.refetch()}>Retry</Button></p>}
    {attachments.length > 0 && <><h4>Signed originals</h4><ul className="dwella-document-list">{attachments.map(original => <li key={original.id}><div><strong>Uploaded signed PDF</strong><span>{original.note}</span><small>{formatDate(original.created_at)} · Original preserved · External signatures unverified</small></div><Button disabled={download.isPending} onClick={() => download.mutate(original.id)}>Download original</Button></li>)}</ul></>}
    {download.isError && <p role="alert">{documentError(download.error)}</p>}
    {preparing && <PrepareAgreement lease={lease} previous={rows[0]} onClose={() => setPreparing(false)} onPrepared={doc => { setPreparing(false); setPreview(doc); }} />}
    {uploading && <OriginalUpload lease={lease} onClose={() => setUploading(false)} />}
    {preview && <DocumentPreview key={preview.id} document={preview} onClose={() => setPreview(null)} />}
  </section>;
}
