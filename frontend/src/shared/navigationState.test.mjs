import test from "node:test";
import assert from "node:assert/strict";
import { matchesPath, moduleChildren, selectedDestination } from "./navigationState.mjs";

const manager = { persona: "landlord", can_manage_properties: true };
const item = (value, to, access = manager) => ({ value, to, children: moduleChildren(value, access) });
const selected = (parent, path, search) => selectedDestination([parent], path, search)?.destination.value;

test("tenant modules never expose manager sections", () => {
  for (const value of ["billing", "maintenance", "reports", "messages"]) {
    assert.deepEqual(moduleChildren(value, { persona: "tenant", can_manage_properties: true }), []);
  }
});
test("management capability controls payouts and vendors", () => {
  for (const [module, restricted] of [["billing", "Payouts"], ["maintenance", "Vendors"]]) {
    assert.ok(moduleChildren(module, manager).some(c => c.label === restricted));
    assert.ok(!moduleChildren(module, { persona: "platform_admin", can_manage_properties: false }).some(c => c.label === restricted));
  }
});
test("billing detail paths select the most specific child", () => {
  const billing = item("billing", "/billing");
  assert.equal(selected(billing, "/billing"), "billing-invoices");
  assert.equal(selected(billing, "/billing/invoices/123"), "billing-invoices");
  assert.equal(selected(billing, "/billing/receipts/123"), "billing-receipts");
  assert.equal(selected(billing, "/billing/payouts"), "billing-payouts");
});
test("query selectors and invalid/absent values agree with screen defaults", () => {
  for (const [module, path, key, value, fallback] of [
    ["reports", "/reports", "report", "arrears", "rent-roll"],
    ["messages", "/messages", "view", "notices", "operational"],
    ["admin-messages", "/admin/messages", "view", "notices", "operational"],
    ["transactions", "/admin/transactions", "view", "ledger", "collections"],
  ]) {
    const parent = item(module, path);
    assert.equal(selected(parent, path, `?${key}=${value}&page=2`), `${module}-${value}`);
    assert.equal(selected(parent, path, `?${key}=unknown`), `${module}-${fallback}`);
    assert.equal(selected(parent, path), `${module}-${fallback}`);
  }
});
test("Vendors selection preserves unrelated request filters", () => {
  const parent = item("maintenance", "/maintenance");
  assert.equal(selected(parent, "/maintenance", "?open=true&panel=vendors"), "maintenance-vendors");
  assert.equal(selected(parent, "/maintenance/123"), "maintenance-requests");
});
test("Outreach details select Contacts and independent routes select themselves", () => {
  const parent = item("outreach", "/admin/outreach");
  assert.equal(selected(parent, "/admin/outreach/contacts/123"), "outreach-contacts");
  for (const child of ["sequences", "review", "outbox"]) assert.equal(selected(parent, `/admin/outreach/${child}`), `outreach-${child}`);
});
test("path matching requires segment boundaries and prefers the deepest parent", () => {
  assert.equal(matchesPath("/billing-other", "/billing"), false);
  assert.equal(matchesPath("/admin/users-extra", "/admin/users"), false);
  assert.equal(selectedDestination([item("admin", "/admin"), item("transactions", "/admin/transactions")], "/admin/transactions", "?view=withdrawals").destination.value, "transactions-withdrawals");
  assert.equal(selectedDestination([item("billing", "/billing")], "/billing-other"), null);
});
