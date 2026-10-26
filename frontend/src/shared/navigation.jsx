import React from "react";
import {
  Building24Regular,
  CheckmarkCircle24Regular,
  DataTrending24Regular,
  DocumentText24Regular,
  FormMultiple24Regular,
  Home24Regular,
  Payment24Regular,
  People24Regular,
  Mail24Regular,
  Wrench24Regular,
  Settings24Regular,
} from "@fluentui/react-icons";

import { getUserAccess } from "./access";

// Sidebar sections, in display order. An item's `group` places it under one of
// these; a group with no visible items for the persona is not rendered.
export const navigationGroups = [
  { value: "platform", label: "Platform" },
  { value: "overview", label: "Overview" },
  { value: "portfolio", label: "Portfolio" },
  { value: "operations", label: "Operations" },
  { value: "tenancy", label: "Your tenancy" },
];

const operationalItems = [
  { to: "/messages", value: "messages", group: "operations", label: "Messages", icon: <Mail24Regular />, personas: ["landlord"] },
  { to: "/admin/messages", value: "admin-messages", group: "platform", label: "Messages", icon: <Mail24Regular />, personas: ["platform_admin"] },
  { to: "/settings", value: "settings", group: "utility", label: "Settings", icon: <Settings24Regular />, personas: ["platform_admin", "landlord", "tenant", "unassigned"] },
  { to: "/admin/transactions", value: "transactions", group: "platform", label: "Transactions", icon: <Payment24Regular />, personas: ["platform_admin"] },
  { to: "/dashboard", value: "administration", group: "platform", label: "Administration", icon: <Home24Regular />, personas: ["platform_admin"] },
  { to: "/workspace/dashboard", value: "workspace-dashboard", group: "overview", label: "Dashboard", icon: <Home24Regular />, personas: ["platform_admin"] },
  { to: "/setup", value: "workspace-setup", group: "overview", label: "Get started", icon: <CheckmarkCircle24Regular />, personas: ["platform_admin"] },
  { to: "/admin/workspaces", value: "workspaces", group: "platform", label: "Workspaces", icon: <Building24Regular />, personas: ["platform_admin"] },
  { to: "/admin/identity-checks", value: "identity-checks", group: "platform", label: "Identity checks", icon: <CheckmarkCircle24Regular />, personas: ["platform_admin"] },
  { to: "/admin/users", value: "admin-users", group: "platform", label: "Users", icon: <People24Regular />, personas: ["platform_admin"] },
  { to: "/setup", value: "setup", group: "overview", label: "Get started", icon: <CheckmarkCircle24Regular />, personas: ["landlord", "unassigned"] },
  { to: "/dashboard", value: "dashboard", group: "overview", label: "Dashboard", tenantLabel: "Home", icon: <Home24Regular />, personas: ["landlord", "tenant"] },
  { to: "/reports", value: "reports", group: "overview", label: "Reports", icon: <DataTrending24Regular />, personas: ["platform_admin", "landlord"] },
  { to: "/properties", value: "properties", group: "portfolio", label: "Properties", icon: <Building24Regular />, personas: ["platform_admin", "landlord"] },
  { to: "/tenants", value: "tenants", group: "portfolio", label: "Tenants", icon: <People24Regular />, personas: ["platform_admin", "landlord"] },
  { to: "/leases", value: "leases", group: "portfolio", label: "Leases", tenantLabel: "My lease", icon: <DocumentText24Regular />, personas: ["platform_admin", "landlord", "tenant"] },
  { to: "/billing", value: "billing", group: "operations", label: "Billing", tenantLabel: "Payments", icon: <Payment24Regular />, personas: ["platform_admin", "landlord", "tenant"] },
  { to: "/maintenance", value: "maintenance", group: "operations", label: "Maintenance", icon: <Wrench24Regular />, personas: ["platform_admin", "landlord", "tenant"] },
  { to: "/beta-signups", value: "beta-signups", group: "platform", label: "Beta signups", icon: <FormMultiple24Regular />, personas: ["platform_admin"] },
  { to: "/admin/audit-log", value: "audit-log", group: "platform", label: "Audit log", icon: <DocumentText24Regular />, personas: ["platform_admin"] },
  { to: "/admin/outreach", value: "outreach", group: "platform", label: "Outreach", icon: <Mail24Regular />, personas: ["platform_admin"] },
];

