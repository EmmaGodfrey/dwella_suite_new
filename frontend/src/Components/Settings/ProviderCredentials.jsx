import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Button, Field, Input } from "@fluentui/react-components";
import { toast } from "react-toastify";
import { useProviderCredentials, useReplaceProviderCredentials } from "../../Services/providerCredentials";
import { useCurrentUserQuery } from "../../Services/queries";
import { FormDrawer } from "../../shared/components/FormFlow";
import { useFormErrors } from "../../shared/useFormErrors";
import { AdminState } from "../Platform/AdminUI";

const providers = [
  { id: "sms", name: "Africa's Talking", purpose: "SMS" },
  { id: "email", name: "Resend", purpose: "Email" },
  { id: "whatsapp", name: "WhatsApp Business", purpose: "Messages and callbacks" },
];

function ReplacementDrawer({ provider, fields, onClose }) {
  const empty = () => Object.fromEntries(fields.map(field => [field.name, ""]));
  const [values, setValues] = useState(empty);
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [failure, setFailure] = useState("");
  const errors = useFormErrors();
  const mutation = useReplaceProviderCredentials();
  const submit = (event) => {
    event.preventDefault();
    if (mutation.isPending) return;
    const selected = Object.fromEntries(Object.entries(values).filter(([, value]) => value !== ""));
    const rules = {
      values: () => Object.keys(selected).length ? "" : "Enter at least one replacement credential.",
      password: () => password ? "" : "Enter your current password.",
      code: () => /^[0-9]{6}$/.test(code) ? "" : "Enter your six-digit authenticator code.",
    };
    for (const field of fields) rules[field.name] = () => {
      const value = values[field.name];
      return !value || (value.length >= field.min_length && value.length <= field.max_length && /^[\x21-\x7E]+$/.test(value))
        ? "" : `Use ${field.min_length}–${field.max_length} characters without spaces.`;
    };
    if (!errors.validate(rules, event.currentTarget)) return;
    setFailure("");
    mutation.mutate({ values: selected, password, code }, {
      onSuccess: () => { toast.success(`${provider.name} credentials replaced.`); onClose(); },
      onError: error => setFailure(error.message || "Could not replace credentials. Enter the values again to retry."),
      onSettled: () => { setValues(empty()); setPassword(""); setCode(""); },
    });
  };
  return <FormDrawer title={`Replace ${provider.name} credentials`}
    description="Saved values stay hidden. Use credentials from the same provider account and environment."
    onClose={onClose} onSubmit={submit} busy={mutation.isPending} errors={errors.errors}
    submitLabel="Replace credentials" pendingLabel="Replacing…"
    notice={failure ? <p role="alert" className="dwella-field-error">{failure} Re-enter the credentials and a fresh code to try again.</p> : null}>
    <div className="admin-fields">
      <p className="dwella-muted-copy">Enter the values you want to replace. Blank fields keep their current value.</p>
      {fields.map(field => <Field key={field.name} label={`New ${field.label.toLowerCase()}`} hint={field.configured ? "A value is already configured." : "Not configured yet."} {...errors.fieldProps(field.name)}>
        <Input type="password" autoComplete="new-password" spellCheck={false} maxLength={field.max_length}
          value={values[field.name]} onChange={(_, data) => { setValues(current => ({ ...current, [field.name]: data.value })); errors.clearError(field.name); errors.clearError("values"); }} />
      </Field>)}
      {errors.errors.values && <p role="alert" className="dwella-field-error">{errors.errors.values}</p>}
      <Field label="Current password" required {...errors.fieldProps("password")}>
        <Input type="password" autoComplete="current-password" maxLength={128} value={password} onChange={(_, data) => { setPassword(data.value); errors.clearError("password"); }} />
      </Field>
      <Field label="Authenticator code" required hint="Use a fresh code for each replacement." {...errors.fieldProps("code")}>
        <Input autoComplete="one-time-code" inputMode="numeric" maxLength={6} value={code} onChange={(_, data) => { setCode(data.value); errors.clearError("code"); }} />
      </Field>
    </div>
  </FormDrawer>;
}

export default function ProviderCredentials() {
  const query = useProviderCredentials();
  const user = useCurrentUserQuery();
  const [chosen, setChosen] = useState(null);
  const confirmed = Boolean(user.data?.has_two_factor);
  return <section className="settings-section">
    <header><div><h2>Provider credentials</h2><p>Replace API keys and callback credentials for this environment. Changes apply to the next provider operation.</p></div></header>
    <AdminState query={query}>{query.data && <>
      <div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>Provider</th><th>Credentials</th><th>Action</th></tr></thead><tbody>
        {providers.map(provider => {
          const fields = query.data.credentials.filter(field => field.provider === provider.id);
          return <tr key={provider.id}><td><strong>{provider.name}</strong><div className="dwella-muted-copy">{provider.purpose}</div></td>
            <td>{fields.filter(field => field.configured).length} of {fields.length} configured</td>
            <td><Button size="small" disabled={!query.data.replacement_available || !confirmed} aria-label={`Replace ${provider.name} credentials`} onClick={() => setChosen(provider)}>Replace</Button></td></tr>;
        })}
      </tbody></table></div>
      {!query.data.replacement_available && <p role="status">Secure credential storage needs to be configured for this environment.</p>}
      {!confirmed && <p role="status"><Link to="/settings?tab=security">Set up your authenticator</Link> to replace provider credentials.</p>}
      {chosen && <ReplacementDrawer provider={chosen} fields={query.data.credentials.filter(field => field.provider === chosen.id)} onClose={() => setChosen(null)} />}
    </>}</AdminState>
  </section>;
}
