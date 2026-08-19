import { useQuery } from "@tanstack/react-query";

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
