import React, { useEffect, useState } from "react";
import { Button, Field, Input } from "@fluentui/react-components";
import { toast } from "react-toastify";

import { isNotLinked, usePortalProfile, useUpdatePortalProfile } from "../../Services/portal";
import { PageSection } from "../../shared/components";
import { useFormErrors } from "../../shared/useFormErrors";

// Same shape the API accepts: local Zambian numbers or +<country><number>.
const looksLikePhone = (value) => {
  const digits = value.replace(/\D/g, "");
  if (value.trim().startsWith("+")) return digits.length >= 8 && digits.length <= 15;
  return digits.length === 10 ? digits.startsWith("0") : digits.length === 9 || (digits.length === 12 && digits.startsWith("260"));
};

// The tenant record the property manager keeps. Only the phone number is the
// tenant's to change; the email is their sign-in and lease-signing address.
export default function ContactDetails() {
  const query = usePortalProfile();
  const [phone, setPhone] = useState("");
  const { validate, clearError, fieldProps, showServerErrors } = useFormErrors();
  useEffect(() => {
    if (query.data) setPhone(query.data.phone_number);
  }, [query.data]);
  const mutation = useUpdatePortalProfile({
    onSuccess: () => toast.success("Mobile number saved."),
    onError: (error) => {
      if (!showServerErrors(error.data, ["phone_number"])) toast.error(error.message || "Could not save the number.");
    },
  });
  if (query.isLoading || isNotLinked(query.error)) return null;
  if (query.isError) return null;
  const profile = query.data;
  const submit = (event) => {
    event.preventDefault();
    const ok = validate({
      phone_number: () => (looksLikePhone(phone) ? "" : "Enter a valid phone number, for example 097 123 4567."),
    }, event.currentTarget);
    if (ok) mutation.mutate({ phone_number: phone.trim() });
  };
  return (
    <PageSection className="dwella-profile-section" title="Contact details" note="What your property manager uses to reach you.">
      <form noValidate onSubmit={submit}>
        <div className="dwella-form-grid">
          <Field label="Mobile number" hint="Used for rent reminders and mobile money." {...fieldProps("phone_number")}>
            <Input type="tel" inputMode="tel" value={phone} onChange={(_, d) => { setPhone(d.value); clearError("phone_number"); }} />
          </Field>
          <Field label="Email" hint="Your sign-in and lease-signing address. Ask your property manager to change it.">
            <Input value={profile.email || "—"} readOnly />
          </Field>
        </div>
        <footer>
          <Button appearance="primary" type="submit" disabled={mutation.isPending || phone.trim() === profile.phone_number}>
            {mutation.isPending ? "Saving…" : "Save number"}
          </Button>
        </footer>
      </form>
    </PageSection>
  );
}
