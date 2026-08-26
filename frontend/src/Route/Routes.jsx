//Pages
import Dashboard from "../Components/Dashboard";
import ModulePlaceholder from "../Components/ModulePlaceholder";
import SamplePage from "../Components/Pages/Sample";
import Properties from "../Components/Properties";
import Profile from "../Components/Profile";
import Security from "../Components/Security";

export const routes = [
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
    Component: <ModulePlaceholder title="Tenants" description="Tenant CRM, occupancy records, and communication history." />,
  },
  {
    path: `/leases`,
    title: "Leases",
    description: "Lease terms, renewals, deposits, and documents.",
    Component: <ModulePlaceholder title="Leases" description="Lease terms, renewals, deposits, and documents." />,
  },
  {
    path: `/billing`,
    title: "Billing",
    description: "Rent invoices, collections, balances, and payment tracking.",
    Component: <ModulePlaceholder title="Billing" description="Rent invoices, collections, balances, and payment tracking." />,
  },
  {
    path: `/maintenance`,
    title: "Maintenance",
    description: "Work orders, vendors, approvals, and service tracking.",
    Component: <ModulePlaceholder title="Maintenance" description="Work orders, vendors, approvals, and service tracking." />,
  },
  {
    path: `/reports`,
    title: "Reports",
    description: "Portfolio, arrears, occupancy, and owner reporting.",
    Component: <ModulePlaceholder title="Reports" description="Portfolio, arrears, occupancy, and owner reports." />,
  },
  {
    path: `/profile`,
    title: "Profile",
    description: "Account details, identity verification, and profile photo.",
    Component: <Profile />,
  },
  {
    path: `/security`,
    title: "Security",
    description: "Two-factor authentication and account protection.",
    Component: <Security />,
  },
  { path: `/pages/sample-page`, title: "Sample", description: "Template reference page.", Component: <SamplePage /> },
];
