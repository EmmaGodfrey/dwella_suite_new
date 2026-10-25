import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./apiClient";
import { queryKeys } from "./queryKeys";
import { optimisticTourStep } from "../shared/tourState";

export function useVerificationMutation(options = {}) {
  const client = useQueryClient();
  return useMutation({
    gcTime: 0,
    mutationFn: (token) => token
      ? api.post("/accounts/email-verification/confirm/", { token })
      : api.post("/accounts/email-verification/", {}),
    ...options,
    onSuccess: async (data) => {
      await client.invalidateQueries({ queryKey: queryKeys.currentUser });
      options.onSuccess?.(data);
    },
  });
}

export function useInvitationPreview(options = {}) {
  return useMutation({ gcTime: 0, mutationFn: (token) => api.post("/accounts/invitations/preview/", { token }), ...options });
}

export function useInvitationAccept(options = {}) {
  const client = useQueryClient();
  return useMutation({
    gcTime: 0,
    mutationFn: (payload) => api.post("/accounts/invitations/accept/", payload),
    ...options,
    onSuccess: (data) => { client.clear(); options.onSuccess?.(data); },
  });
}

export function useTenantInvitation(id, options = {}) {
  return useMutation({
    mutationKey: ["tenant-invitation", id],
    mutationFn: (revoke) => api.post(`/tenants/${id}/${revoke ? "revoke-invite" : "invite"}/`, {}),
    ...options,
  });
}

export function useGuidedTour(user, enabled = true) {
  const client = useQueryClient();
  const key = ["accounts", "tour", user?.id, user?.access?.organization_id];
  const query = useQuery({
    queryKey: key,
    queryFn: () => api.get("/accounts/guided-tour/"),
    enabled: enabled && Boolean(user?.id),
  });
  const mutationKey = ["tour-progress", ...key];
  const mutation = useMutation({
    mutationKey,
    // Saves run one at a time in click order, so a quick Next, Next never races itself.
    scope: { id: mutationKey.join(":") },
    mutationFn: (payload) => api.patch("/accounts/guided-tour/", payload),
    onMutate: async ({ action }) => {
      await client.cancelQueries({ queryKey: key });
      const previous = client.getQueryData(key);
      const optimistic = optimisticTourStep(previous, action);
      if (optimistic) client.setQueryData(key, optimistic);
      return { previous };
    },
    onSuccess: (data) => {
      // A queued click already shows a later step; let the last save settle the state.
      if (client.isMutating({ mutationKey }) <= 1) client.setQueryData(key, data);
    },
    onError: (error, _, context) => {
      if (context?.previous) client.setQueryData(key, context.previous);
      client.invalidateQueries({ queryKey: key });
    },
  });
  return { ...query, mutation };
}
