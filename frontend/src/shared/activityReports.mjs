import { portalStatementData } from "./statement.mjs";

export const reportOptions = [
  { value: "rent-roll", label: "Rent roll" }, { value: "arrears", label: "Arrears" },
  { value: "collections", label: "Collections" }, { value: "tenant-statement", label: "Tenant statement" },
];
export const paymentMethods = { cash: "Cash", mobile_money: "Mobile money", bank_transfer: "Bank transfer", card: "Card", cheque: "Cheque", deposit: "From security deposit" };
const decimal = /^-?\d+\.\d{2}$/;

export function activityReportFilters(report, filters, csv = false) {
  const keys = ["tenant", "property", "date_from", "date_to", ...(report === "collections" ? ["method"] : [])];
  return Object.fromEntries([
    ...keys.filter(key => filters[key]).map(key => [key, filters[key]]),
    ...(csv ? [["export", "csv"]] : [["page", filters.page || 1], ["page_size", 25]]),
  ]);
}

export function activityReportData(response, report, tenant) {
  if (report === "tenant-statement") return portalStatementData(response, tenant);
  const data = response?.results;
  if (!data || !Array.isArray(data.rows) || !/^[A-Z]{3}$/.test(data.currency || "")
      || !decimal.test(data.totals?.amount) || !Number.isInteger(data.totals?.payments)
      || data.totals.payments < 0 || !Object.keys(paymentMethods).every(key => decimal.test(data.by_method?.[key]))
      || ![data.date_from, data.date_to, data.as_of].every(value => /^\d{4}-\d{2}-\d{2}$/.test(value || ""))
      || !Number.isInteger(data.page) || data.page < 1 || !Number.isInteger(data.total_pages) || data.total_pages < data.page
      || !Number.isInteger(data.total_rows) || data.total_rows < 0
      || !data.rows.every(row => row.id && row.invoice_id && row.tenant_id && decimal.test(row.amount)
        && row.currency === data.currency && paymentMethods[row.method] && /^\d{4}-\d{2}-\d{2}$/.test(row.paid_on))) {
    throw new Error("The collections response is incomplete. Please try again.");
  }
  return data;
}
