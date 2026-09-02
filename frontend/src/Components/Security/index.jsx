import React, { useState } from "react";
import { Button, Card, Field, Input, Text, Title3 } from "@fluentui/react-components";
import { Key24Regular, Shield24Regular, ShieldDismiss24Regular } from "@fluentui/react-icons";
import { toast } from "react-toastify";

import { useCurrentUserQuery } from "../../Services/queries";
import { useTwoFactorDisableMutation, useTwoFactorSetupMutation, useTwoFactorSetupVerifyMutation } from "../../Services/mutations";

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
      <Card className="dwella-card dwella-panel security-panel" appearance="outline">
        <header className="dwella-panel-heading">
          <div><Title3>Account Protection</Title3><Text>Manage sign-in protections for your admin account.</Text></div>
          <span className={`dwella-security-emblem ${user?.has_two_factor ? "enabled" : ""}`}>{user?.has_two_factor ? <Shield24Regular /> : <ShieldDismiss24Regular />}</span>
        </header>
        <div className="dwella-security-row">
          <div>
            <Title3>Two-Factor Authentication</Title3>
            <Text>{user?.has_two_factor ? "2FA is enabled for this account." : "Add an authenticator code before account access is granted."}</Text>
          </div>
          {user?.has_two_factor ? (
            <Button appearance="primary" disabled={disableMutation.isPending} onClick={() => disableMutation.mutate()}>Disable</Button>
          ) : (
            <Button appearance="primary" disabled={setupMutation.isPending} onClick={() => setupMutation.mutate()}>{setupMutation.isPending ? "Starting..." : "Set Up 2FA"}</Button>
          )}
        </div>

        {setup ? (
          <div className="dwella-setup-box">
            <Key24Regular />
            <div>
              <Text><strong>Secret:</strong> <code>{setup.secret}</code></Text>
              <Text><strong>Authenticator URI:</strong> <code>{setup.provisioning_uri}</code></Text>
              <Field label="6-digit code">
                <Input inputMode="numeric" maxLength={6} value={code} onChange={(_, data) => setCode(data.value.replace(/\D/g, ""))} />
              </Field>
              <Button appearance="primary" disabled={verifyMutation.isPending} onClick={() => verifyMutation.mutate({ code })}>{verifyMutation.isPending ? "Verifying..." : "Verify 2FA"}</Button>
            </div>
          </div>
        ) : null}
      </Card>
    </div>
  );
};

export default Security;
