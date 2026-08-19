import { useMutation } from "@tanstack/react-query";

import { login } from "./auth";
import { api } from "./apiClient";
import { queryClient } from "./queryClient";
import { queryKeys } from "./queryKeys";

export function useLoginMutation(options = {}) {
  return useMutation({
    mutationFn: login,
    onSuccess: (data, variables, context) => {
      queryClient.setQueryData(queryKeys.currentUser, data.user);
      options.onSuccess?.(data, variables, context);
    },
    onError: options.onError,
  });
}

export function useCreatePropertyMutation(options = {}) {
  return useMutation({
    mutationFn: (payload) => api.post("/properties/", payload),
    onSuccess: (data, variables, context) => {
      queryClient.invalidateQueries({ queryKey: ["properties"] });
      options.onSuccess?.(data, variables, context);
    },
    onError: options.onError,
  });
}
