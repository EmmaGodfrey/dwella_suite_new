import test from "node:test";
import assert from "node:assert/strict";
import { activityReportData, activityReportFilters, paymentMethods } from "./activityReports.mjs";
import { moduleChildren, selectedDestination } from "./navigationState.mjs";

test("CSV retains applied scope and drops paging, draft and unsupported filters", () => {
  const filters = { tenant: "tenant-1", property: "home-1", date_from: "2026-10-01", date_to: "2026-10-31", method: "deposit", page: 3, draft: "bad" };
  assert.deepEqual(activityReportFilters("collections", filters, true), { tenant: "tenant-1", property: "home-1", date_from: "2026-10-01", date_to: "2026-10-31", method: "deposit", export: "csv" });
  assert.deepEqual(activityReportFilters("tenant-statement", filters), { tenant: "tenant-1", property: "home-1", date_from: "2026-10-01", date_to: "2026-10-31", page: 3, page_size: 25 });
});
const collections = () => ({ results: { rows: [{ id: "p-1", invoice_id: "i-1", tenant_id: "t-1", amount: "123456789012345678.91", currency: "USD", method: "deposit", paid_on: "2026-10-01" }], currency: "USD", totals: {amount:"123456789012345678.91",payments:1}, by_method: Object.fromEntries(Object.keys(paymentMethods).map(key => [key, "0.00"])), date_from:"2026-10-01",date_to:"2026-10-31",as_of:"2026-11-05",page:1,total_pages:1,total_rows:1 }, pagination: {count:1} });
test("collections unwraps the actual paginated envelope and preserves cents", () => {
  const response = collections();
  assert.equal(activityReportData(response,"collections").totals.amount,"123456789012345678.91");
  assert.throws(() => activityReportData(response.results,"collections"), /incomplete/);
});
test("malformed collection totals, methods, scope and paging become errors", () => {
  for (const change of [data => delete data.by_method.cash, data => data.totals.amount = 0, data => data.rows[0].currency = "ZMW", data => data.rows[0].method = "pending", data => data.total_pages = 0]) {
    const response = collections(); change(response.results);
    assert.throws(() => activityReportData(response,"collections"), /incomplete/);
  }
});
test("manager report navigation selects both new reports precisely", () => {
  const item = { to:"/reports",value:"reports",children:moduleChildren("reports",{persona:"landlord"}) };
  for (const report of ["collections","tenant-statement"]) assert.equal(selectedDestination([item],"/reports",`?report=${report}`).destination.value, `reports-${report}`);
});
