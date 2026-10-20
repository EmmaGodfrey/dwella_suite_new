import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { apiRequest, getApiBaseUrl } from "./apiClient";
import { queryKeys } from "./queryKeys";

const toSearchParams = (filters = {}) => {
  const params = new URLSearchParams();

  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      params.set(key, value);
    }
  });

  const query = params.toString();
  return query ? `?${query}` : "";
};

export function useHealthQuery() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: async () => {
      const healthUrl = getApiBaseUrl().replace(/\/api\/v1$/, "/api/health/");
      const response = await fetch(healthUrl);

      if (!response.ok) {
        throw new Error("Health check failed");
      }

      return response.json();
    },
  });
}

export function useCurrentUserQuery(options = {}) {
  return useQuery({
    queryKey: queryKeys.currentUser,
    queryFn: () => apiRequest("/accounts/me/"),
    ...options,
  });
}

export function useDashboardSummaryQuery(options = {}) {
  return useQuery({
    queryKey: queryKeys.dashboardSummary,
    queryFn: () => apiRequest("/properties/dashboard/"),
    placeholderData: keepPreviousData,
    staleTime: 60_000,
    ...options,
  });
}

export function useOrganizationsQuery(filters = {}, options = {}) {
  return useQuery({
    queryKey: queryKeys.organizations,
    queryFn: () => apiRequest(`/organizations/${toSearchParams(filters)}`),
    ...options,
  });
}

export function usePropertiesQuery(filters = {}, options = {}) {
  return useQuery({
    queryKey: queryKeys.properties(filters),
    queryFn: () => apiRequest(`/properties/${toSearchParams(filters)}`),
    ...options,
  });
}

export function usePropertyQuery(id, options = {}) {
  return useQuery({
    queryKey: queryKeys.property(id),
    queryFn: () => apiRequest(`/properties/${id}/`),
    enabled: Boolean(id),
    ...options,
  });
}

export function usePropertyOwnersQuery(filters = {}, options = {}) {
  return useQuery({
    queryKey: queryKeys.propertyOwners(filters),
    queryFn: () => apiRequest(`/properties/owners/${toSearchParams(filters)}`),
    ...options,
  });
}

export function useUnitsQuery(filters = {}, options = {}) {
  return useQuery({
    queryKey: queryKeys.units(filters),
    queryFn: () => apiRequest(`/properties/units/${toSearchParams(filters)}`),
    ...options,
  });
}

export function useTenantsQuery(filters = {}, options = {}) {
  return useQuery({
    queryKey: queryKeys.tenants(filters),
    queryFn: () => apiRequest(`/tenants/${toSearchParams(filters)}`),
    ...options,
  });
}

export function useTenantQuery(id, options = {}) {
  return useQuery({
    queryKey: queryKeys.tenant(id),
    queryFn: () => apiRequest(`/tenants/${id}/`),
    enabled: Boolean(id),
    ...options,
  });
}

export function useLeasesQuery(filters = {}, options = {}) {
  return useQuery({
    queryKey: queryKeys.leases(filters),
    queryFn: () => apiRequest(`/leases/${toSearchParams(filters)}`),
    ...options,
  });
}

export function useLeaseQuery(id, options = {}) {
  return useQuery({
    queryKey: queryKeys.lease(id),
    queryFn: () => apiRequest(`/leases/${id}/`),
    enabled: Boolean(id),
    ...options,
  });
}

export function useInvoicesQuery(filters = {}, options = {}) {
  return useQuery({
    queryKey: queryKeys.invoices(filters),
    queryFn: () => apiRequest(`/billing/invoices/${toSearchParams(filters)}`),
    ...options,
  });
}

export function useInvoiceQuery(id, options = {}) {
  return useQuery({
    queryKey: queryKeys.invoice(id),
    queryFn: () => apiRequest(`/billing/invoices/${id}/`),
    enabled: Boolean(id),
    ...options,
  });
}

export function useBillingSummaryQuery(options = {}) {
  return useQuery({
    queryKey: queryKeys.billingSummary,
    queryFn: () => apiRequest("/billing/invoices/summary/"),
    staleTime: 30_000,
    ...options,
  });
}

export function usePaymentsQuery(filters = {}, options = {}) {
  return useQuery({
    queryKey: queryKeys.payments(filters),
    queryFn: () => apiRequest(`/billing/payments/${toSearchParams(filters)}`),
    ...options,
  });
}

export function useMaintenanceRequestsQuery(filters = {}, options = {}) {
  return useQuery({
    queryKey: queryKeys.maintenanceRequests(filters),
    queryFn: () => apiRequest(`/maintenance/requests/${toSearchParams(filters)}`),
    placeholderData: keepPreviousData,
    ...options,
  });
}

export function useMaintenanceRequestQuery(id, options = {}) {
  return useQuery({
    queryKey: queryKeys.maintenanceRequest(id),
    queryFn: () => apiRequest(`/maintenance/requests/${id}/`),
    enabled: Boolean(id),
    ...options,
  });
}

export function useMaintenanceSummaryQuery(options = {}) {
  return useQuery({
    queryKey: queryKeys.maintenanceSummary,
    queryFn: () => apiRequest("/maintenance/requests/summary/"),
    staleTime: 30_000,
    ...options,
  });
}

export function useVendorsQuery(filters = {}, options = {}) {
  return useQuery({
    queryKey: queryKeys.vendors(filters),
    queryFn: () => apiRequest(`/maintenance/vendors/${toSearchParams(filters)}`),
    ...options,
  });
}
