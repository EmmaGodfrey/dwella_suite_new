import React, { useState } from "react";
import { Key, Shield, ShieldOff } from "react-feather";
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
      <section className="dwella-card dwella-panel security-panel">
        <header className="dwella-panel-heading">
          <div>
            <h2>Account Protection</h2>
            <p>Manage sign-in protections for your admin account.</p>
          </div>
          <span className={`dwella-security-emblem ${user?.has_two_factor ? "enabled" : ""}`}>
            {user?.has_two_factor ? <Shield size={22} /> : <ShieldOff size={22} />}
          </span>
        </header>
        <div className="dwella-security-row">
          <div>
            <h3>Two-Factor Authentication</h3>
            <p>{user?.has_two_factor ? "2FA is enabled for this account." : "Add an authenticator code before account access is granted."}</p>
          </div>
          {user?.has_two_factor ? (
            <button className="dwella-danger-action" disabled={disableMutation.isPending} onClick={() => disableMutation.mutate()} type="button">
              Disable
            </button>
          ) : (
            <button className="dwella-primary-action compact" disabled={setupMutation.isPending} onClick={() => setupMutation.mutate()} type="button">
              {setupMutation.isPending ? "Starting..." : "Set Up 2FA"}
            </button>
          )}
        </div>

        {setup ? (
          <div className="dwella-setup-box">
            <Key size={18} />
            <div>
              <p><strong>Secret:</strong> <code>{setup.secret}</code></p>
              <p><strong>Authenticator URI:</strong> <code>{setup.provisioning_uri}</code></p>
              <label className="dwella-field">
                <span>6-digit code</span>
                <input inputMode="numeric" maxLength="6" value={code} onChange={(event) => setCode(event.target.value.replace(/\D/g, ""))} />
              </label>
              <button className="dwella-primary-action compact" disabled={verifyMutation.isPending} onClick={() => verifyMutation.mutate({ code })} type="button">
                {verifyMutation.isPending ? "Verifying..." : "Verify 2FA"}
              </button>
            </div>
          </div>
        ) : null}
      </section>
    </div>
  );
};

export default Security;
