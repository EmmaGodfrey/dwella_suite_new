import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./apiClient";
import { queryKeys } from "./queryKeys";

const resources = {
  personal: "/notifications/preferences/",
  reminders: "/notifications/reminders/",
  messaging: "/notifications/platform-settings/",
  workspace: "/notifications/workspace-settings/",
  payments: "/payments/platform/configuration/",
  balance: "/payments/platform/balance/",
};

export function useSettingsResource(resource, options = {}) {
  return useQuery({
    queryKey: ["settings", resource],
    queryFn: ({ signal }) => api.get(resources[resource], { signal }),
    retry: false,
    ...options,
  });
}

export function useSaveSettings(resource) {
  const cache = useQueryClient();
  return useMutation({
    mutationFn: (data) => api.patch(resources[resource], data),
    retry: false,
    onSuccess: async () => {
      await Promise.all([
        cache.invalidateQueries({ queryKey: ["settings", resource] }),
        cache.invalidateQueries({ queryKey: ["notifications"] }),
        ...(resource === "workspace"
          ? [
              cache.invalidateQueries({ queryKey: queryKeys.currentUser }),
              cache.invalidateQueries({ queryKey: queryKeys.onboarding }),
            ]
          : []),
      ]);
    },
  });
}

export function useNotificationPhone() {
  return useQuery({
    queryKey: ["settings", "phone-link"],
    queryFn: () => api.get("/notifications/phone-link/"),
    retry: false,
    refetchInterval: (query) => query.state.data?.pending?.length ? 10_000 : false,
  });
}

export function useConnectNotificationPhone() {
  const cache = useQueryClient();
  return useMutation({
    mutationFn: (data) => api.post("/notifications/phone-link/", data),
    retry: false,
    onSuccess: async () => {
      await Promise.all([
        cache.invalidateQueries({ queryKey: ["settings", "phone-link"] }),
        cache.invalidateQueries({ queryKey: ["settings", "personal"] }),
      ]);
    },
  });
}
