import React, { useEffect, useRef, useState } from "react";
import { Button, Field, Input, Select, Textarea } from "@fluentui/react-components";
import { useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "react-toastify";

import { isNotLinked, usePortalProfile, useUpdatePortalProfile } from "../../Services/portal";
import { PageSection } from "../../shared/components";
import { useFormErrors } from "../../shared/useFormErrors";

export const RECEIPT_DETAILS_ID = "receipt-details";

const INDIVIDUAL = ["national_id", "identity_type", "identity_country"];
const COMPANY = ["company_registration", "representative_name", "representative_phone"];
const FIELDS = ["tpin", "billing_address", ...INDIVIDUAL, ...COMPANY];
const LOCKED_HINT = "Already recorded. Ask your property manager to correct it.";

// Only return to pages inside the tenant's own payments area.
const safeReturn = (value) => (value && /^\/billing\/receipts\/[\w-]+$/.test(value) ? value : "");

// The details Dwella prints on receipts. TPIN and billing address are always
// the tenant's to keep current; identity and company details can be filled in
// while blank and are corrected by the property manager afterwards.
export default function ReceiptDetails() {
  const query = usePortalProfile();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const returnTo = safeReturn(params.get("return"));
  const sectionRef = useRef(null);
  const [form, setForm] = useState(null);
  const { validate, clearError, fieldProps, showServerErrors } = useFormErrors();

  useEffect(() => {
    if (query.data) setForm(Object.fromEntries(FIELDS.map((key) => [key, query.data[key] || ""])));
  }, [query.data]);

  // Arriving from a blocked receipt: bring this section into view.
  useEffect(() => {
    if (form && params.get("section") === RECEIPT_DETAILS_ID) {
      sectionRef.current?.scrollIntoView({ block: "start" });
      sectionRef.current?.querySelector("input, textarea")?.focus({ preventScroll: true });
    }
  }, [Boolean(form), params]); // eslint-disable-line react-hooks/exhaustive-deps

  const mutation = useUpdatePortalProfile({
    onSuccess: (data) => {
      if (!data.missing_details?.length && returnTo) {
        toast.success("Details saved. Your receipt is ready.");
        navigate(returnTo, { replace: true });
        return;
      }
      toast.success("Receipt details saved.");
    },
    onError: (error) => {
      if (!showServerErrors(error.data, FIELDS)) toast.error(error.message || "Could not save your details.");
    },
  });

  if (query.isLoading || isNotLinked(query.error) || query.isError || !form) return null;
  const profile = query.data;
  const locked = new Set(profile.locked_fields || []);
  const company = profile.tenant_type === "company";
  const missing = profile.missing_details || [];
  const shown = ["tpin", "billing_address", ...(company ? COMPANY : INDIVIDUAL)];
  const changed = shown.filter((key) => !locked.has(key) && form[key].trim() !== (profile[key] || ""));

  const update = (name, value) => { setForm((current) => ({ ...current, [name]: value })); clearError(name); };
  const lockedProps = (name) => (locked.has(name) ? { readOnly: true } : {});
  const hint = (name, normal) => (locked.has(name) ? LOCKED_HINT : normal);

  const submit = (event) => {
    event.preventDefault();
    const ok = validate({
      tpin: () => (form.tpin.trim() && !/^[0-9]{10}$/.test(form.tpin.trim()) ? "A TPIN is 10 digits." : ""),
      billing_address: () => (form.billing_address.length > 1000 ? "Keep the address under 1,000 characters." : ""),
      identity_country: () => (!company && !locked.has("identity_country") && !/^[A-Za-z]{2}$/.test(form.identity_country.trim())
        ? "Use a two-letter country code, for example ZM." : ""),
    }, event.currentTarget);
    if (!ok) return;
    mutation.mutate(Object.fromEntries(changed.map((key) => [key, form[key].trim()])));
  };

  return (
    <div id={RECEIPT_DETAILS_ID} ref={sectionRef} className="dwella-anchor-target">
      <PageSection
        className="dwella-profile-section"
        title="Receipt details"
        note={missing.length
          ? `Needed before your receipts can be issued: ${missing.map((item) => item.label).join(", ")}.`
          : "Printed on your receipts. Keep your TPIN and billing address current."}
      >
        <form noValidate onSubmit={submit}>
          <div className="dwella-form-grid">
            <Field label="TPIN" hint="10 digits, from your ZRA registration." {...fieldProps("tpin")}>
              <Input inputMode="numeric" maxLength={10} value={form.tpin} onChange={(_, d) => update("tpin", d.value.replace(/\D/g, ""))} />
            </Field>
            {company ? <>
              <Field label="Company registration" hint={hint("company_registration")} {...fieldProps("company_registration")}>
                <Input maxLength={80} value={form.company_registration} {...lockedProps("company_registration")} onChange={(_, d) => update("company_registration", d.value)} />
              </Field>
              <Field label="Authorised representative" hint={hint("representative_name")} {...fieldProps("representative_name")}>
                <Input maxLength={180} value={form.representative_name} {...lockedProps("representative_name")} onChange={(_, d) => update("representative_name", d.value)} />
              </Field>
              <Field label="Representative phone" hint={hint("representative_phone")} {...fieldProps("representative_phone")}>
                <Input type="tel" inputMode="tel" maxLength={20} value={form.representative_phone} {...lockedProps("representative_phone")} onChange={(_, d) => update("representative_phone", d.value)} />
              </Field>
            </> : <>
              <Field label="Identity document" hint={hint("identity_type")} {...fieldProps("identity_type")}>
                <Select value={form.identity_type || "nrc"} disabled={locked.has("identity_type")} onChange={(_, d) => update("identity_type", d.value)}>
                  <option value="nrc">NRC</option>
                  <option value="passport">Passport</option>
                  <option value="other">Other identity document</option>
                </Select>
              </Field>
              <Field label="Identity document number" hint={hint("national_id", "Kept off invoices and notices.")} {...fieldProps("national_id")}>
                <Input maxLength={40} value={form.national_id} {...lockedProps("national_id")} onChange={(_, d) => update("national_id", d.value)} />
              </Field>
              <Field label="Issuing country" hint={hint("identity_country", "Two-letter code, for example ZM.")} {...fieldProps("identity_country")}>
                <Input maxLength={2} value={form.identity_country} {...lockedProps("identity_country")} onChange={(_, d) => update("identity_country", d.value.toUpperCase())} />
              </Field>
            </>}
            <Field className="dwella-field-wide" label="Billing address" hint="The address printed on your receipts." {...fieldProps("billing_address")}>
              <Textarea resize="vertical" maxLength={1000} value={form.billing_address} onChange={(_, d) => update("billing_address", d.value)} />
            </Field>
          </div>
          <footer>
            <Button appearance="primary" type="submit" disabled={mutation.isPending || !changed.length}>
              {mutation.isPending ? "Saving…" : returnTo ? "Save and view receipt" : "Save details"}
            </Button>
          </footer>
        </form>
      </PageSection>
    </div>
  );
}
