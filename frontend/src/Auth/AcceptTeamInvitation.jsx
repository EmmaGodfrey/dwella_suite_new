import React, { useEffect, useState } from "react";
import { Button, Field, Input } from "@fluentui/react-components";
import { Link, useSearchParams } from "react-router-dom";
import { getAuthToken } from "../Services/apiClient";
import { logout } from "../Services/auth";
import { queryClient } from "../Services/queryClient";
import { useTeamInvitationAccept, useTeamInvitationPreview } from "../Services/team";
import { appHref, scopedStorageKey } from "../shared/storage";
import { useFormErrors } from "../shared/useFormErrors";
import AccessFrame from "./AccessFrame";

const PENDING_INVITE = scopedStorageKey("dwella.pending-team-invitation");

export default function AcceptTeamInvitation() {
  const [params] = useSearchParams();
  const [token] = useState(() => params.get("token") || sessionStorage.getItem(PENDING_INVITE) || "");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [accepted, setAccepted] = useState(false);
  const errors = useFormErrors();
  const preview = useTeamInvitationPreview({
    onSuccess: (data) => setFullName(data.full_name || ""),
    onError: (error) => { if (error.status === 400) sessionStorage.removeItem(PENDING_INVITE); },
  });
  const accept = useTeamInvitationAccept({
    onSuccess: () => { sessionStorage.removeItem(PENDING_INVITE); setAccepted(true); },
    onError: (error) => errors.showServerErrors(error.data, ["full_name", "password"]),
  });
  useEffect(() => {
    // Take the token out of the address bar; previewing does not use up the link.
    window.history.replaceState(window.history.state, "", window.location.pathname);
    if (token) { sessionStorage.setItem(PENDING_INVITE, token); preview.mutate(token); }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const data = preview.data;
  const signedIn = Boolean(getAuthToken());
  const submit = (event) => {
    event.preventDefault();
    if (accept.isPending) return;
    if (data.existing_account) { accept.mutate({ token }); return; }
    const name = fullName.trim();
    const ok = errors.validate({
      full_name: () => (name.length >= 2 ? "" : "Enter your full name."),
      password: () => (password.length >= 10 && !/^\d+$/.test(password) ? "" : "Use at least 10 characters, not all digits."),
      confirm: () => (password === confirm ? "" : "Passwords must match."),
    }, event.currentTarget);
    if (ok) accept.mutate({ token, full_name: name, password });
  };
  const switchAccount = async () => {
    sessionStorage.setItem(PENDING_INVITE, token);
    try { await logout(); queryClient.clear(); window.location.assign(appHref("/accept-team-invitation")); }
    catch { errors.validate({ account: () => "Could not sign out. Try again." }); }
  };

  const unavailable = !token || preview.error?.status === 400;
  const title = accepted ? "You have joined the team" : unavailable ? "Invitation unavailable"
    : preview.isError ? "Could not load invitation" : "Your team invitation";
  return (
    <AccessFrame title={title}>
      {accepted ? (
        <>
          <p>Your account now works in {data?.workspace_name || "the workspace"}. {signedIn ? "Continue to your dashboard." : "Sign in to continue."}</p>
          <Button as="a" href={appHref(signedIn ? "/dashboard" : "/login")} appearance="primary">Continue to Dwella</Button>
        </>
      ) : unavailable ? (
        <>
          <p>This invitation has expired or is unavailable. Ask a property admin for a new one.</p>
          <Button as={Link} to="/login">Back to sign in</Button>
        </>
      ) : preview.isError ? (
        <>
          <p role="alert">We could not check your invitation. Please try again.</p>
          <Button onClick={() => preview.mutate(token)} disabled={preview.isPending}>Retry</Button>
        </>
      ) : !data ? <p role="status">Checking your invitation…</p> : (
        <>
          <p><strong>{data.workspace_name}</strong> invited {data.email} to join as a <strong>{data.role_label.toLowerCase()}</strong>.</p>
          <p>
            {data.role === "landlord"
              ? "A property admin sees every property, the team, payouts and workspace settings."
              : "A property manager works on the properties a property admin assigns to them."}
          </p>
          {signedIn ? <Button appearance="subtle" onClick={switchAccount}>Use a different account</Button> : null}
          {data.existing_account && !signedIn ? (
            <>
              <p>Sign in with the invited email, then return here to accept.</p>
              <Button as={Link} to="/login?invitation=team" appearance="primary" onClick={() => sessionStorage.setItem(PENDING_INVITE, token)}>Sign in to accept</Button>
            </>
          ) : !data.existing_account && signedIn ? (
            <p role="alert">You are signed in to another account. Choose “Use a different account” to create the invited one.</p>
          ) : (
            <form onSubmit={submit} noValidate>
              {!data.existing_account ? (
                <>
                  <Field label="Full name" required {...errors.fieldProps("full_name")}>
                    <Input autoComplete="name" maxLength={180} value={fullName} onChange={(_, d) => { setFullName(d.value); errors.clearError("full_name"); }} />
                  </Field>
                  <Field label="Password" required {...errors.fieldProps("password")}>
                    <Input type="password" autoComplete="new-password" maxLength={128} value={password} onChange={(_, d) => { setPassword(d.value); errors.clearError("password"); }} />
                  </Field>
                  <Field label="Confirm password" required {...errors.fieldProps("confirm")}>
                    <Input type="password" autoComplete="new-password" maxLength={128} value={confirm} onChange={(_, d) => { setConfirm(d.value); errors.clearError("confirm"); }} />
                  </Field>
                </>
              ) : <p>You must be signed in with {data.email}.</p>}
              {accept.isError ? <p role="alert">{accept.error.message}</p> : null}
              <Button type="submit" appearance="primary" disabled={accept.isPending}>{accept.isPending ? "Accepting…" : "Accept invitation"}</Button>
            </form>
          )}
        </>
      )}
    </AccessFrame>
  );
}
