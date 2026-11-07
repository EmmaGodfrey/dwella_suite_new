import test from "node:test";
import assert from "node:assert/strict";
import { portfolioReportData } from "./portfolioReport.mjs";

test("paginated report payload retains rows, totals and page metadata", () => {
  for (const rows of [[], [{ property: "Sample property", monthly_rent: "1000.00" }]]) {
    const data = { rows, totals: { monthly_rent: "1000.00" }, as_of: "2026-11-01", page: 2, total_rows: 26, total_pages: 2 };
    const result = portfolioReportData({ results: data, pagination: { count: 26, page: 2, total_pages: 2 } });
    assert.equal(result, data);
    assert.equal(result.rows, rows);
    assert.equal(result.total_rows, 26);
    assert.equal(result.total_pages, 2);
    assert.equal(result.totals.monthly_rent, "1000.00");
  }
});

test("invalid report responses become query errors instead of false empty reports", () => {
  for (const response of [undefined, {}, { results: [] }, { results: {} }, { results: { rows: null } }]) {
    assert.throws(() => portfolioReportData(response), /missing its rows/);
  }
});
