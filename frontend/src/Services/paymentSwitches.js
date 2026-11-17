import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "./apiClient";

export function useSwitchPaymentMethods() {
  const cache = useQueryClient();
  return useMutation({
    gcTime: 0,
    retry: false,
    mutationFn: (payload) => api.post("/payments/platform/switches/", payload),
    onSuccess: () => cache.invalidateQueries({ queryKey: ["settings", "payments"] }),
    onSettled: (_, __, payload) => {
      // Do not keep the password or one-time code in the mutation cache.
      payload.password = "";
      payload.code = "";
    },
  });
}
