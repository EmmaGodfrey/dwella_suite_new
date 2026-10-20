import React, { useMemo, useState } from "react";
import { Button, Field, Input } from "@fluentui/react-components";
import { ArrowLeft16Regular, Eye20Regular, EyeOff20Regular } from "@fluentui/react-icons";
import { useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "react-toastify";

import { useLoginMutation, usePasswordResetConfirmMutation, usePasswordResetRequestMutation, useTwoFactorLoginMutation } from "../Services/mutations";
import { useFormErrors } from "../shared/useFormErrors";
import AuthTour from "./AuthTour";

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

// Heading, supporting line, and submit label for each step of the flow. Keeping
// them in one table makes it obvious that every mode states its own task -- the
// heading is the thing the person is here to do, not a greeting.
const modeCopy = {
  login: ["Sign in", "Use your Dwella admin email and password."],
  forgot: ["Reset password", "We will email a reset link to your admin address."],
  "reset-confirm": ["Set a new password", "At least 10 characters, and not all digits."],
  "2fa": ["Enter your code", "Open your authenticator app and enter the current 6-digit code."],
};

const Signin = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  // Local-dev convenience only. `import.meta.env.DEV` folds to false in a
  // production build, so these literals are stripped from the shipped bundle.
  const [email, setEmail] = useState(import.meta.env.DEV ? "admin@dwella.local" : "");
  const [password, setPassword] = useState(import.meta.env.DEV ? "admin12345" : "");
  const [resetPassword, setResetPassword] = useState("");
  const [twoFactorCode, setTwoFactorCode] = useState("");
  const [challengeToken, setChallengeToken] = useState("");
  const [mode, setMode] = useState(searchParams.get("reset_uid") && searchParams.get("reset_token") ? "reset-confirm" : "login");
  const [showPassword, setShowPassword] = useState(false);
  const resetUid = searchParams.get("reset_uid");
  const resetToken = searchParams.get("reset_token");
  const { validate, clearError, clearAll, fieldProps } = useFormErrors();

  // Each mode is a different form; stale messages should not carry across.
  const switchMode = (next) => {
    clearAll();
    setShowPassword(false);
    setMode(next);
  };

  const [heading, blurb] = modeCopy[mode];

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
    const valid = validate({
      email: () => validateEmail(email),
      password: () => (password ? "" : "Enter your password."),
    }, event.currentTarget);
    if (!valid) return;
    loginMutation.mutate({ email: email.trim().toLowerCase(), password });
  };
  const submitResetRequest = (event) => {
    event.preventDefault();
    const valid = validate({ email: () => validateEmail(email) }, event.currentTarget);
    if (!valid) return;
    resetRequestMutation.mutate({ email: email.trim().toLowerCase() });
  };
  const submitResetConfirm = (event) => {
    event.preventDefault();
    const valid = validate({ resetPassword: () => validatePassword(resetPassword) }, event.currentTarget);
    if (!valid) return;
    resetConfirmMutation.mutate({ uid: resetUid, token: resetToken, password: resetPassword });
  };
  const submitTwoFactor = (event) => {
    event.preventDefault();
    const valid = validate({
      twoFactorCode: () => (/^\d{6}$/.test(twoFactorCode) ? "" : "Enter the 6-digit code from your authenticator app."),
    }, event.currentTarget);
    if (!valid) return;
    twoFactorMutation.mutate({ challengeToken, code: twoFactorCode });
  };

  const pending = loginMutation.isPending || twoFactorMutation.isPending || resetRequestMutation.isPending || resetConfirmMutation.isPending;
  const submitLabel = {
    login: pending ? "Signing in..." : "Sign in",
    forgot: pending ? "Sending..." : "Send reset link",
    "reset-confirm": pending ? "Saving..." : "Set password",
    "2fa": pending ? "Verifying..." : "Verify and continue",
  }[mode];
  const onSubmit = { login: submitLogin, forgot: submitResetRequest, "reset-confirm": submitResetConfirm, "2fa": submitTwoFactor }[mode];
  const revealToggle = (
    <Button
      appearance="transparent"
      icon={showPassword ? <EyeOff20Regular /> : <Eye20Regular />}
      onClick={() => setShowPassword((value) => !value)}
      aria-label={showPassword ? "Hide password" : "Show password"}
    />
  );

  return (
    <main className="dwella-auth-page">
      <section className="dwella-auth-hero">
        <div className="dwella-auth-brand">
          <img src="/assets/images/logo/dwella-mark-white.png" alt="" />
          <strong>Dwella Suite</strong>
        </div>

        <AuthTour />

        <p className="dwella-auth-foot">Admin access only. Sessions are logged.</p>

        {/* Decorative: the house mark at low opacity, bleeding off the corner. */}
        <img className="dwella-auth-watermark" src="/assets/images/logo/dwella-mark-white.png" alt="" aria-hidden="true" />
      </section>

      <section className="dwella-auth-panel">
        {/* noValidate: validation is ours, so the browser must not pop its own
            bubbles for type="email" or the required attribute Fluent sets. */}
        <form className="dwella-auth-form" noValidate onSubmit={onSubmit}>
          {/* Replaces the hero below 1080px, where the brand panel is hidden. */}
          <div className="dwella-auth-compact-brand">
            <img src="/assets/images/logo/dwella-mark.png" alt="" />
            <strong>Dwella Suite</strong>
          </div>

          <div className="dwella-auth-heading">
            <h1>{heading}</h1>
            <p>{blurb}</p>
          </div>

          <div className="dwella-auth-fields">
            {mode === "2fa" ? (
              <Field label="Authentication code" {...fieldProps("twoFactorCode")} className={`dwella-otp-field ${fieldProps("twoFactorCode").className || ""}`}>
                <Input
                  name="otp"
                  autoComplete="one-time-code"
                  inputMode="numeric"
                  maxLength={6}
                  autoFocus
                  value={twoFactorCode}
                  onChange={(_, data) => { setTwoFactorCode(data.value.replace(/\D/g, "")); clearError("twoFactorCode"); }}
                />
              </Field>
            ) : mode === "reset-confirm" ? (
              <Field label="New password" {...fieldProps("resetPassword")}>
                <Input
                  name="new-password"
                  autoComplete="new-password"
                  type={showPassword ? "text" : "password"}
                  autoFocus
                  value={resetPassword}
                  onChange={(_, data) => { setResetPassword(data.value); clearError("resetPassword"); }}
                  contentAfter={revealToggle}
                />
              </Field>
            ) : (
              <>
                <Field label="Email address" {...fieldProps("email")}>
                  <Input
                    name="email"
                    autoComplete="email"
                    type="email"
                    autoFocus
                    placeholder="you@company.com"
                    value={email}
                    onChange={(_, data) => { setEmail(data.value); clearError("email"); }}
                  />
                </Field>

                {mode === "login" ? (
                  <Field
                    {...fieldProps("password")}
                    label={{
                      children: (
                        <span className="dwella-auth-label-row">
                          <span>Password</span>
                          {/* A quiet inline link beside the field it concerns,
                              rather than a second block button competing with
                              the primary action below. */}
                          <button type="button" className="dwella-text-link" onClick={() => switchMode("forgot")}>
                            Forgot password?
                          </button>
                        </span>
                      ),
                    }}
                  >
                    <Input
                      name="password"
                      autoComplete="current-password"
                      type={showPassword ? "text" : "password"}
                      value={password}
                      onChange={(_, data) => { setPassword(data.value); clearError("password"); }}
                      contentAfter={revealToggle}
                    />
                  </Field>
                ) : null}
              </>
            )}
          </div>

          <Button className="dwella-auth-submit" appearance="primary" type="submit" disabled={pending}>
            {submitLabel}
          </Button>

          {mode !== "login" ? (
            <button type="button" className="dwella-text-link dwella-auth-alt" onClick={() => switchMode("login")}>
              <ArrowLeft16Regular />
              Back to sign in
            </button>
          ) : null}
        </form>
      </section>
    </main>
  );
};

export default Signin;
