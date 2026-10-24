import React, { useEffect, useState } from "react";
import { Button, Field, Input } from "@fluentui/react-components";
import { Link, useSearchParams } from "react-router-dom";
import { useInvitationAccept, useInvitationPreview } from "../Services/accountSetup";
import { getAuthToken } from "../Services/apiClient";
import { useFormErrors } from "../shared/useFormErrors";
import AccessFrame from "./AccessFrame";
import { scopedStorageKey, appHref } from "../shared/storage";
import { logout } from "../Services/auth";
import { queryClient } from "../Services/queryClient";

const PENDING_INVITE = scopedStorageKey("dwella.pending-tenant-invitation");
export default function AcceptInvitation() {
  const [params] = useSearchParams();
  const [token] = useState(() => params.get("token") || sessionStorage.getItem(PENDING_INVITE) || "");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [accepted, setAccepted] = useState(false);
  const preview = useInvitationPreview({ onError: (error) => { if (error.status === 400) sessionStorage.removeItem(PENDING_INVITE); } });
  const errors = useFormErrors();
  const accept = useInvitationAccept({ onSuccess: () => { sessionStorage.removeItem(PENDING_INVITE); setAccepted(true); }, onError: (e) => errors.showServerErrors(e.data, ["password"]) });
  useEffect(() => {
    window.history.replaceState(window.history.state, "", window.location.pathname);
    if (token) { sessionStorage.setItem(PENDING_INVITE, token); preview.mutate(token); }
    // Preview does not consume the link; only the explicit acceptance button does.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);
  const submit = (event) => {
    event.preventDefault();
    if (!preview.data?.existing_account && !errors.validate({
      password: () => password.length >= 10 && !/^\d+$/.test(password) ? "" : "Use at least 10 characters, not all digits.",
      confirm: () => password === confirm ? "" : "Passwords must match.",
    }, event.currentTarget)) return;
    accept.mutate({ token, ...(preview.data?.existing_account ? {} : { password }) });
  };
  const unavailable = !token || preview.error?.status === 400;
  return <AccessFrame title={accepted ? "Your tenant account is ready" : unavailable ? "Invitation unavailable" : preview.isError ? "Could not load invitation" : "Your tenant invitation"}>
    {accepted ? <><p>Your account is linked to your tenancy. Sign in to continue.</p><Button as={Link} to={getAuthToken() ? "/profile" : "/login"} appearance="primary">Continue to Dwella</Button></> : unavailable ? <><p>This invitation has expired or is unavailable. Ask your property manager for a new one.</p><Button as={Link} to="/login">Back to sign in</Button></> : preview.isError ? <><p role="alert">We could not check your invitation. Please try again.</p><Button onClick={() => preview.mutate(token)} disabled={preview.isPending}>Retry</Button></> : !preview.data ? <p role="status">Checking your invitation…</p> : <>
      <p><strong>{preview.data.workspace_name}</strong> invited <strong>{preview.data.tenant_name}</strong> at {preview.data.email}.</p>
      <p>Accepting connects your tenant account. It does not sign a lease or make a payment.</p>
      {getAuthToken() ? <Button appearance="subtle" onClick={async () => {
        sessionStorage.setItem(PENDING_INVITE, token);
        try { await logout(); queryClient.clear(); window.location.assign(appHref("/accept-invitation")); }
        catch { errors.validate({ account: () => "Could not sign out. Try again." }); }
      }}>Use a different account</Button> : null}
      {preview.data.existing_account && !getAuthToken() ? <>
        <p>Sign in with the invited email, then return here to accept.</p>
        <Button as={Link} to="/login?invitation=1" appearance="primary" onClick={() => sessionStorage.setItem(PENDING_INVITE, token)}>Sign in to accept</Button>
      </> : <form onSubmit={submit} noValidate>
        {!preview.data.existing_account ? <>
          <Field label="Password" {...errors.fieldProps("password")}><Input type="password" autoComplete="new-password" maxLength={128} value={password} onChange={(_, d) => { setPassword(d.value); errors.clearError("password"); }} /></Field>
          <Field label="Confirm password" {...errors.fieldProps("confirm")}><Input type="password" autoComplete="new-password" maxLength={128} value={confirm} onChange={(_, d) => { setConfirm(d.value); errors.clearError("confirm"); }} /></Field>
        </> : <p>You must be signed in with {preview.data.email}.</p>}
        {accept.isError ? <p role="alert">{accept.error.message}</p> : null}
        <Button type="submit" appearance="primary" disabled={accept.isPending}>{accept.isPending ? "Accepting…" : "Accept invitation"}</Button>
      </form>}
    </>}
  </AccessFrame>;
}
