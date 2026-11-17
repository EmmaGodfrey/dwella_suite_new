// Page guide content, keyed by module id (the same ids the server accepts).
// Steps explain what the page is for and where related things live. A step's
// `to` offers a link to another authorized page; guides never act for the user.
export const GUIDES = {
  landlord: {
    dashboard: { title: "Your dashboard", steps: [
      { title: "What needs attention", body: "Rent owed, overdue invoices and open repairs show here first. Select any figure to see the records behind it." },
      { title: "Handy, your assistant", body: "Ask Handy about tenants, invoices and payments in plain words. Handy answers from your own records.", },
    ] },
    setup: { title: "Get started", steps: [
      { title: "Four short steps", body: "Business details, how tenants pay, billing and reminders, then a review. Each step saves as you go, so you can leave and come back." },
      { title: "Payment details come first", body: "Tick the ways tenants can pay. Dwella asks for the account details for each one so invoices show them correctly." },
    ] },
    properties: { title: "Properties and units", steps: [
      { title: "Add a property", body: "Start with the building, then add its units and the asking rent for each." },
      { title: "Lots of units?", body: "Use Import units to bring a whole spreadsheet in at once. Download the template first so the columns match." },
      { title: "Next: tenants", body: "Once units exist you can add tenants and link them to a unit.", to: "/tenants", toLabel: "Go to Tenants" },
    ] },
    tenants: { title: "Tenants", steps: [
      { title: "Your tenant records", body: "Add a tenant with their contact details, then link them to a unit through a lease." },
      { title: "Invite them", body: "Send an invitation so a tenant can see their own invoices, pay online and report repairs. Nothing is sent until you press Send invitation." },
      { title: "Then a lease", body: "A lease ties the tenant, unit and rent together.", to: "/leases", toLabel: "Go to Leases" },
    ] },
    leases: { title: "Leases", steps: [
      { title: "Agreements in one place", body: "Open a lease to review its terms, the rent and the signed document." },
      { title: "Signing", body: "Send a lease for signing from its page. Tenants can sign on their phone. Dwella keeps the signed copy." },
    ] },
    billing: { title: "Billing", steps: [
      { title: "Invoices", body: "Generate rent invoices for the month or create one by hand. Tenants receive them by email and WhatsApp with a PDF copy." },
      { title: "Recording payments", body: "Record a payment when rent arrives by bank, cash or mobile money. Partial payments are fine and the balance updates." },
      { title: "Proof of payment", body: "When a tenant sends proof, you confirm it before it counts. Receipts go out automatically.", to: "/billing/payment-proofs", toLabel: "Open payment proofs" },
      { title: "Where your money lands", body: "Receiving details and payouts live under Payouts and Settings.", to: "/billing/payouts", toLabel: "Open Payouts" },
    ] },
    maintenance: { title: "Maintenance", steps: [
      { title: "Repair requests", body: "Tenants report issues here, with photos. Open a request to reply, assign it and update its status." },
      { title: "Keep tenants informed", body: "Each status change is visible to the tenant, so they always know where a repair stands." },
    ] },
    reports: { title: "Reports", steps: [
      { title: "Collections and statements", body: "See what was billed, collected and is still owed, by property or tenant." },
      { title: "Share or keep", body: "Reports reflect the records in Dwella, so keep payments recorded to keep them accurate." },
    ] },
    team: { title: "Team", steps: [
      { title: "Who works on what", body: "Invite managers and choose which properties each one can see. Managers only see their own properties." },
    ] },
    settings: { title: "Settings", steps: [
      { title: "Your business details", body: "Business name, contact details and receiving details are kept here." },
      { title: "How tenants pay", body: "Edit your bank and mobile-money details, and see which online payment methods are switched on." },
    ] },
    messages: { title: "Messages", steps: [
      { title: "Tenant conversations", body: "Messages from tenants, including WhatsApp, appear here so you can reply in one place." },
    ] },
  },
  tenant: {
    dashboard: { title: "Your home page", steps: [
      { title: "Your tenancy at a glance", body: "See what you owe, your next due date and any open repair requests." },
      { title: "Pay or report", body: "Pay an invoice online or report a repair from here.", to: "/billing", toLabel: "Go to Payments" },
    ] },
    billing: { title: "Payments", steps: [
      { title: "Invoices and balance", body: "Open an invoice to see exactly what it covers. Partial payments are fine." },
      { title: "Paying", body: "Pay online by mobile money, or pay your property manager directly and send proof of payment for them to confirm." },
      { title: "Receipts", body: "Every confirmed payment has a receipt you can open or download.", to: "/billing/receipts", toLabel: "Open receipts" },
    ] },
    leases: { title: "My lease", steps: [
      { title: "Your agreement", body: "Read your lease terms and, when it is ready, sign it on your phone." },
    ] },
    maintenance: { title: "Maintenance", steps: [
      { title: "Report a repair", body: "Describe the problem and add photos. You will see progress and replies here." },
    ] },
    profile: { title: "Your profile", steps: [
      { title: "Keep your details current", body: "Your contact details are how your property manager and Dwella reach you." },
    ] },
    security: { title: "Security", steps: [
      { title: "Protect your account", body: "Set up an authenticator app so only you can sign in." },
    ] },
  },
};

const ALIASES = { "/workspace/dashboard": "dashboard" };

// Module id for a path: the first path segment, so detail pages share their section's guide.
export function moduleForPath(pathname) {
  if (ALIASES[pathname]) return ALIASES[pathname];
  const first = pathname.split("/").filter(Boolean)[0];
  return first || "dashboard";
}