export function getNavigationItems(user) {
  const access = getUserAccess(user);
  return operationalItems
    .filter((item) => item.personas.includes(access.persona))
    .filter((item) => access.persona !== "platform_admin" || ["platform", "utility"].includes(item.group) || Boolean(access.acting_workspace))
    .map((item) => ({
      ...item,
      label: access.persona === "tenant" && item.tenantLabel ? item.tenantLabel : item.label,
      // A tenant sees one short list about their own home.
      group: access.persona === "tenant" ? "tenancy" : item.group,
    }));
}

export const pageMeta = {
  "/messages": ["Messages", "Send tenant notices and track requests."],
  "/admin/messages": ["Messages", "Platform message requests and delivery status."],
  "/settings": ["Settings", "Account, workspace and preferences."],
  "/admin/transactions": ["Transactions", "Tenant collections, landlord payouts and gateway responses."],
  "/admin/settings": ["Platform settings", "Manage platform-wide features."],
  "/admin/outreach": ["Outreach", "Personal partnerships and early tester invitations."],
  "/admin/audit-log": ["Audit log", "Account and workspace actions with support context."],
  "/workspace/dashboard": ["Dashboard", "Workspace overview."],
  "/admin/workspaces": ["Workspaces", "Manage property manager workspaces and audited support access."],
  "/admin/identity-checks": ["Identity checks", "Review submitted identity documents."],
  "/admin/users": ["Users", "Manage accounts, workspace access and identity checks."],
  "/setup": ["Get started", "Set up your workspace, add a tenant and start tracking rent."],
  "/dashboard": ["Dashboard", "Portfolio health, occupancy, rent roll, and current work."],
  "/properties": ["Properties", "Search, filter, and grow the property portfolio."],
  "/tenants": ["Tenants", "Tenant CRM, occupancy records, and communication history."],
  "/leases": ["Leases", "Lease terms, renewals, deposits, and documents."],
  "/billing": ["Billing", "Rent invoices, collections, balances, and payment tracking."],
  "/maintenance": ["Maintenance", "Work orders, vendors, approvals, and service tracking."],
  "/reports": ["Reports", "Rent roll, outstanding balances and overdue invoices."],
  "/beta-signups": ["Beta signups", "Review applicants and coordinate beta onboarding."],
  "/profile": ["Profile", "Account details, identity verification, and profile photo."],
  "/security": ["Security", "Two-factor authentication and account protection."],
};

export function getPageMeta(pathname, user) {
  const access = getUserAccess(user);
  if (access.persona === "tenant") {
    if (pathname === "/dashboard") return ["Home", "Your tenancy, payments, and maintenance requests."];
    if (pathname.startsWith("/leases")) return ["My lease", "Lease terms and your signed agreement."];
    if (pathname.startsWith("/billing")) return ["Payments", "Invoices, receipts, and what you owe."];
    if (pathname === "/maintenance") return ["Maintenance", "Report a repair and follow it to completion."];
    if (pathname.startsWith("/maintenance/")) return ["Repair", "Progress and messages with your property manager."];
  }
  if (access.persona === "platform_admin" && pathname === "/dashboard") {
    return ["Administration", "Property manager activity and platform portfolio oversight."];
  }
  // Detail pages (`/leases/<id>`) take their section's title.
  const section = Object.keys(pageMeta).find((path) => pathname.startsWith(`${path}/`));
  return pageMeta[pathname] || pageMeta[section] || ["Dwella Suite", "Property operations workspace."];
}

export function canAccessPath(pathname, user) {
  if (pathname === "/admin/settings") return getUserAccess(user).persona === "platform_admin";
  if (["/profile", "/security", "/dashboard", "/"].includes(pathname)) return true;
  return getNavigationItems(user).some((item) => pathname.startsWith(item.to));
}

export function getSelectedNavValue(pathname, user) {
  return getNavigationItems(user).find((item) => pathname.startsWith(item.to))?.value || "";
}
