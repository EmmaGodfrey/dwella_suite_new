const decimal = /^-?\d+\.\d{2}$/;

const dateValue = (value) => {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value || "")) return NaN;
  const time = Date.parse(`${value}T00:00:00Z`);
  return Number.isFinite(time) && new Date(time).toISOString().slice(0, 10) === value ? time : NaN;
};

export function statementDateErrors(period, today) {
  const start = dateValue(period.date_from), end = dateValue(period.date_to);
  const errors = {};
  if (!Number.isFinite(start)) errors.date_from = "Enter a valid start date.";
  if (!Number.isFinite(end)) errors.date_to = "Enter a valid end date.";
  if (Number.isFinite(end) && period.date_to > today) errors.date_to = "Choose today or an earlier date.";
  if (Number.isFinite(start) && Number.isFinite(end)) {
    if (end < start) errors.date_to = "Choose an end date on or after the start date.";
    else if (end - start > 365 * 86_400_000) errors.date_from = "Choose at most 366 days.";
  }
  return errors;
}

export function workspaceToday(timeZone, now = new Date()) {
  const parts = new Intl.DateTimeFormat("en-GB", { timeZone, year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(now);
  const part = (type) => parts.find((item) => item.type === type).value;
  return `${part("year")}-${part("month")}-${part("day")}`;
}

// Keep the cents as a string; converting a large ledger amount to Number can round it.
export function statementMoney(value, currency, withCurrency = true) {
  if (!decimal.test(value)) return "—";
  const negative = value.startsWith("-");
  const [integer, cents] = value.replace(/^-/, "").split(".");
  const whole = BigInt(integer);
  const signed = negative ? (whole === 0n ? -0 : -whole) : whole;
  return new Intl.NumberFormat("en-ZM", {
    ...(withCurrency ? { style: "currency", currency, currencyDisplay: "code" } : {}),
    minimumFractionDigits: 2, maximumFractionDigits: 2,
  }).formatToParts(signed).map((part) => part.type === "fraction" ? cents : part.value).join("");
}

export function portalStatementData(response, accountId) {
  const data = response?.results;
  const totals = ["opening_balance", "charges", "payments", "closing_balance"];
  if (!data || !Array.isArray(data.rows) || data.tenant?.id !== accountId
      || !/^[A-Z]{3}$/.test(data.currency || "")
      || !totals.every((key) => decimal.test(data.totals?.[key]))
      || !decimal.test(data.page_opening_balance)
      || !Number.isFinite(dateValue(data.date_from)) || !Number.isFinite(dateValue(data.date_to))
      || !Number.isFinite(dateValue(data.as_of))
      || !Number.isInteger(data.page) || data.page < 1
      || !Number.isInteger(data.total_pages) || data.total_pages < data.page
      || !Number.isInteger(data.total_rows) || data.total_rows < 0
      || !data.rows.every((row) => ["charge", "payment"].includes(row.type)
        && ["debit", "credit", "balance"].every((key) => decimal.test(row[key]))
        && Number.isFinite(dateValue(row.date)) && row.id && row.invoice_id)) {
    throw new Error("The statement response is incomplete. Please try again.");
  }
  return data;
}
