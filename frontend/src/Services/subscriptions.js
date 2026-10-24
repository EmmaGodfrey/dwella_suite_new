import { useQuery } from "@tanstack/react-query";
import { api } from "./apiClient";
import { queryKeys } from "./queryKeys";

export function useWorkspaceEntitlementsQuery(options = {}) {
  return useQuery({
    queryKey: queryKeys.workspaceEntitlements,
    queryFn: () => api.get("/subscriptions/entitlements/"),
    staleTime: 0,
    retry: false,
    ...options,
  });
}
