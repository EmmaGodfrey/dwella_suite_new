export const tenantFields = ["full_name", "phone_number", "email", "national_id", "tpin", "notes",
  "tenant_type", "identity_type", "identity_country", "billing_address", "company_registration",
  "representative_name", "representative_phone"];
export const missingTenantDetails = (tenant) => ["full_name", "phone_number", "tpin", "billing_address",
  ...(tenant.tenant_type === "company" ? ["company_registration", "representative_name", "representative_phone"] : ["national_id", "identity_country"])]
  .filter(key => !tenant[key]?.trim());
export const detailLabel = key => ({ tpin: "TPIN", national_id: "Identity document number", billing_address: "Billing address",
  representative_name: "Authorised representative", representative_phone: "Representative phone", company_registration: "Company registration",
  full_name: "Full legal name", phone_number: "Phone", identity_country: "Identity issuing country" }[key] || key);
