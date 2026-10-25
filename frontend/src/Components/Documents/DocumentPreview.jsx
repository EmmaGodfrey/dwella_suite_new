import React, { useEffect, useRef, useState } from "react";
import { Button, Select } from "@fluentui/react-components";
import { ArrowDownload20Regular, Dismiss20Regular } from "@fluentui/react-icons";
import { useMutation } from "@tanstack/react-query";
import { documentError, managementDocuments, useDocumentAction, useDocumentDownload, useDocumentPage } from "../../Services/documents";
import { formatDate } from "../../shared/format";
import SignaturePanel from "./SignaturePanel";
import { useBlobUrl } from "./SignatureInput";
import "./documents.scss";

export const documentStatus = { ready: "Ready for review", signing: "Awaiting signatures", signed: "Fully signed", superseded: "Superseded", revoked: "Signing revoked" };

export function PaperPreview({ doc, client = managementDocuments, accessKey = "management" }) {
  const [page, setPage] = useState(1);
  const [zoom, setZoom] = useState("fit");
  const result = useDocumentPage(client, doc, page, accessKey);
  const url = useBlobUrl(result.data);
  const download = useDocumentDownload(client, doc);
  useEffect(() => setPage(1), [doc.sha256]);
  return <div className="dwella-paper-preview">
    <div className="dwella-document-toolbar">
      <div className="dwella-document-actions">
        <Button disabled={page <= 1 || result.isFetching} onClick={() => setPage(value => value - 1)}>Previous</Button>
        <Select aria-label="Document page" value={String(page)} disabled={result.isFetching} onChange={(_, data) => setPage(Number(data.value))}>
          {Array.from({ length: doc.page_count }, (_, index) => <option key={index + 1} value={index + 1}>Page {index + 1} of {doc.page_count}</option>)}
        </Select>
        <Button disabled={page >= doc.page_count || result.isFetching} onClick={() => setPage(value => value + 1)}>Next</Button>
      </div>
      <div className="dwella-document-actions">
        <Select aria-label="Preview zoom" value={zoom} onChange={(_, data) => setZoom(data.value)}>
          <option value="fit">Fit width</option><option value="100">100%</option><option value="125">125%</option>
        </Select>
        <Button icon={<ArrowDownload20Regular />} disabled={download.isPending} onClick={() => download.mutate()}>{download.isPending ? "Downloading…" : "Download PDF"}</Button>
      </div>
    </div>
    <p className="dwella-document-fineprint">A4 · {doc.page_count} {doc.page_count === 1 ? "page" : "pages"} · {doc.snapshot.reference} · Version {doc.version}</p>
    <div className={`dwella-paper-stage${zoom === "fit" ? " is-fit" : ""}`} aria-busy={result.isFetching}>
      {result.isPending || result.isFetching ? <div className="dwella-paper-loading" role="status">Preparing document preview…</div>
        : result.isError ? <div className="dwella-paper-loading"><p role="alert">{documentError(result.error)}</p><Button onClick={() => result.refetch()}>Retry preview</Button></div>
        : <img className="dwella-document-paper" style={zoom === "fit" ? undefined : { width: zoom === "125" ? 993 : 794 }} src={url} alt={`${doc.snapshot.reference}, page ${page} of ${doc.page_count}. Download the PDF for selectable document text.`} />}
    </div>
    {download.isError && <p role="alert" className="dwella-document-error">{documentError(download.error)}</p>}
    <p className="dwella-document-fineprint">Previewed from the saved PDF. The downloaded document stays white and ready to print.</p>
  </div>;
}

export function SigningRecord({ doc }) {
  return <section className="dwella-signing-record">
    <h3>Signing record</h3>
    {!doc.signatures.length ? <p>No signatures recorded.</p> : <ul>{doc.signatures.map(signature => <li key={signature.id}>
      <strong>{signature.signer_name}</strong><span>{signature.role === "landlord" ? "For the landlord" : "Tenant"} · {formatDate(signature.signed_at)} · {signature.authentication_method === "account" ? "Authorised account" : "Email verified"}</span>
      <details><summary>Version and consent</summary><p>{signature.consent}</p><p className="dwella-document-digest">Reviewed SHA-256: {signature.reviewed_sha256}</p><p className="dwella-document-digest">Signed revision SHA-256: {signature.sha256}</p></details>
    </li>)}</ul>}
    <details><summary>Document fingerprint</summary><p className="dwella-document-digest">SHA-256: {doc.sha256}</p></details>
  </section>;
}

