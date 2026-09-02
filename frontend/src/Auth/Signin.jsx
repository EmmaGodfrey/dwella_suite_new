import React, { useMemo, useState } from "react";
import { Button, Card, Field, Input, Text, Title1, Title3 } from "@fluentui/react-components";
import { ArrowLeft24Regular, Eye24Regular, EyeOff24Regular, LockClosed24Regular, Mail24Regular, Shield24Regular } from "@fluentui/react-icons";
import { useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "react-toastify";

import { useLoginMutation, usePasswordResetConfirmMutation, usePasswordResetRequestMutation, useTwoFactorLoginMutation } from "../Services/mutations";

const disposableDomains = new Set(["10minutemail.com", "guerrillamail.com", "mailinator.com", "tempmail.com", "temp-mail.org", "throwawaymail.com", "yopmail.com"]);
const validateEmail = (value) => {
  const email = value.trim().toLowerCase();
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return "Enter a valid email address.";
  if (disposableDomains.has(email.split("@").pop())) return "Use a permanent email address.";
  return "";
};
const validatePassword = (value) => {
  if (value.length < 10) return "Password must be at least 10 characters.";
  if (/^\d+$/.test(value)) return "Password cannot be entirely numeric.";
  return "";
};

const Signin = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [email, setEmail] = useState("admin@dwella.local");
  const [password, setPassword] = useState("admin12345");
  const [resetPassword, setResetPassword] = useState("");
  const [twoFactorCode, setTwoFactorCode] = useState("");
  const [challengeToken, setChallengeToken] = useState("");
  const [mode, setMode] = useState(searchParams.get("reset_uid") && searchParams.get("reset_token") ? "reset-confirm" : "login");
  const [showPassword, setShowPassword] = useState(false);
  const resetUid = searchParams.get("reset_uid");
  const resetToken = searchParams.get("reset_token");

  const copy = useMemo(() => {
    if (mode === "forgot") return ["Reset password", "Enter your admin email and we will send a secure reset link."];
    if (mode === "reset-confirm") return ["Set new password", "Choose a stronger password for your Dwella account."];
    if (mode === "2fa") return ["Two-factor verification", "Enter the code from your authenticator app."];
    return ["Welcome to Dwella Suite", "Secure access for property operations, owners, tenants, and finance."];
  }, [mode]);

  const loginMutation = useLoginMutation({
    onSuccess: (data) => {
      if (data.two_factor_required) {
        setChallengeToken(data.challenge_token);
        setMode("2fa");
        return;
      }
      navigate("/dashboard", { replace: true });
    },
    onError: (error) => toast.error(error.message || "Login failed"),
  });
  const twoFactorMutation = useTwoFactorLoginMutation({
    onSuccess: () => navigate("/dashboard", { replace: true }),
    onError: (error) => toast.error(error.message || "Invalid authentication code"),
  });
  const resetRequestMutation = usePasswordResetRequestMutation({
    onSuccess: () => toast.success("If that email exists, a reset link has been sent."),
    onError: (error) => toast.error(error.message || "Password reset failed"),
  });
  const resetConfirmMutation = usePasswordResetConfirmMutation({
    onSuccess: () => {
      toast.success("Password reset complete. Sign in with your new password.");
      setMode("login");
      navigate("/login", { replace: true });
    },
    onError: (error) => toast.error(error.message || "Password reset failed"),
  });

  const submitLogin = (event) => {
    event.preventDefault();
    const emailError = validateEmail(email);
    if (emailError) return toast.error(emailError);
    if (!password) return toast.error("Enter your password.");
    loginMutation.mutate({ email: email.trim().toLowerCase(), password });
  };
  const submitResetRequest = (event) => {
    event.preventDefault();
    const emailError = validateEmail(email);
    if (emailError) return toast.error(emailError);
    resetRequestMutation.mutate({ email: email.trim().toLowerCase() });
  };
  const submitResetConfirm = (event) => {
    event.preventDefault();
    const passwordError = validatePassword(resetPassword);
    if (passwordError) return toast.error(passwordError);
    resetConfirmMutation.mutate({ uid: resetUid, token: resetToken, password: resetPassword });
  };
  const submitTwoFactor = (event) => {
    event.preventDefault();
    if (!/^\d{6}$/.test(twoFactorCode)) return toast.error("Enter the 6-digit code from your authenticator app.");
    twoFactorMutation.mutate({ challengeToken, code: twoFactorCode });
  };

  return (
    <main className="dwella-auth-page">
      <section className="dwella-auth-hero">
        <div className="dwella-auth-brand">
          <span><img src="/assets/images/logo/dwella-icon.png" alt="" /></span>
          <div><strong>Dwella Suite</strong><small>Property OS</small></div>
        </div>
        <div>
          <Text className="dwella-kicker">Built for property operators</Text>
          <Title1>One calm workspace for the messy business of managing property.</Title1>
          <Text>Track portfolio health, tenants, leases, maintenance, payments, reports, and admin security without carrying template clutter into the product.</Text>
        </div>
      </section>

      <section className="dwella-auth-panel">
        <Card className="dwella-auth-card" appearance="outline">
          <form onSubmit={mode === "forgot" ? submitResetRequest : mode === "reset-confirm" ? submitResetConfirm : mode === "2fa" ? submitTwoFactor : submitLogin}>
            <div className="dwella-auth-card-header">
              <span>{mode === "2fa" ? <Shield24Regular /> : <LockClosed24Regular />}</span>
              <div><Title3>{copy[0]}</Title3><Text>{copy[1]}</Text></div>
            </div>

            {mode === "2fa" ? (
              <Field label="Authentication code"><Input inputMode="numeric" maxLength={6} value={twoFactorCode} onChange={(_, data) => setTwoFactorCode(data.value.replace(/\D/g, ""))} /></Field>
            ) : mode === "reset-confirm" ? (
              <Field label="New password"><Input type={showPassword ? "text" : "password"} value={resetPassword} onChange={(_, data) => setResetPassword(data.value)} contentAfter={<Button appearance="transparent" icon={showPassword ? <EyeOff24Regular /> : <Eye24Regular />} onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? "Hide password" : "Show password"} />} /></Field>
            ) : (
              <>
                <Field label="Email address"><Input type="email" contentBefore={<Mail24Regular />} value={email} onChange={(_, data) => setEmail(data.value)} /></Field>
                {mode === "login" ? <Field label="Password"><Input type={showPassword ? "text" : "password"} value={password} onChange={(_, data) => setPassword(data.value)} contentAfter={<Button appearance="transparent" icon={showPassword ? <EyeOff24Regular /> : <Eye24Regular />} onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? "Hide password" : "Show password"} />} /></Field> : null}
              </>
            )}

            <Button appearance="primary" type="submit" disabled={loginMutation.isPending || twoFactorMutation.isPending || resetRequestMutation.isPending || resetConfirmMutation.isPending}>
              {mode === "forgot"
                ? resetRequestMutation.isPending ? "Sending..." : "Send reset link"
                : mode === "reset-confirm"
                  ? resetConfirmMutation.isPending ? "Saving..." : "Set password"
                  : mode === "2fa"
                    ? twoFactorMutation.isPending ? "Verifying..." : "Verify and continue"
                    : loginMutation.isPending ? "Signing in..." : "Sign in"}
            </Button>

            {mode === "login" ? (
              <Button appearance="transparent" onClick={() => setMode("forgot")}>Forgot password?</Button>
            ) : (
              <Button appearance="transparent" icon={<ArrowLeft24Regular />} onClick={() => setMode("login")}>Back to sign in</Button>
            )}
          </form>
        </Card>
      </section>
    </main>
  );
};

export default Signin;
