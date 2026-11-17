// Page guide content, keyed by module id (the same ids the server accepts).
// A step may point at a real control with `target`: { sel, text } highlights the first
// visible match, { handy: true } the Handy assistant button. With no match the card
// sits beside the lightbulb. `to` links to another authorized page. Guides only
// explain; they never save, send, pay or sign anything for the person.
const M = "main ";
const btn = (text) => ({ sel: `${M}button`, text });
const tab = (text) => ({ sel: `${M}[role=tab]`, text });
const HANDY = { handy: true };

export const GUIDES = {
  landlord: {
    dashboard: { title: "Dashboard", steps: [
      { title: "Your month at a glance", body: "Rent billed, collected and still owed, plus occupancy. This is the quickest read on how the portfolio is doing.", target: { sel: `${M}h1` } },
      { title: "What needs attention", body: "Leases about to end and empty units appear here. Select one to open it and act.", target: btn("Lease ends") },
      { title: "Ask Handy", body: "Handy is your built-in assistant. Ask who has not paid, what is due, or to record a payment, and it answers from your own records.", target: HANDY },
      { title: "Go straight to billing", body: "Jump to invoices and payments from the recent payments panel.", target: btn("Go to billing") },
      { title: "Notifications", body: "Payments, proof of payment and repair requests show up here as they happen.", target: { sel: "header button[aria-label^='Notifications']" } },
      { title: "Your setup checklist", body: "Get started stays in the menu until your account, payment details and billing are ready.", target: { sel: "nav a, aside a", text: "Get started" } },
    ] },
    setup: { title: "Get started", steps: [
      { title: "Four short steps", body: "Business details, how tenants pay, billing and reminders, then a review. Each step saves as you go, so you can leave and return.", target: { sel: `${M}h1` } },
      { title: "How tenants pay", body: "Tick the ways tenants can pay. Dwella asks for the account details for each one so invoices show them correctly." },
      { title: "Review and edit", body: "The last step lists everything you entered. Edit any section from there before you finish." },
      { title: "Finish", body: "Finishing opens your workspace. You can change all of this later in Settings.", target: btn("Finish account setup") },
      { title: "Handy is waiting", body: "Once you are set up, ask Handy about your tenants, invoices and payments.", target: HANDY },
    ] },
    properties: { title: "Properties", steps: [
      { title: "Add a property", body: "Start with the building. You then add its units and the asking rent for each.", target: btn("Add property") },
      { title: "Add units", body: "Open a property, then Add unit for each flat or room. Unit status shows whether it is occupied, vacant or in maintenance.", target: btn("Add unit") },
      { title: "Many units at once", body: "Import them from a spreadsheet. Download the template first so the columns match.", target: btn("Import units") },
      { title: "Search and filter", body: "Find a property by name or town, or filter by type and management status.", target: { sel: `${M}input[placeholder*='Search']` } },
      { title: "Edit and photos", body: "Edit changes a property's details. Add a cover photo to recognise it quickly.", target: btn("Edit") },
      { title: "Ask Handy", body: "Handy can tell you which units are vacant and what they would earn.", target: HANDY },
      { title: "Next: tenants", body: "Once units exist, add the people who live in them.", to: "/tenants", toLabel: "Go to Tenants" },
    ] },
    tenants: { title: "Tenants", steps: [
      { title: "Add a tenant", body: "Enter their contact details. You can link them to a unit through a lease straight after.", target: btn("Add tenant") },
      { title: "Import many", body: "Bring tenants, or tenants with their leases, in from a spreadsheet.", target: btn("Import tenants") },
      { title: "Find the right tenant", body: "Filter by active, applicants, past or archived, and search by name.", target: btn("Applicants") },
      { title: "Open a tenant", body: "Their page has contact buttons (call, SMS, email), their lease and their balance.", target: { sel: `${M}h2` } },
      { title: "Invite them online", body: "Send an invitation so a tenant can see their invoices, pay and report repairs. Nothing is sent until you press it.", target: btn("Send invitation") },
      { title: "Keep details complete", body: "Tenant ID and address details are needed for tax-ready invoices. Edit tenant lets you complete them.", target: btn("Edit tenant") },
      { title: "Next: a lease", body: "A lease ties a tenant, a unit and the rent together.", to: "/leases", toLabel: "Go to Leases" },
    ] },
    leases: { title: "Leases", steps: [
      { title: "Create a lease", body: "Pick the tenant, the unit, the rent and the dates. Dwella builds the agreement from this.", target: btn("New lease") },
      { title: "Where each lease stands", body: "Draft, awaiting signature, active or ended. Use these to see what needs your attention.", target: btn("Awaiting signature") },
      { title: "Open a lease", body: "Inside a lease you can preview the document, send it for signing and keep the signed copy.", target: { sel: `${M}tbody tr` } },
      { title: "Renewals and deposits", body: "Leases ending soon are flagged under the term so you can renew in time.", target: { sel: `${M}tbody tr` } },
      { title: "Search", body: "Search by tenant, unit or lease number.", target: { sel: `${M}input[placeholder*='Search']` } },
    ] },
    billing: { title: "Invoices", steps: [
      { title: "Monthly rent", body: "Generate the month's rent invoices in one go. Tenants receive them by email and WhatsApp with a PDF copy.", target: btn("Generate rent invoices") },
      { title: "One-off charges", body: "Add a single charge such as a deposit, a repair or a fee.", target: btn("New charge") },
      { title: "Opening balances", body: "Moving from paper or another system? Enter what tenants already owe here.", target: btn("Opening balances") },
      { title: "Find what is owed", body: "Filter to unpaid, overdue, paid or void invoices, or search by tenant.", target: btn("Overdue") },
      { title: "Record a payment", body: "Open an invoice to record a payment by bank, cash or mobile money. Partial payments are fine and the balance updates. A receipt is sent automatically.", target: { sel: `${M}tbody tr` } },
      { title: "Proof of payment", body: "Tenants can send proof for you to confirm before it counts.", to: "/billing/payment-proofs", toLabel: "Open payment proofs" },
      { title: "Ask Handy", body: "Ask Handy who is overdue, or have it record a payment for you.", target: HANDY },
    ] },
    payouts: { title: "Payouts", steps: [
      { title: "Receiving account", body: "The bank or mobile-money account your collected rent is paid out to.", target: btn("Add receiving account") },
      { title: "Withdraw", body: "Move collected money to your account. You see the fee and the amount before you confirm.", target: btn("Withdraw") },
      { title: "Payout timing", body: "Choose how often money is paid out.", target: btn("Change timing") },
      { title: "History", body: "Every withdrawal and its status is listed below.", target: { sel: `${M}h2`, text: "Withdrawal history" } },
    ] },
    "payment-proofs": { title: "Payment proofs", steps: [
      { title: "Waiting for you", body: "Proof tenants have sent appears here. Check the amount and date against your records, then confirm it.", target: btn("Waiting for you") },
      { title: "Ask for details", body: "If something is unclear, ask the tenant for more details instead of confirming.", target: btn("Asked for details") },
      { title: "Confirmed and not received", body: "Confirming records the payment and sends a receipt. Mark it not received if the money did not arrive.", target: btn("Confirmed") },
    ] },
    receipts: { title: "Receipts", steps: [
      { title: "Every payment, one receipt", body: "Receipts are created when a payment is recorded. Open one to view, print or download the PDF." },
    ] },
    maintenance: { title: "Maintenance", steps: [
      { title: "Log a request", body: "Tenants report repairs here with photos. You can also add one yourself.", target: btn("New request") },
      { title: "Board or list", body: "Board shows requests by stage: new, scheduled, in progress and done. List is better for scanning.", target: btn("Board") },
      { title: "Filter the work", body: "Narrow by property, status, priority or vendor.", target: { sel: `${M}[role=combobox]` } },
      { title: "Open a request", body: "Reply to the tenant, assign a vendor, set a priority and update the status. Every change is visible to the tenant.", target: { sel: `${M}h2`, text: "New" } },
      { title: "Search", body: "Find a request by keyword.", target: { sel: `${M}input[placeholder*='Search']` } },
    ] },
    reports: { title: "Reports", steps: [
      { title: "Choose a report", body: "Rent roll, arrears, collections or a single tenant statement.", target: btn("Arrears") },
      { title: "Rent roll", body: "Every unit with its tenant, rent and balance.", target: btn("Rent roll") },
      { title: "Tenant statement", body: "A full statement of charges and payments for one tenant, ready to share.", target: btn("Tenant statement") },
      { title: "Export", body: "Download what you see as a CSV for your accountant.", target: btn("Export CSV") },
    ] },
    team: { title: "Team", steps: [
      { title: "Invite a manager", body: "Choose which properties each teammate can see. Managers only see their own properties.", target: btn("Invite team member") },
      { title: "People", body: "See everyone with access and change what they can reach.", target: tab("People") },
      { title: "Activity", body: "A record of who did what in your workspace.", target: tab("Activity") },
      { title: "Cover for each other", body: "Let managers cover each other's properties when someone is away.", target: { sel: `${M}input[type=checkbox], ${M}input[role=switch]` } },
    ] },
    settings: { title: "Settings", steps: [
      { title: "Account", body: "Your name, photo, phone and identity verification.", target: tab("Account") },
      { title: "Workspace", body: "Business name, address, currency and the setup checklist.", target: tab("Workspace") },
      { title: "Payments", body: "Your bank and mobile-money details, and which online payment methods are on.", target: tab("Payments") },
      { title: "Notifications", body: "Choose what reaches you, and by which channel.", target: tab("Notifications") },
      { title: "Security", body: "Password and authenticator app. Turn these on to protect your records.", target: tab("Security") },
    ] },
    messages: { title: "Messages", steps: [
      { title: "Send a message", body: "Write to a tenant. Their replies, including WhatsApp, appear here.", target: btn("New message") },
      { title: "Reminder settings", body: "Choose how and when tenants are reminded about rent.", target: { sel: "main a, main button", text: "Reminder settings" } },
      { title: "Stay current", body: "Refresh to check for new messages.", target: btn("Refresh") },
    ] },
  },
  tenant: {
    dashboard: { title: "Home", steps: [
      { title: "Your tenancy at a glance", body: "What you owe, what is due next and any open repairs.", target: { sel: `${M}h1` } },
      { title: "Pay online", body: "Pay an invoice by mobile money. Your balance and receipt update once the payment is confirmed.", target: btn("Pay online") },
      { title: "Report a repair", body: "Tell your property manager about a problem and follow it to completion.", target: btn("Report a repair") },
      { title: "Ask Handy", body: "Handy can answer questions about your invoices and payments.", target: HANDY },
    ] },
    billing: { title: "Payments", steps: [
      { title: "Invoices and balance", body: "Open an invoice to see exactly what it covers. Partial payments are fine.", target: btn("View invoice") },
      { title: "Pay online", body: "Pay by mobile money without leaving Dwella. Never share your PIN here.", target: btn("Pay online") },
      { title: "Paid another way?", body: "If you paid your property manager directly, send proof so they can confirm it.", target: btn("I've already paid") },
      { title: "Your statement", body: "Every charge and payment in one place.", target: btn("Statement") },
      { title: "Receipts", body: "Each confirmed payment has a receipt.", to: "/billing/receipts", toLabel: "Open receipts" },
    ] },
    leases: { title: "My lease", steps: [
      { title: "Your agreement", body: "Read your lease terms, rent and dates.", target: btn("View agreement") },
      { title: "Signing", body: "When your lease is ready you can sign it on your phone. Dwella keeps the signed copy." },
    ] },
    maintenance: { title: "Maintenance", steps: [
      { title: "Report a repair", body: "Describe the problem and add photos.", target: btn("Report a repair") },
      { title: "Follow progress", body: "Open a request to see updates and message your property manager." },
    ] },
    profile: { title: "Profile", steps: [{ title: "Keep details current", body: "This is how your property manager and Dwella reach you." }] },
    security: { title: "Security", steps: [{ title: "Protect your account", body: "Set up an authenticator app so only you can sign in." }] },
  },
};

const ALIASES = { "/workspace/dashboard": "dashboard", "/billing/payouts": "payouts", "/billing/payment-proofs": "payment-proofs", "/billing/receipts": "receipts" };

// Module id for a path: the first path segment, so detail pages share their section's guide.
export function moduleForPath(pathname) {
  if (ALIASES[pathname]) return ALIASES[pathname];
  const first = pathname.split("/").filter(Boolean)[0];
  return first || "dashboard";
}
