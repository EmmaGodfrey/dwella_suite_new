import { useCurrentUserQuery } from "../Services/queries";
import { getUserAccess } from "../shared/access";

// Tenants share the manager's paths (/leases, /billing, /maintenance) but see
// their own self-service pages, backed by /portal/ instead of manager APIs.
export default function ForTenant({ tenant, children }) {
  const { data: user } = useCurrentUserQuery({ staleTime: 60_000 });
  return getUserAccess(user).persona === "tenant" ? tenant : children;
}
