import test from "node:test";
import assert from "node:assert/strict";
import { firstErrorStep, ruleErrors } from "./formFlow.js";

const groups = [
  ["full_name", "email"],
  ["lease.unit", "lease.monthly_rent"],
  [],
];

test("nested lease API errors return to the lease step", () => {
  assert.equal(
    firstErrorStep(
      { lease: { unit: ["This unit is already occupied."] } },
      groups,
      2,
    ),
    1,
  );
});

test("the earliest affected step wins regardless of server error ordering", () => {
  assert.equal(
    firstErrorStep(
      {
        lease: { monthly_rent: ["Invalid amount."] },
        email: ["Invalid email."],
      },
      groups,
      2,
    ),
    0,
  );
});

test("non-field errors stay on the current step", () => {
  assert.equal(
    firstErrorStep({ non_field_errors: ["Please retry."] }, groups, 2),
    2,
  );
  assert.equal(firstErrorStep(null, groups, 1), 1);
});

test("final validation can identify a field on an earlier step", () => {
  const found = ruleErrors({
    full_name: () => "",
    email: () => "Enter a valid email.",
    "lease.unit": () => "",
  });
  assert.deepEqual(found, { email: "Enter a valid email." });
  assert.equal(firstErrorStep(found, groups, 2), 0);
  assert.deepEqual(ruleErrors({ email: () => "" }), {});
});
