import React, { useEffect, useState } from "react";
import { Button } from "@fluentui/react-components";
import { Link, Navigate, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { useCurrentUserQuery } from "../Services/queries";
import { useVerificationMutation } from "../Services/accountSetup";
import { getAuthToken } from "../Services/apiClient";
import { logout } from "../Services/auth";
import { queryClient } from "../Services/queryClient";
import AccessFrame from "./AccessFrame";
import { appHref } from "../shared/storage";

export default function VerifyEmail() {
  const [params] = useSearchParams();
  const [token] = useState(() => params.get("token") || "");
  const navigate = useNavigate();
  const location = useLocation();
  const [notice, setNotice] = useState("");
  const [cooldown, setCooldown] = useState(location.state?.deliveryFailed === false ? 60 : 0);
  const [confirmed, setConfirmed] = useState(false);
  const user = useCurrentUserQuery({ enabled: Boolean(getAuthToken()), retry: false });
  useEffect(() => { if (token) window.history.replaceState(window.history.state, "", window.location.pathname); }, [token]);
  useEffect(() => { if (!cooldown) return; const timer = setTimeout(() => setCooldown(cooldown - 1), 1000); return () => clearTimeout(timer); }, [cooldown]);
  const mutation = useVerificationMutation({ onSuccess: (data) => {
    if (data.verified) setConfirmed(true);
    else if (data.sent) { setNotice("Verification email sent. Check your inbox and spam folder."); setCooldown(60); }
  }, onError: (error) => { if (error.status === 429) setCooldown(60); } });
  const refresh = async () => {
    setNotice("");
    const result = await user.refetch();
    if (result.data?.email_verification?.verified) navigate("/dashboard", { replace: true });
    else setNotice("Your email is not confirmed yet. Open the verification link, then check again.");
  };
  if (!token && !getAuthToken()) return <Navigate to="/login" replace />;
  return <AccessFrame title={confirmed || user.data?.email_verification?.verified ? "Your email is confirmed" : token ? "Confirm your email" : "Verify your email"}>
    {confirmed || user.data?.email_verification?.verified ? <>
      <p>Continue with your account. If you opened this link in another browser, sign in with your password.</p>
      <Button as={Link} to={getAuthToken() ? "/dashboard" : "/login"} appearance="primary">Continue to Dwella</Button>
    </> : token ? <>
      <p>Confirm this email address to continue with Dwella. This does not sign you in.</p>
      {mutation.isError ? <p role="alert">{mutation.error.message}</p> : null}
      <Button appearance="primary" disabled={mutation.isPending || mutation.error?.status === 400} onClick={() => mutation.mutate(token)}>{mutation.isPending ? "Confirming…" : "Confirm email address"}</Button>
      {mutation.isError ? <Button onClick={() => window.location.assign(appHref(getAuthToken() ? "/verify-email" : "/login"))}>Request a new link</Button> : null}
    </> : <>
      <p>{location.state?.deliveryFailed && !mutation.isSuccess ? "We could not send your verification email. Try sending it again to " : "Open the verification email for "}<strong>{user.data?.email || "your email address"}</strong> to continue setup. Check your spam folder too.</p>
      {user.isError ? <p role="alert">Could not load your account. <Button onClick={() => user.refetch()}>Retry</Button></p> : null}
      <Button appearance="primary" disabled={user.isFetching} onClick={refresh}>I have verified my email</Button>
      <Button disabled={mutation.isPending || cooldown > 0 || user.isLoading} onClick={() => mutation.mutate()}>{cooldown ? `Resend in ${cooldown}s` : mutation.isPending ? "Sending…" : "Resend verification email"}</Button>
      {mutation.isError ? <p role="alert">{mutation.error.status === 503 ? "We could not send the email. Please try again." : mutation.error.message}</p> : null}
      <Button appearance="subtle" onClick={async () => { try { await logout(); queryClient.clear(); navigate("/login", { replace: true }); } catch { setNotice("Could not sign out. Please try again."); } }}>Sign out</Button>
    </>}
    {notice ? <p role="status">{notice}</p> : null}
  </AccessFrame>;
}