export default function DocumentPreview({ document: initial, onClose, onChange, returnFocusRef }) {
  const heading = useRef(null);
  useEffect(() => {
    const opener = returnFocusRef?.current || window.document.activeElement;
    heading.current?.focus();
    return () => { if (opener?.isConnected) opener.focus({ preventScroll: true }); };
  }, [returnFocusRef]);
  const [doc, setDoc] = useState(initial);
  const [signing, setSigning] = useState(false);
  const [inviteLink, setInviteLink] = useState(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const client = managementDocuments;
  function changed(data) { setDoc(data); onChange?.(data); }
  const refresh = useMutation({ mutationFn: () => client.get(doc.id, "document"), onSuccess: changed, onError: e => setError(documentError(e)) });
  const invite = useDocumentAction(client, doc.id, "invite", { onSuccess: (data) => {
    setInviteLink(data); setMessage("Signing link created. It expires in 7 days and requires tenant email verification."); refresh.mutate();
  }, onError: e => setError(documentError(e)) });
  const revoke = useDocumentAction(client, doc.id, "revoke", { onSuccess: data => { changed(data); setInviteLink(null); setMessage("Signing revoked. Existing links can no longer open this version."); }, onError: e => setError(documentError(e)) });
  const email = useDocumentAction(client, doc.id, "email-copies", { onSuccess: data => { setMessage(data.delivered ? "Completed copies have been emailed." : "Delivery failed. The signed PDF is saved; you can retry sending."); refresh.mutate(); }, onError: e => setError(documentError(e)) });
  const busy = invite.isPending || revoke.isPending || email.isPending;
  const open = doc.kind === "lease" && ["ready", "signing"].includes(doc.status) && doc.current_terms;
  return <section className="dwella-document-workspace" aria-label={doc.kind === "invoice" ? "Invoice preview" : "Lease agreement review"}>
    <div className="dwella-document-heading"><div><h2 ref={heading} tabIndex={-1}>{doc.kind === "invoice" ? "Invoice preview" : "Lease agreement"}</h2><p>{doc.snapshot.reference} · {documentStatus[doc.status]}</p></div>
      <Button appearance="subtle" icon={<Dismiss20Regular />} aria-label="Close document preview" disabled={busy || signing} onClick={onClose} />
    </div>
    <div className={doc.kind === "lease" ? "dwella-document-editor" : ""}>
      {doc.kind === "lease" && <div className="dwella-document-rail">
        <h3>Review and signing</h3>
        <p className="dwella-document-fineprint">Review every page before signing or inviting the tenant.</p>
        <div className="dwella-document-actions dwella-document-workflow">
          {open && <><Button disabled={busy || signing} onClick={() => { setError(""); invite.mutate({ email_link: false }); }}>Create tenant signing link</Button>
            <Button disabled={busy || signing} onClick={() => { setError(""); invite.mutate({ email_link: true }); }}>Email invitation to tenant</Button></>}
          {doc.can_sign && <Button appearance="primary" disabled={busy || signing} onClick={() => setSigning(true)}>Sign for landlord</Button>}
          {["ready", "signing"].includes(doc.status) && <Button disabled={busy || signing} onClick={() => { if (window.confirm("Revoke signing for this version? Existing links will stop working. Saved documents and signatures are retained.")) revoke.mutate({}); }}>Revoke signing</Button>}
          {doc.status === "signed" && doc.delivery_failed && <Button disabled={busy} onClick={() => email.mutate({})}>Retry emailing completed copies</Button>}
          <Button disabled={busy || signing || refresh.isPending} onClick={() => { setError(""); refresh.mutate(); }}>Refresh status</Button>
        </div>
        {!doc.current_terms && doc.status !== "signed" && <p className="dwella-document-notice">Lease details have changed. Prepare a new version before collecting more signatures.</p>}
        {message && <p role="status" className="dwella-document-notice">{message}</p>}
        {error && <p role="alert" className="dwella-document-error">{error}</p>}
        {inviteLink && <div className="dwella-signing-link"><label htmlFor="signing-link">Tenant signing link · share privately</label><input id="signing-link" readOnly value={inviteLink.url} onFocus={event => event.target.select()} />
          <Button onClick={async () => { try { await navigator.clipboard.writeText(inviteLink.url); setMessage("Signing link copied."); } catch { setMessage("Select and copy the signing link above."); } }}>Copy link</Button></div>}
        {signing && <SignaturePanel key={doc.sha256} doc={doc} client={client} onCancel={() => setSigning(false)} onSigned={data => {
          changed(data); setSigning(false); setMessage("Your signature has been recorded. The tenant signs separately.");
        }} />}
        <SigningRecord doc={doc} />
      </div>}
      <PaperPreview doc={doc} />
    </div>
  </section>;
}
