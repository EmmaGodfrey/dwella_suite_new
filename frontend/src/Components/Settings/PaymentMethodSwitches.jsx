import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Button, Field, Input } from "@fluentui/react-components";
import { toast } from "react-toastify";
import { useSwitchPaymentMethods } from "../../Services/paymentSwitches";
import { useCurrentUserQuery } from "../../Services/queries";
import { FormDrawer } from "../../shared/components/FormFlow";
import { StatusBadge } from "../../shared/components";
import { useFormErrors } from "../../shared/useFormErrors";

const METHODS = [
  { key: "card", name: "Card payments", on: "card_enabled" },
  { key: "mobile_money", name: "Mobile-money payments", on: "mobile_money_enabled" },
];

function SwitchDrawer({ method, turnOn, onClose }) {
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [failure, setFailure] = useState("");
  const errors = useFormErrors();
  const mutation = useSwitchPaymentMethods();
  const verb = turnOn ? "on" : "off";
  const submit = (event) => {
    event.preventDefault();
    if (mutation.isPending) return;
    if (!errors.validate({
      password: () => password ? "" : "Enter your current password.",
      code: () => /^[0-9]{6}$/.test(code) ? "" : "Enter your six-digit authenticator code.",
    }, event.currentTarget)) return;
    setFailure("");
    mutation.mutate({ [method.key]: turnOn, password, code }, {
      onSuccess: () => { toast.success(`${method.name} switched ${verb}.`); onClose(); },
      onError: (error) => setFailure(error.message || "Could not change this switch."),
      onSettled: () => { setPassword(""); setCode(""); },
    });
  };
  return <FormDrawer title={`Switch ${method.name.toLowerCase()} ${verb}`}
    description={turnOn
      ? "Tenants will be able to pay by this method again."
      : "Tenants will no longer be offered this method. Payments already in progress are not cancelled."}
    onClose={onClose} onSubmit={submit} busy={mutation.isPending} errors={errors.errors}
    submitLabel={`Switch ${verb}`} pendingLabel="Saving…"
    notice={failure ? <p role="alert" className="dwella-field-error">{failure} Use a fresh code to try again.</p> : null}>
    <div className="admin-fields">
      <Field label="Current password" required {...errors.fieldProps("password")}>
        <Input type="password" autoComplete="current-password" maxLength={128} value={password}
          onChange={(_, data) => { setPassword(data.value); errors.clearError("password"); }} />
      </Field>
      <Field label="Authenticator code" required hint="Use a fresh code each time." {...errors.fieldProps("code")}>
        <Input autoComplete="one-time-code" inputMode="numeric" maxLength={6} value={code}
          onChange={(_, data) => { setCode(data.value); errors.clearError("code"); }} />
      </Field>
    </div>
  </FormDrawer>;
}

export default function PaymentMethodSwitches({ data }) {
  const user = useCurrentUserQuery();
  const [chosen, setChosen] = useState(null);
  const confirmed = Boolean(user.data?.has_two_factor);
  return <>
    {METHODS.map((method) => {
      const enabled = Boolean(data[method.on]);
      return <div key={method.key} className="settings-row">
        <div><strong>{method.name}</strong></div>
        <div>
          <StatusBadge color={enabled ? "success" : "subtle"}>{enabled ? "On" : "Off"}</StatusBadge>{" "}
          <Button size="small" disabled={!confirmed} aria-label={`Switch ${method.name.toLowerCase()} ${enabled ? "off" : "on"}`}
            onClick={() => setChosen({ method, turnOn: !enabled })}>{enabled ? "Switch off" : "Switch on"}</Button>
        </div>
      </div>;
    })}
    {!confirmed && <p role="status"><Link to="/settings?tab=security">Set up your authenticator</Link> to change payment switches.</p>}
    {chosen && <SwitchDrawer {...chosen} onClose={() => setChosen(null)} />}
  </>;
}
