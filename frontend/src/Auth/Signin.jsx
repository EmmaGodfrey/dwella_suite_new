import React, { useMemo, useState } from "react";
import { ArrowLeft, Eye, EyeOff, Lock, Mail, Shield } from "react-feather";
import { useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "react-toastify";

import {
  useLoginMutation,
  usePasswordResetConfirmMutation,
  usePasswordResetRequestMutation,
  useTwoFactorLoginMutation,
} from "../Services/mutations";

const disposableDomains = new Set([
  "10minutemail.com",
  "guerrillamail.com",
  "mailinator.com",
  "tempmail.com",
  "temp-mail.org",
  "throwawaymail.com",
  "yopmail.com",
]);

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
          <span>
            <img src="/assets/images/logo/dwella-icon.png" alt="" />
          </span>
          <div>
            <strong>Dwella Suite</strong>
            <small>Property OS</small>
          </div>
        </div>
        <div>
          <p className="dwella-kicker">Built for property operators</p>
          <h1>One calm workspace for the messy business of managing property.</h1>
          <p>
            Track portfolio health, tenants, leases, maintenance, payments, reports, and admin security
            without carrying template clutter into the product.
          </p>
        </div>
      </section>

      <section className="dwella-auth-panel">
        <form className="dwella-auth-card" onSubmit={mode === "forgot" ? submitResetRequest : mode === "reset-confirm" ? submitResetConfirm : mode === "2fa" ? submitTwoFactor : submitLogin}>
          <div className="dwella-auth-card-header">
            <span>{mode === "2fa" ? <Shield size={18} /> : <Lock size={18} />}</span>
            <div>
              <h2>{copy[0]}</h2>
              <p>{copy[1]}</p>
            </div>
          </div>

          {mode === "2fa" ? (
            <label className="dwella-field">
              <span>Authentication code</span>
              <input inputMode="numeric" maxLength="6" value={twoFactorCode} onChange={(event) => setTwoFactorCode(event.target.value.replace(/\D/g, ""))} />
            </label>
          ) : mode === "reset-confirm" ? (
            <label className="dwella-field">
              <span>New password</span>
              <div className="dwella-password-field">
                <input type={showPassword ? "text" : "password"} value={resetPassword} onChange={(event) => setResetPassword(event.target.value)} />
                <button type="button" onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? "Hide password" : "Show password"}>
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </label>
          ) : (
            <>
              <label className="dwella-field">
                <span>Email address</span>
                <div className="dwella-input-icon">
                  <Mail size={16} />
                  <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} />
                </div>
              </label>
              {mode === "login" ? (
                <label className="dwella-field">
                  <span>Password</span>
                  <div className="dwella-password-field">
                    <input type={showPassword ? "text" : "password"} value={password} onChange={(event) => setPassword(event.target.value)} />
                    <button type="button" onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? "Hide password" : "Show password"}>
                      {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                </label>
              ) : null}
            </>
          )}

          <button className="dwella-primary-action" type="submit" disabled={loginMutation.isPending || twoFactorMutation.isPending || resetRequestMutation.isPending || resetConfirmMutation.isPending}>
            {mode === "forgot"
              ? resetRequestMutation.isPending ? "Sending..." : "Send reset link"
              : mode === "reset-confirm"
                ? resetConfirmMutation.isPending ? "Saving..." : "Set password"
                : mode === "2fa"
                  ? twoFactorMutation.isPending ? "Verifying..." : "Verify and continue"
                  : loginMutation.isPending ? "Signing in..." : "Sign in"}
          </button>

          {mode === "login" ? (
            <button className="dwella-text-action" type="button" onClick={() => setMode("forgot")}>
              Forgot password?
            </button>
          ) : (
            <button className="dwella-text-action" type="button" onClick={() => setMode("login")}>
              <ArrowLeft size={15} />
              Back to sign in
            </button>
          )}
        </form>
      </section>
    </main>
  );
};

export default Signin;
