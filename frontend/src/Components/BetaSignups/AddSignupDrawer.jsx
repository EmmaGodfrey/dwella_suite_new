import React, { useState } from "react";
import {
  Button,
  DrawerBody,
  DrawerFooter,
  DrawerHeader,
  DrawerHeaderTitle,
  Dropdown,
  Field,
  Input,
  Option,
  OverlayDrawer,
  Switch,
} from "@fluentui/react-components";
import { Dismiss24Regular } from "@fluentui/react-icons";
import { toast } from "react-toastify";

import { useCreateBetaApplicationMutation } from "../../Services/mutations";
import { useFormErrors } from "../../shared/useFormErrors";

// Same unit choices and phone rule as the dwella.properties form.
export const unitRanges = ["1–5", "6–20", "21–50", "51–200", "More than 200"];
const PHONE_PATTERN = /^\+?[\d\s-]{9,16}$/;
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const empty = { name: "", phone: "", email: "", units: "", town: "" };

// Sign someone up on their behalf, e.g. after a call or a DM. They then get the
// same emails as a website signup, including sign-in details on beta day.
export default function AddSignupDrawer({ emailsEnabled, onClose, onSaved }) {
  const [values, setValues] = useState(empty);
  const [sendWelcome, setSendWelcome] = useState(true);
  const [earlyAccess, setEarlyAccess] = useState(false);
  const { validate, clearError, fieldProps, showServerErrors } = useFormErrors();

  const mutation = useCreateBetaApplicationMutation({
    onSuccess: (data) => {
      toast.success(
        earlyAccess ? `${data.name} has early access. Their account setup email was sent.` : sendWelcome && emailsEnabled
          ? `${data.name} is signed up. Their welcome email is on its way.`
          : `${data.name} is signed up.`
      );
      onSaved?.(data);
    },
    onError: (error) => {
      if (!showServerErrors(error.data, Object.keys(empty))) toast.error(error.message || "Could not add the signup.");
    },
  });

  const set = (field) => (_, data) => {
    setValues((current) => ({ ...current, [field]: data.value ?? data.optionValue }));
    clearError(field);
  };

  const submit = (event) => {
    event.preventDefault();
    if (mutation.isPending) return;
    const rules = {
      name: () => (values.name.trim().length >= 2 ? "" : "Enter their name."),
      phone: () => (PHONE_PATTERN.test(values.phone.trim()) ? "" : "Enter a valid phone number."),
      email: () => (EMAIL_PATTERN.test(values.email.trim()) ? "" : "Enter their email. Every beta update is sent by email."),
      units: () => (values.units ? "" : "Choose roughly how many units."),
    };
    if (!validate(rules, event.currentTarget)) return;
    mutation.mutate({
      ...values,
      name: values.name.trim(),
      phone: values.phone.trim(),
      email: values.email.trim().toLowerCase(),
      town: values.town.trim(),
      send_welcome: !earlyAccess && sendWelcome,
      give_early_access: earlyAccess,
    });
  };

  return (
    <OverlayDrawer open position="end" size="medium" className="dwella-drawer" onOpenChange={(_, data) => !data.open && !mutation.isPending && onClose()}>
      <DrawerHeader>
        <DrawerHeaderTitle action={<Button appearance="subtle" aria-label="Close" icon={<Dismiss24Regular />} disabled={mutation.isPending} onClick={onClose} />}>
          Add a beta signup
        </DrawerHeaderTitle>
        <p className="dwella-drawer-note">They get the same emails as a website signup, and their sign-in details on beta day.</p>
      </DrawerHeader>
      <form id="beta-signup-form" noValidate onSubmit={submit} className="dwella-drawer-form">
        <DrawerBody>
          <fieldset disabled={mutation.isPending}>
            <section className="dwella-form-section">
              <div className="dwella-form-grid dwella-beta-signup-grid">
                <Field label="Full name" required {...fieldProps("name")}>
                  <Input maxLength={150} autoComplete="off" value={values.name} onChange={set("name")} />
                </Field>
                <Field label="Phone" required {...fieldProps("phone")}>
                  <Input type="tel" maxLength={16} placeholder="097 123 4567" value={values.phone} onChange={set("phone")} />
                </Field>
                <Field label="Email" required {...fieldProps("email")}>
                  <Input type="email" maxLength={254} placeholder="name@example.com" value={values.email} onChange={set("email")} />
                </Field>
                <Field label="Town" {...fieldProps("town")}>
                  <Input maxLength={120} placeholder="Lusaka" value={values.town} onChange={set("town")} />
                </Field>
                <Field label="Units" required {...fieldProps("units")}>
                  <Dropdown
                    placeholder="Choose a range"
                    selectedOptions={values.units ? [values.units] : []}
                    value={values.units}
                    onOptionSelect={set("units")}
                  >
                    {unitRanges.map((range) => <Option key={range} value={range}>{range}</Option>)}
                  </Dropdown>
                </Field>
              </div>
            </section>
            <section className="dwella-form-section">
              <Switch checked={earlyAccess} disabled={!emailsEnabled} onChange={(_, data) => setEarlyAccess(data.checked)} label="Give early access now" />
              {earlyAccess && <p className="dwella-drawer-note">Send a one-time account setup link immediately. Welcome and countdown emails stop.</p>}
              <Switch
                disabled={earlyAccess}
                checked={sendWelcome}
                onChange={(_, data) => setSendWelcome(data.checked)}
                label="Send the welcome email now"
              />
              {!emailsEnabled ? (
                <p className="dwella-drawer-note">
                  Beta emails are turned off on this server, so nothing is sent yet. Welcome emails go out once they are turned on.
                </p>
              ) : null}
            </section>
          </fieldset>
        </DrawerBody>
      </form>
      <DrawerFooter className="dwella-drawer-footer">
        <Button onClick={onClose} disabled={mutation.isPending}>Cancel</Button>
        <Button appearance="primary" type="submit" form="beta-signup-form" disabled={mutation.isPending}>
          {mutation.isPending ? "Adding…" : "Add signup"}
        </Button>
      </DrawerFooter>
    </OverlayDrawer>
  );
}
