import React, { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { Button, Field, Input } from "@fluentui/react-components";
import { documentError, signingDocuments, useDocumentAction, useSigningDocument } from "../../Services/documents";
import { PaperPreview, SigningRecord, documentStatus } from "./DocumentPreview";
import SignaturePanel from "./SignaturePanel";
import "./documents.scss";

export default function PublicSigning() {
  const { token } = useParams();
  const cache = useQueryClient();
  const [session, setSession] = useState("");
  const [code, setCode] = useState("");
  const [requested, setRequested] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [signed, setSigned] = useState(null);
  const client = useMemo(() => signingDocuments(token, session), [token, session]);
  const document = useSigningDocument(client, session, token);
  const request = useDocumentAction(client, null, "request-code", {
    onSuccess: data => { setRequested(true); setMessage(data.message); setError(""); },
    onError: e => setError(documentError(e)),
  });
  const verify = useDocumentAction(client, null, "verify", {
    onSuccess: data => { setSession(data.session); setError(""); setMessage(""); setCode(""); },
    onError: e => setError(documentError(e)),
  });
  useEffect(() => {
    // A full reload discards any third-party widget already loaded in an account tab.
    // Fresh signing entries skip widget installation entirely.
    if (window.document.getElementById("dwella-handy-agent-widget")) {
      window.location.reload();
      return;
    }
    const oldTitle = window.document.title;
    window.document.title = "Review and sign your lease · Dwella";
    const meta = window.document.createElement("meta"); meta.name = "referrer"; meta.content = "no-referrer"; window.document.head.appendChild(meta);
    return () => { meta.remove(); window.document.title = oldTitle; cache.removeQueries({ queryKey: ["signing-document"] }); cache.removeQueries({ queryKey: ["document-page"] }); };
  }, [cache]);
  useEffect(() => { setSession(""); setSigned(null); setRequested(false); setError(""); }, [token]);
  const doc = signed || document.data;
  const tenantSigned = doc?.signatures.some(signature => signature.role === "tenant");
  return <main className={`dwella-public-signing${doc ? " has-document" : ""}`}>
    <header className="dwella-public-signing-heading"><span className="dwella-public-wordmark">Dwe<span>lla</span></span><span>Lease signing</span></header>
    {!session ? <section className="dwella-signing-entry">
      <h1>Review and sign your lease</h1><p>Verify your email to open your agreement. We’ll send a code to the tenant email provided by your property manager.</p>
      <Button appearance={requested ? "secondary" : "primary"} disabled={request.isPending || verify.isPending} onClick={() => request.mutate({})}>{request.isPending ? "Requesting code…" : requested ? "Send another code" : "Send verification code"}</Button>
      {requested && <form onSubmit={event => { event.preventDefault(); setError(""); if (!/^\d{6}$/.test(code)) setError("Enter the six-digit code from your email."); else verify.mutate({ code }); }}>
        <Field label="Verification code" required hint="The code expires in 10 minutes."><Input value={code} inputMode="numeric" autoComplete="one-time-code" maxLength={6} onChange={(_, data) => setCode(data.value.replace(/\D/g, ""))} /></Field>
        <Button type="submit" appearance="primary" disabled={verify.isPending || code.length !== 6}>{verify.isPending ? "Verifying…" : "Verify and open agreement"}</Button>
      </form>}
      {message && <p role="status">{message}</p>}
      {error && <p role="alert" className="dwella-document-error">{error}</p>}
      <p className="dwella-document-fineprint">Entering a code only opens the document. Your signature is applied after a separate review and confirmation.</p>
    </section> : document.isPending ? <p role="status">Opening your agreement…</p> : document.isError ? <section className="dwella-signing-entry"><h1>Agreement unavailable</h1><p role="alert">{documentError(document.error)}</p><Button onClick={() => { setSession(""); setSigned(null); }}>Verify email again</Button><p>Contact your property manager if the invitation has expired or the lease has changed.</p></section>
      : doc && <>
        <div className="dwella-public-document-title"><h1>{tenantSigned ? "Your signature is recorded" : "Review your agreement"}</h1><p>{doc.snapshot.tenant_name} · {doc.snapshot.reference} · Version {doc.version} · {documentStatus[doc.status]}</p></div>
        <Button disabled={document.isFetching} onClick={() => { setSigned(null); document.refetch(); }}>Refresh document and signing status</Button>
        {tenantSigned && <p role="status" className="dwella-document-notice">{doc.status === "signed" ? "All parties have signed. Download your completed agreement below." : "Your signature is saved. The landlord still needs to sign; completed copies are emailed after both parties sign."}</p>}
        <div className={`dwella-public-document-layout${tenantSigned ? " is-complete" : ""}`}>
          <PaperPreview doc={doc} client={client} accessKey={session} />
          {!tenantSigned && <SignaturePanel key={doc.sha256} role="tenant" doc={doc} client={client} onSigned={setSigned} />}
        </div>
        <SigningRecord doc={doc} />
      </>}
    <footer className="dwella-document-fineprint">Private document review · Electronic signatures with a signing record</footer>
  </main>;
}
