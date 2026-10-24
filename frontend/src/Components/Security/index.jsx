import React, { useState } from "react";
import "./security.scss";
import { Button, Field, Input } from "@fluentui/react-components";
import { CheckmarkCircle24Regular, Key24Regular, Shield24Regular, ShieldDismiss24Regular } from "@fluentui/react-icons";
import { toast } from "react-toastify";

import { useCurrentUserQuery } from "../../Services/queries";
import { useTwoFactorDisableMutation, useTwoFactorSetupMutation, useTwoFactorSetupVerifyMutation } from "../../Services/mutations";
import { PageSection } from "../../shared/components";
import { FormModal } from "../../shared/components/FormFlow";
import { useFormErrors } from "../../shared/useFormErrors";
import { Link } from "react-router-dom";
import { QRCodeSVG } from "qrcode.react";

const Security = () => {
  const [setup, setSetup] = useState(null);
  const [code, setCode] = useState("");
  const [removing, setRemoving] = useState(false);
  const [password, setPassword] = useState("");
  const [removalCode, setRemovalCode] = useState("");
  const [keyCopied, setKeyCopied] = useState(false);
  const errors = useFormErrors();
  const { data: user } = useCurrentUserQuery();
  const setupMutation = useTwoFactorSetupMutation({
    onSuccess: setSetup,
    onError: (error) => toast.error(error.message || "Could not start 2FA setup"),
  });
  const verifyMutation = useTwoFactorSetupVerifyMutation({
    onSuccess: () => {
      setSetup(null);
      setCode("");
      setKeyCopied(false);
      setupMutation.reset();
      toast.success("Two-factor authentication enabled.");
    },
    onError: (error) => toast.error(error.message || "Invalid authentication code"),
  });
  const disableMutation = useTwoFactorDisableMutation({
    onSuccess: () => { setRemoving(false); setPassword(""); setRemovalCode(""); toast.success("Two-factor authentication disabled."); },
    onError: (error) => errors.showServerErrors(error.data, ["password", "code"]),
  });

  return (
    <div className="dwella-screen dwella-security-screen" data-tour="security-settings">
      {user && !user.email_verification?.verified ? <div className="dwella-verification-note"><p>Verify {user.email} to confirm access to your mailbox.</p><Button as={Link} to="/verify-email">Verify email</Button></div> : null}
      <PageSection
        className="dwella-security-overview"
        title="Account protection"
        note="Manage sign-in protections for your account."
        actions={
          <span className={`dwella-security-emblem ${user?.has_two_factor ? "enabled" : ""}`}>{user?.has_two_factor ? <Shield24Regular /> : <ShieldDismiss24Regular />}</span>
        }
      >
        <div className={`dwella-security-status ${user?.has_two_factor ? "is-enabled" : ""}`}>
          <span className="dwella-security-status-icon">
            {user?.has_two_factor ? <CheckmarkCircle24Regular /> : <Key24Regular />}
          </span>
          <div>
            <h3>Two-factor authentication</h3>
            <p>{user?.has_two_factor ? "Authenticator verification is required when this account signs in." : "Require an authenticator code after the password step."}</p>
          </div>
          {user?.has_two_factor ? (
            <Button appearance="secondary" onClick={() => { errors.clearAll(); disableMutation.reset(); setRemoving(true); }}>Disable 2FA</Button>
          ) : (
            <Button appearance="primary" disabled={setupMutation.isPending || Boolean(setup)} onClick={() => setupMutation.mutate()}>{setupMutation.isPending ? "Starting..." : "Set up 2FA"}</Button>
          )}
        </div>

        <div className="dwella-security-facts" aria-label="Account security details">
          <div><span>Password</span><strong>Configured</strong></div>
          <div><span>Identity review</span><strong>{user?.identity_verification?.status?.replace(/_/g, " ") || "Not submitted"}</strong></div>
          <div><span>Second factor</span><strong>{user?.has_two_factor ? "Active" : "Not active"}</strong></div>
        </div>

        {setup ? (
          <div className="dwella-setup-box">
            <Key24Regular />
            <div>
              <h3>Connect your authenticator</h3>
              <p>Scan this QR code with your authenticator app, then enter the 6-digit code it shows.</p>
              <div className="dwella-authenticator-qr">
                <QRCodeSVG value={setup.provisioning_uri} size={208} marginSize={4} level="M" bgColor="#ffffff" fgColor="#000000" role="img" title="Scan this QR code with your authenticator app" />
              </div>
              <details className="dwella-authenticator-manual">
                <summary>Can’t scan? Enter a setup key</summary>
                <p>On this phone? Add an account manually in your authenticator. Choose a time-based code.</p>
                <div className="dwella-security-code"><span>Account</span><code>{user?.email}</code><span>Issuer</span><code>Dwella Suite</code><span>Setup key</span><code>{setup.secret}</code></div>
                <Button appearance="subtle" onClick={async () => {
                  try { await navigator.clipboard.writeText(setup.secret); setKeyCopied(true); }
                  catch { toast.error("Could not copy the key. Select it and copy it manually."); }
                }}>Copy setup key</Button>
                {keyCopied ? <p role="status">Setup key copied.</p> : null}
              </details>
              <Field label="6-digit code" hint="From your authenticator app.">
                <Input inputMode="numeric" autoComplete="one-time-code" maxLength={6} value={code} onChange={(_, data) => setCode(data.value.replace(/\D/g, ""))} />
              </Field>
              <Button appearance="primary" disabled={verifyMutation.isPending || code.length !== 6} onClick={() => verifyMutation.mutate({ code })}>{verifyMutation.isPending ? "Verifying..." : "Verify 2FA"}</Button>
              <Button appearance="subtle" disabled={verifyMutation.isPending} onClick={() => { setSetup(null); setCode(""); setKeyCopied(false); setupMutation.reset(); }}>Cancel</Button>
            </div>
          </div>
        ) : null}
      </PageSection>
      {removing ? <FormModal title="Turn off two-factor authentication?" description="Confirm your current password and authenticator code to remove this protection." busy={disableMutation.isPending} errors={errors.errors} submitLabel="Turn off 2FA" onClose={() => { setRemoving(false); setPassword(""); setRemovalCode(""); }} onSubmit={(event) => {
        event.preventDefault();
        if (!errors.validate({ password: () => password ? "" : "Enter your current password.", code: () => /^\d{6}$/.test(removalCode) ? "" : "Enter your current 6-digit code." }, event.currentTarget)) return;
        disableMutation.mutate({ password, code: removalCode });
      }}>
        <Field label="Current password" {...errors.fieldProps("password")}><Input type="password" autoComplete="current-password" maxLength={128} value={password} onChange={(_, d) => { setPassword(d.value); errors.clearError("password"); }} /></Field>
        <Field label="Authenticator code" {...errors.fieldProps("code")}><Input inputMode="numeric" autoComplete="one-time-code" maxLength={6} value={removalCode} onChange={(_, d) => { setRemovalCode(d.value.replace(/\D/g, "")); errors.clearError("code"); }} /></Field>
        {disableMutation.isError ? <p role="alert">{disableMutation.error.message}</p> : null}
      </FormModal> : null}
    </div>
  );
};

export default Security;
