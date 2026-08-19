//Pages
import Dashboard from "../Components/Dashboard";
import ModulePlaceholder from "../Components/ModulePlaceholder";
import SamplePage from "../Components/Pages/Sample";
import Properties from "../Components/Properties";

export const routes = [
  //page
  { path: `/dashboard`, Component: <Dashboard /> },
  { path: `/properties`, Component: <Properties /> },
  { path: `/tenants`, Component: <ModulePlaceholder title="Tenants" description="Tenant CRM, occupancy records, and communication history." /> },
  { path: `/leases`, Component: <ModulePlaceholder title="Leases" description="Lease terms, renewals, deposits, and documents." /> },
  { path: `/billing`, Component: <ModulePlaceholder title="Billing" description="Rent invoices, collections, balances, and payment tracking." /> },
  { path: `/maintenance`, Component: <ModulePlaceholder title="Maintenance" description="Work orders, vendors, approvals, and service tracking." /> },
  { path: `/reports`, Component: <ModulePlaceholder title="Reports" description="Portfolio, arrears, occupancy, and owner reports." /> },
  { path: `/pages/sample-page`, Component: <SamplePage /> },
];
