import test from "node:test";
import assert from "node:assert/strict";
import { missingTenantDetails } from "./tenantDetails.mjs";
import { correctionCsv } from "./importCorrections.mjs";

test("individual and company checklists use their own identity requirements", () => {
  const person = { full_name: "Jane Banda", phone_number: "+260971234567", tpin: "0123456789", billing_address: "Plot 1", national_id: "P1", identity_country: "MW" };
  assert.deepEqual(missingTenantDetails(person), []);
  assert.deepEqual(missingTenantDetails({ ...person, tpin: " " }), ["tpin"]);
  assert.deepEqual(missingTenantDetails({ ...person, tenant_type: "company" }), ["company_registration", "representative_name", "representative_phone"]);
});
test("correction download retains text IDs and neutralises spreadsheet formulas", () => {
  const csv = correctionCsv([{status:"invalid",values:{full_name:"=HYPERLINK(1)",tpin:"0123456789"}},{status:"ready",values:{full_name:"Already imported"}}]);
  assert.match(csv, /"'=HYPERLINK\(1\)"/);
  assert.match(csv, /"0123456789"/);
  assert.ok(!csv.includes("Already imported"));
});
