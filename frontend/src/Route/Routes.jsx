//Pages
import Billing from "../Components/Billing";
import InvoiceDetail from "../Components/Billing/InvoiceDetail";
import Settings, { LegacySettings } from "../Components/Settings";
import Transactions from "../Components/Platform/Transactions";
import Messages from "../Components/Messages";
import Dashboard from "../Components/Dashboard";
import LeaseDetail from "../Components/Leases/LeaseDetail";
import Leases from "../Components/Leases";
import Maintenance from "../Components/Maintenance";
import RequestDetail from "../Components/Maintenance/RequestDetail";
import Tenants from "../Components/Tenants";
import Receipt from "../Components/Billing/Receipt";
import Receipts from "../Components/Billing/Receipts";
import Reports from "../Components/Reports";
import Setup from "../Components/Setup";
import Properties from "../Components/Properties";
import BetaSignups from "../Components/BetaSignups";
import Users from "../Components/Platform/Users";
import UserDetail from "../Components/Platform/UserDetail";
import IdentityChecks from "../Components/Platform/IdentityChecks";
import Workspaces from "../Components/Platform/Workspaces";
import WorkspaceDetail from "../Components/Platform/WorkspaceDetail";
import AuditLog from "../Components/Platform/AuditLog";
import Outreach from "../Components/Outreach";
import OutreachContact from "../Components/Outreach/ContactDetail";
import OutreachSequences from "../Components/Outreach/Sequences";
import OutreachReview from "../Components/Outreach/ReviewQueue";
import OutreachOutbox from "../Components/Outreach/Outbox";
import PortalLease from "../Components/Portal/MyLease";
import PortalMaintenance from "../Components/Portal/Maintenance";
import PortalPayments from "../Components/Portal/Payments";
import Payouts from "../Components/Billing/Payouts";
import PortalReceipt from "../Components/Portal/Receipt";
import PortalRepairDetail from "../Components/Portal/RepairDetail";
import ForTenant from "./ForTenant";

export const routes = [
  { path: "/messages", title: "Messages", Component: <Messages /> },
  { path: "/admin/messages", title: "Messages", Component: <Messages /> },
  { path: "/settings", title: "Settings", Component: <Settings /> },
  { path: "/billing/receiving-details", Component: <LegacySettings tab="billing" /> },
  { path: "/admin/settings", Component: <LegacySettings tab="assistant" /> },
  { path: "/admin/transactions", title: "Transactions", Component: <Transactions /> },
  { path: "/admin/outreach/contacts/:id", Component: <OutreachContact /> },
  { path: "/admin/outreach/sequences", Component: <OutreachSequences /> },
  { path: "/admin/outreach/review", Component: <OutreachReview /> },
  { path: "/admin/outreach/outbox", Component: <OutreachOutbox /> },
  { path: "/admin/outreach/settings", Component: <LegacySettings tab="outreach" /> },
  { path: "/admin/outreach", Component: <Outreach /> },
  { path: "/admin/audit-log", title: "Audit log", Component: <AuditLog /> },
  { path: "/workspace/dashboard", title: "Dashboard", Component: <Dashboard /> },
  { path: "/admin/workspaces", title: "Workspaces", Component: <Workspaces /> },
  { path: "/admin/workspaces/:id", title: "Workspace detail", Component: <WorkspaceDetail /> },
  { path: "/admin/identity-checks", title: "Identity checks", Component: <IdentityChecks /> },
  { path: "/admin/users", title: "Users", Component: <Users /> },
  { path: "/admin/users/:id", title: "User detail", Component: <UserDetail /> },
  { path: "/setup", title: "Get started", Component: <Setup /> },
  { path: "/billing/payouts", title: "Payouts", Component: <ForTenant tenant={<PortalPayments />}><Payouts /></ForTenant> },
  { path: "/billing/receipts", title: "Receipts", Component: <ForTenant tenant={<PortalPayments />}><Receipts /></ForTenant> },
  { path: "/billing/receipts/:id", title: "Receipt", Component: <ForTenant tenant={<PortalReceipt />}><Receipt /></ForTenant> },
  {
    path: `/dashboard`,
    title: "Dashboard",
    description: "Portfolio health, occupancy, rent roll, and current work.",
    Component: <Dashboard />,
  },
  {
    path: `/properties`,
    title: "Properties",
    description: "Search, filter, and grow the property portfolio.",
    Component: <Properties />,
  },
  {
    path: `/tenants`,
    title: "Tenants",
    description: "Tenant CRM, occupancy records, and communication history.",
    Component: <Tenants />,
  },
  {
    path: `/leases`,
    title: "Leases",
    description: "Lease terms, renewals, deposits, and documents.",
    Component: <ForTenant tenant={<PortalLease />}><Leases /></ForTenant>,
  },
  {
    path: `/leases/:id`,
    title: "Lease",
    description: "Lease terms and history.",
    Component: <ForTenant tenant={<PortalLease />}><LeaseDetail /></ForTenant>,
  },
  {
    path: `/billing`,
    title: "Billing",
    description: "Rent invoices, collections, balances, and payment tracking.",
    Component: <ForTenant tenant={<PortalPayments />}><Billing /></ForTenant>,
  },
  {
    path: `/billing/invoices/:id`,
    title: "Invoice",
    description: "Invoice lines, payments, and balance.",
    Component: <ForTenant tenant={<PortalPayments />}><InvoiceDetail /></ForTenant>,
  },
  {
    path: `/maintenance`,
    title: "Maintenance",
    description: "Work orders, vendors, approvals, and service tracking.",
    Component: <ForTenant tenant={<PortalMaintenance />}><Maintenance /></ForTenant>,
  },
  {
    path: `/maintenance/:id`,
    title: "Maintenance request",
    description: "Progress, conversation and scheduling for one repair.",
    Component: <ForTenant tenant={<PortalRepairDetail />}><RequestDetail /></ForTenant>,
  },
  {
    path: `/reports`,
    title: "Reports",
    description: "Portfolio, arrears, occupancy, and owner reporting.",
    Component: <Reports />,
  },
  {
    path: `/beta-signups`,
    title: "Beta signups",
    description: "Review applicants and coordinate beta onboarding.",
    Component: <BetaSignups />,
  },
  {
    path: `/profile`,
    title: "Profile",
    description: "Account details, identity verification, and profile photo.",
    Component: <LegacySettings tab="account" />,
  },
  {
    path: `/security`,
    title: "Security",
    description: "Two-factor authentication and account protection.",
    Component: <LegacySettings tab="security" />,
  },
];
