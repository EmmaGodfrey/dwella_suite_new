// Billing vocabulary shared by the Billing page, invoice detail and the
// record-payment drawer.

// Each tab maps to API filters; "overdue" is derived on the server from the
// due date rather than stored, so it is a filter, not a status.
export const invoiceViews = [
  { value: "all", label: "All", filters: {} },
  { value: "unpaid", label: "Unpaid", filters: { unpaid: "true" } },
  { value: "overdue", label: "Overdue", filters: { overdue: "true" } },
  { value: "paid", label: "Paid", filters: { status: "paid" } },
  { value: "void", label: "Void", filters: { status: "void" } },
];

const invoiceBadge = {
  open: ["warning", "Unpaid"],
  partially_paid: ["warning", "Part paid"],
  paid: ["success", "Paid"],
  void: ["subtle", "Void"],
};

export const invoiceBadgeProps = (invoice) => {
  if (invoice.days_overdue > 0) {
    return { color: "danger", children: `Overdue · ${invoice.days_overdue} ${invoice.days_overdue === 1 ? "day" : "days"}` };
  }
  const [color, label] = invoiceBadge[invoice.status] || ["subtle", invoice.status];
  return { color, children: label };
};

export const paymentMethods = [
  { value: "mobile_money", label: "Mobile money" },
  { value: "bank_transfer", label: "Bank transfer" },
  { value: "cash", label: "Cash" },
  { value: "card", label: "Card" },
  { value: "cheque", label: "Cheque" },
];

export const paymentMethodLabel = (value) => paymentMethods.find((method) => method.value === value)?.label || value;

export const lineKinds = [
  { value: "rent", label: "Rent" },
  { value: "utility", label: "Utility" },
  { value: "deposit", label: "Deposit" },
  { value: "late_fee", label: "Late fee" },
  { value: "other", label: "Other" },
];

export const periodLabel = (isoDate) => {
  if (!isoDate) return "One-off charge";
  const [year, month] = isoDate.split("-").map(Number);
  return new Date(year, month - 1, 1).toLocaleDateString("en-GB", { month: "long", year: "numeric" });
};
