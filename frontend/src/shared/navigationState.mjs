// Destinations are data only so matching and capability gates can be checked
// without mounting the application or fetching any module's records.
export function moduleChildren(value, access) {
  if (access.persona === "tenant") return [];
  const messages = value === "admin-messages" ? "/admin/messages" : "/messages";
  const child = (key, label, to, extra = {}) => ({ value: `${value}-${key}`, label, to, ...extra });
  switch (value) {
    case "billing": return [
      child("invoices", "Invoices", "/billing", { default: true }),
      child("receipts", "Receipts", "/billing/receipts"),
      ...(access.can_manage_properties ? [
        child("proofs", "Payment proofs", "/billing/payment-proofs"),
        child("payouts", "Payouts", "/billing/payouts"),
      ] : []),
    ];
    case "maintenance": return [
      child("requests", "Requests", "/maintenance", { default: true }),
      ...(access.can_manage_properties ? [child("vendors", "Vendors", "/maintenance?panel=vendors")] : []),
    ];
    case "reports": return [
      child("rent-roll", "Rent roll", "/reports?report=rent-roll", { default: true }),
      child("arrears", "Arrears", "/reports?report=arrears"),
      child("collections", "Collections", "/reports?report=collections"),
      child("tenant-statement", "Tenant statement", "/reports?report=tenant-statement"),
    ];
    case "messages": case "admin-messages": return [
      child("operational", "Operational updates", `${messages}?view=operational`, { default: true }),
      child("notices", "Notices & reminders", `${messages}?view=notices`),
    ];
    case "transactions": return [
      child("collections", "Collections", "/admin/transactions?view=collections", { default: true }),
      child("withdrawals", "Withdrawals", "/admin/transactions?view=withdrawals"),
      child("payouts", "Automatic payouts", "/admin/transactions?view=payouts"),
      child("ledger", "Gateway ledger", "/admin/transactions?view=ledger"),
    ];
    case "outreach": return [
      child("contacts", "Contacts", "/admin/outreach", { default: true }),
      child("sequences", "Sequences", "/admin/outreach/sequences"),
      child("review", "Review queue", "/admin/outreach/review"),
      child("outbox", "Outbox", "/admin/outreach/outbox"),
    ];
    default: return [];
  }
}

export const matchesPath = (pathname, path) => pathname === path || pathname.startsWith(`${path}/`);

export function selectedDestination(items, pathname, search = "") {
  const parent = items.filter(item => matchesPath(pathname, item.to))
    .sort((a, b) => b.to.length - a.to.length)[0];
  if (!parent) return null;
  const params = new URLSearchParams(search);
  const children = parent.children || [];
  const match = children.filter(item => {
    const [path, query] = item.to.split("?");
    return matchesPath(pathname, path) && [...new URLSearchParams(query)].every(([k, v]) => params.get(k) === v);
  }).sort((a, b) => b.to.length - a.to.length)[0];
  // Default children also cover detail pages and absent/invalid selectors.
  const destination = match || children.find(item => item.default) || parent;
  return { parent, destination };
}
