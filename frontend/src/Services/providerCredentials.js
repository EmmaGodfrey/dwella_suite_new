import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./apiClient";

const key = ["platform", "provider-credentials"];
const path = "/platform/provider-credentials/";

export const useProviderCredentials = () => useQuery({
  queryKey: key,
  queryFn: ({ signal }) => api.get(path, { signal }),
  retry: false,
});

export function useReplaceProviderCredentials() {
  const cache = useQueryClient();
  return useMutation({
    gcTime: 0,
    retry: false,
    mutationFn: (payload) => api.post(path, payload),
    onSuccess: async (data) => {
      cache.setQueryData(key, data);
      await Promise.all([
        cache.invalidateQueries({ queryKey: ["platform", "runtime-settings"] }),
        cache.invalidateQueries({ queryKey: ["settings", "messaging"] }),
      ]);
    },
    onSettled: (_, __, payload) => {
      // The mutation cache may outlive its drawer. Retain no submitted secrets.
      payload.password = "";
      payload.code = "";
      for (const name of Object.keys(payload.values)) payload.values[name] = "";
    },
  });
}
