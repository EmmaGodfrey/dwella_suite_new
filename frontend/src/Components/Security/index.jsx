import React, { useState } from "react";
import "./security.scss";
import { Button, Field, Input } from "@fluentui/react-components";
import { CheckmarkCircle24Regular, Key24Regular, Shield24Regular, ShieldDismiss24Regular } from "@fluentui/react-icons";
import { toast } from "react-toastify";

import { useCurrentUserQuery } from "../../Services/queries";
import { useTwoFactorDisableMutation, useTwoFactorSetupMutation, useTwoFactorSetupVerifyMutation } from "../../Services/mutations";
import { PageSection } from "../../shared/components";

const Security = () => {
  const [setup, setSetup] = useState(null);
  const [code, setCode] = useState("");
  const { data: user } = useCurrentUserQuery();
  const setupMutation = useTwoFactorSetupMutation({
    onSuccess: setSetup,
    onError: (error) => toast.error(error.message || "Could not start 2FA setup"),
  });
  const verifyMutation = useTwoFactorSetupVerifyMutation({
    onSuccess: () => {
      setSetup(null);
      setCode("");
      toast.success("Two-factor authentication enabled.");
    },
    onError: (error) => toast.error(error.message || "Invalid authentication code"),
  });
  const disableMutation = useTwoFactorDisableMutation({
    onSuccess: () => toast.success("Two-factor authentication disabled."),
    onError: (error) => toast.error(error.message || "Could not disable 2FA"),
  });

  return (
    <div className="dwella-screen dwella-security-screen">
      <PageSection
        className="dwella-security-overview"
        title="Account protection"
        note="Manage sign-in protections for your admin account."
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
            <Button appearance="secondary" disabled={disableMutation.isPending} onClick={() => disableMutation.mutate()}>Disable 2FA</Button>
          ) : (
            <Button appearance="primary" disabled={setupMutation.isPending} onClick={() => setupMutation.mutate()}>{setupMutation.isPending ? "Starting..." : "Set up 2FA"}</Button>
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
              <p>Enter this secret manually or use the provisioning URI in your authenticator app.</p>
              <div className="dwella-security-code"><span>Secret</span><code>{setup.secret}</code></div>
              <div className="dwella-security-code"><span>Authenticator URI</span><code>{setup.provisioning_uri}</code></div>
              <Field label="6-digit code" hint="From your authenticator app.">
                <Input inputMode="numeric" maxLength={6} value={code} onChange={(_, data) => setCode(data.value.replace(/\D/g, ""))} />
              </Field>
              <Button appearance="primary" disabled={verifyMutation.isPending || code.length !== 6} onClick={() => verifyMutation.mutate({ code })}>{verifyMutation.isPending ? "Verifying..." : "Verify 2FA"}</Button>
            </div>
          </div>
        ) : null}
      </PageSection>
    </div>
  );
};

export default Security;
