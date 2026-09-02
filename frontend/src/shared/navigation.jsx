import React from "react";
import {
  Building24Regular,
  DocumentText24Regular,
  Home24Regular,
  Payment24Regular,
  People24Regular,
  Settings24Regular,
  Wrench24Regular,
} from "@fluentui/react-icons";

export const navigationItems = [
  { to: "/dashboard", value: "dashboard", label: "Dashboard", icon: <Home24Regular /> },
  { to: "/properties", value: "properties", label: "Properties", icon: <Building24Regular /> },
  { to: "/tenants", value: "tenants", label: "Tenants", icon: <People24Regular /> },
  { to: "/leases", value: "leases", label: "Leases", icon: <DocumentText24Regular /> },
  { to: "/billing", value: "billing", label: "Billing", icon: <Payment24Regular /> },
  { to: "/maintenance", value: "maintenance", label: "Maintenance", icon: <Wrench24Regular /> },
  { to: "/reports", value: "reports", label: "Reports", icon: <Settings24Regular /> },
];

export const pageMeta = {
  "/dashboard": ["Dashboard", "Portfolio health, occupancy, rent roll, and current work."],
  "/properties": ["Properties", "Search, filter, and grow the property portfolio."],
  "/tenants": ["Tenants", "Tenant CRM, occupancy records, and communication history."],
  "/leases": ["Leases", "Lease terms, renewals, deposits, and documents."],
  "/billing": ["Billing", "Rent invoices, collections, balances, and payment tracking."],
  "/maintenance": ["Maintenance", "Work orders, vendors, approvals, and service tracking."],
  "/reports": ["Reports", "Portfolio, arrears, occupancy, and owner reporting."],
  "/profile": ["Profile", "Account details, identity verification, and profile photo."],
  "/security": ["Security", "Two-factor authentication and account protection."],
};

export function getSelectedNavValue(pathname) {
  return navigationItems.find((item) => pathname.startsWith(item.to))?.value || "";
}
