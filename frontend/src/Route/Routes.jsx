//Pages
import Dashboard from "../Components/Dashboard";
import LeaseDetail from "../Components/Leases/LeaseDetail";
import Leases from "../Components/Leases";
import Tenants from "../Components/Tenants";
import ModulePlaceholder from "../Components/ModulePlaceholder";
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
    Component: <Tenants />,
  },
  {
    path: `/leases`,
    title: "Leases",
    description: "Lease terms, renewals, deposits, and documents.",
    Component: <Leases />,
  },
  {
    path: `/leases/:id`,
    title: "Lease",
    description: "Lease terms and history.",
    Component: <LeaseDetail />,
  },
  {
    path: `/billing`,
    title: "Billing",
    description: "Rent invoices, collections, balances, and payment tracking.",
    Component: <ModulePlaceholder description="Rent invoices, collections, balances, and payment tracking." />,
  },
  {
    path: `/maintenance`,
    title: "Maintenance",
    description: "Work orders, vendors, approvals, and service tracking.",
    Component: <ModulePlaceholder description="Work orders, vendors, approvals, and service tracking." />,
  },
  {
    path: `/reports`,
    title: "Reports",
    description: "Portfolio, arrears, occupancy, and owner reporting.",
    Component: <ModulePlaceholder description="Portfolio, arrears, occupancy, and owner reports." />,
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
];
