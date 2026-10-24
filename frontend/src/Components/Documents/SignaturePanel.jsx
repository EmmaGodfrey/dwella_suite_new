import React, { useState } from "react";
import { Button, Checkbox, Field, Input } from "@fluentui/react-components";
import { documentError, useDocumentAction } from "../../Services/documents";
import SignatureInput, { useBlobUrl } from "./SignatureInput";

export const signingConsent = "I confirm my identity, have reviewed this complete agreement and its schedules, and intend this signature to apply to this document version.";

export default function SignaturePanel({ doc, client, role = "landlord", onSigned, onCancel }) {
  const [signature, setSignature] = useState(null);
  const [source, setSource] = useState("drawn");
  const [name, setName] = useState("");
  const [consent, setConsent] = useState(false);
  const [error, setError] = useState("");
  const url = useBlobUrl(signature);
  const expectedName = doc.snapshot[role === "landlord" ? "landlord_signer_name" : "tenant_name"];
  const mutation = useDocumentAction(client, doc.id, "sign", { onSuccess: onSigned,
    onError: e => setError(documentError(e)) });
  function submit(event) {
    event.preventDefault(); setError("");
    if (!signature || !consent || name.trim().toLocaleLowerCase() !== expectedName.trim().toLocaleLowerCase()) {
      setError("Review your signature, enter the name shown on the agreement, and confirm your intent to sign."); return;
    }
    const body = new FormData();
    body.append("signature", signature, "signature.png"); body.append("source", source);
    body.append("signer_name", name.trim()); body.append("consent", "true");
    body.append("expected_sha256", doc.sha256); mutation.mutate(body);
  }
  return <section className="dwella-signature-panel" aria-label="Sign agreement">
    <h2>{signature ? "Review your signature" : "Your signature"}</h2>
    <p>{expectedName} · {role === "landlord" ? "For the landlord" : "Tenant"}</p>
    {!signature ? <SignatureInput client={client} documentId={doc.id} onPreview={(blob, method) => {
      setSignature(blob); setSource(method); setConsent(false); setError("");
    }} /> : <form onSubmit={submit} noValidate>
      <fieldset disabled={mutation.isPending}>
        <div className="dwella-signature-placement">
          <small>{role === "landlord" ? "For the landlord" : "Tenant"} · execution page</small>
          <img src={url} alt="Your selected signature as it will appear in the signature field" />
          <strong>{expectedName}</strong>
          <small>The signing date and record are added when you confirm.</small>
        </div>
        <Button appearance="subtle" onClick={() => { setSignature(null); setConsent(false); }}>Change signature</Button>
        <Field label="Your full name" hint={`Enter ${expectedName} as shown on the agreement.`} required>
          <Input autoComplete="name" value={name} maxLength={180} onChange={(_, data) => setName(data.value)} />
        </Field>
        <Checkbox checked={consent} label={signingConsent} onChange={(_, data) => setConsent(data.checked === true)} />
        <p className="dwella-document-fineprint">{doc.snapshot.reference} · Version {doc.version}. Signing records your agreement; tenancy activation is handled separately.</p>
        <Button type="submit" appearance="primary" disabled={!consent || !name.trim() || mutation.isPending}>
          {mutation.isPending ? "Applying signature…" : "Confirm and sign agreement"}
        </Button>
      </fieldset>
    </form>}
    {error && <p role="alert" className="dwella-document-error">{error}</p>}
    {onCancel && <Button appearance="subtle" disabled={mutation.isPending} onClick={onCancel}>Cancel signing</Button>}
  </section>;
}
