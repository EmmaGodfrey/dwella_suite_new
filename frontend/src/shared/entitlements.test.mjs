import assert from "node:assert/strict";
import test from "node:test";
import { canAddRecords, canUseFeature } from "./entitlements.js";

test("unknown, denied and loading capabilities do not grant access", () => {
  assert.equal(canUseFeature(undefined, "bulk_imports"), false);
  assert.equal(canUseFeature({ features: {} }, "bulk_imports"), false);
  assert.equal(canUseFeature({ features: { bulk_imports: { enabled: false } } }, "bulk_imports"), false);
});

test("explicit feature access and expiry determine the UI hint", () => {
  const state = value => ({ features: { bulk_imports: value } });
  assert.equal(canUseFeature(state({ enabled: true, expires_at: null }), "bulk_imports"), true);
  assert.equal(canUseFeature(state({ enabled: true, expires_at: "2030-01-01T00:00:00Z" }), "bulk_imports", 0), true);
  assert.equal(canUseFeature(state({ enabled: true, expires_at: "2000-01-01T00:00:00Z" }), "bulk_imports"), false);
  assert.equal(canUseFeature(state({ enabled: true, expires_at: "bad" }), "bulk_imports"), false);
});

test("capacity hints support unlimited, exact and exceeded limits", () => {
  const state = (limit, used) => ({ limits: { units: { limit, used } } });
  assert.equal(canAddRecords(state(null, 100), "units"), true);
  assert.equal(canAddRecords(state(5, 4), "units"), true);
  assert.equal(canAddRecords(state(5, 5), "units"), false);
  assert.equal(canAddRecords(state(2, 5), "units"), false);
  assert.equal(canAddRecords(state(5, 3), "units", 2), true);
  assert.equal(canAddRecords(state(5, 3), "units", 3), false);
});

test("missing/malformed capacity and invalid batch sizes do not grant access", () => {
  assert.equal(canAddRecords(undefined, "units"), false);
  assert.equal(canAddRecords({ limits: { units: { used: 0 } } }, "units"), false);
  assert.equal(canAddRecords({ limits: { units: { limit: null, used: 0 } } }, "units", -1), false);
  assert.equal(canAddRecords({ limits: { units: { limit: null, used: 0 } } }, "units", 1.2), false);
});
