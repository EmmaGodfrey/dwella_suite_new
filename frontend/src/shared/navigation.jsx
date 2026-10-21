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
  Wrench24Regular,
} from "@fluentui/react-icons";

import { getUserAccess } from "./access";

// Sidebar sections, in display order. An item's `group` places it under one of
// these; a group with no visible items for the persona is not rendered.
export const navigationGroups = [
  { value: "overview", label: "Overview" },
  { value: "portfolio", label: "Portfolio" },
  { value: "operations", label: "Operations" },
  { value: "platform", label: "Platform" },
];

const operationalItems = [
  { to: "/setup", value: "setup", group: "overview", label: "Get started", icon: <CheckmarkCircle24Regular />, personas: ["landlord", "unassigned"] },
  { to: "/dashboard", value: "dashboard", group: "overview", label: "Dashboard", icon: <Home24Regular />, personas: ["platform_admin", "landlord", "tenant"] },
  { to: "/reports", value: "reports", group: "overview", label: "Reports", icon: <DataTrending24Regular />, personas: ["platform_admin", "landlord"] },
  { to: "/properties", value: "properties", group: "portfolio", label: "Properties", icon: <Building24Regular />, personas: ["platform_admin", "landlord"] },
  { to: "/tenants", value: "tenants", group: "portfolio", label: "Tenants", icon: <People24Regular />, personas: ["platform_admin", "landlord"] },
  { to: "/leases", value: "leases", group: "portfolio", label: "Leases", tenantLabel: "My lease", icon: <DocumentText24Regular />, personas: ["platform_admin", "landlord", "tenant"] },
  { to: "/billing", value: "billing", group: "operations", label: "Billing", tenantLabel: "Payments", icon: <Payment24Regular />, personas: ["platform_admin", "landlord", "tenant"] },
  { to: "/maintenance", value: "maintenance", group: "operations", label: "Maintenance", icon: <Wrench24Regular />, personas: ["platform_admin", "landlord", "tenant"] },
  { to: "/beta-signups", value: "beta-signups", group: "platform", label: "Beta signups", icon: <FormMultiple24Regular />, personas: ["platform_admin"] },
];

export function getNavigationItems(user) {
  const access = getUserAccess(user);
  return operationalItems
    .filter((item) => item.personas.includes(access.persona))
    .map((item) => ({
      ...item,
      label: access.persona === "tenant" && item.tenantLabel ? item.tenantLabel : item.label,
    }));
}

export const pageMeta = {
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
    if (pathname === "/leases") return ["My lease", "Lease details, documents, and renewal information."];
    if (pathname === "/billing") return ["Payments", "Rent charges, receipts, and payment history."];
  }
  if (access.persona === "platform_admin" && pathname === "/dashboard") {
    return ["Administration", "Landlord activity and platform portfolio oversight."];
  }
  // Detail pages (`/leases/<id>`) take their section's title.
  const section = Object.keys(pageMeta).find((path) => pathname.startsWith(`${path}/`));
  return pageMeta[pathname] || pageMeta[section] || ["Dwella Suite", "Property operations workspace."];
}

export function canAccessPath(pathname, user) {
  if (["/profile", "/security", "/dashboard", "/"].includes(pathname)) return true;
  return getNavigationItems(user).some((item) => pathname.startsWith(item.to));
}

export function getSelectedNavValue(pathname, user) {
  return getNavigationItems(user).find((item) => pathname.startsWith(item.to))?.value || "";
}
