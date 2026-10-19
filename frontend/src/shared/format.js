const money = new Intl.NumberFormat("en-ZM", { style: "currency", currency: "ZMW", minimumFractionDigits: 2 });
const wholeMoney = new Intl.NumberFormat("en-ZM", { style: "currency", currency: "ZMW", maximumFractionDigits: 0 });
const shortDate = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", year: "numeric" });

export const formatMoney = (value, { whole = false } = {}) =>
  (whole ? wholeMoney : money).format(Number(value || 0));

// API dates are `YYYY-MM-DD`; parsing them as UTC midnight would show the
// previous day west of Greenwich, so they are read as local dates.
export const parseDate = (value) => {
  if (!value) return null;
  const [year, month, day] = String(value).slice(0, 10).split("-").map(Number);
  return new Date(year, month - 1, day);
};

export const formatDate = (value) => {
  const date = value instanceof Date ? value : parseDate(value);
  return date && !Number.isNaN(date.getTime()) ? shortDate.format(date) : "—";
};

export const toIsoDate = (date) =>
  [date.getFullYear(), String(date.getMonth() + 1).padStart(2, "0"), String(date.getDate()).padStart(2, "0")].join("-");

export const initials = (name = "") =>
  name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join("") || "?";

export const daysUntil = (value) => {
  const date = parseDate(value);
  if (!date) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((date - today) / 86_400_000);
};
