import assert from "node:assert/strict";
import test from "node:test";
import { portalStatementData, statementDateErrors, statementMoney, workspaceToday } from "./statement.mjs";

test("statement dates enforce inclusive 366-day limit, real dates and today", () => {
  assert.deepEqual(statementDateErrors({ date_from: "2024-01-01", date_to: "2024-12-31" }, "2024-12-31"), {});
  assert.ok(statementDateErrors({ date_from: "2024-01-01", date_to: "2025-01-01" }, "2025-01-01").date_from);
  assert.ok(statementDateErrors({ date_from: "2025-02-29", date_to: "2025-03-01" }, "2025-03-01").date_from);
  assert.ok(statementDateErrors({ date_from: "2026-11-05", date_to: "2026-11-04" }, "2026-11-05").date_to);
  assert.ok(statementDateErrors({ date_from: "2026-11-05", date_to: "2026-11-06" }, "2026-11-05").date_to);
  assert.ok(statementDateErrors({ date_from: "", date_to: "" }, "2026-11-05").date_from);
});

test("workspace day follows its timezone across UTC midnight", () => {
  const now = new Date("2026-11-04T23:30:00Z");
  assert.equal(workspaceToday("Africa/Lusaka", now), "2026-11-05");
  assert.equal(workspaceToday("America/Los_Angeles", now), "2026-11-04");
});

test("statement currency formatting preserves cents, large amounts and negative credits", () => {
  assert.match(statementMoney("123456789012345678.91", "USD"), /123,456,789,012,345,678\.91/);
  assert.match(statementMoney("-0.01", "USD"), /-.*0\.01/);
  assert.match(statementMoney("12.34", "USD"), /USD.*12\.34/);
  assert.equal(statementMoney("12.34", "USD", false), "12.34");
  assert.equal(statementMoney(null, "USD"), "—");
});

const data = {
  tenant: { id: "own-account" }, rows: [], currency: "USD", page: 1, total_rows: 0, total_pages: 1,
  date_from: "2026-11-01", date_to: "2026-11-05", as_of: "2026-11-05", page_opening_balance: "-0.01",
  totals: { opening_balance: "-0.01", charges: "0.00", payments: "0.00", closing_balance: "-0.01" },
};
test("the paginated envelope retains a valid empty statement and credit balance", () => {
  assert.equal(portalStatementData({ results: data, pagination: { count: 0 } }, "own-account"), data);
});
test("malformed or wrong-account responses fail instead of showing fabricated empty balances", () => {
  for (const response of [{}, { results: [] }, { results: { ...data, totals: {} } },
    { results: { ...data, tenant: { id: "another-account" } } },
    { results: { ...data, rows: [{ id: "bad", type: "payment", balance: "NaN" }] } }]) {
    assert.throws(() => portalStatementData(response, "own-account"), /incomplete/);
  }
});
