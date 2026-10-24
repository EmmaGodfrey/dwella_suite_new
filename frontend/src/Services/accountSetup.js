import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./apiClient";
import { queryKeys } from "./queryKeys";

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
  const mutation = useMutation({
    mutationFn: (payload) => api.patch("/accounts/guided-tour/", payload),
    onSuccess: (data) => client.setQueryData(key, data),
    onError: (error) => { if ([400, 403].includes(error.status)) client.invalidateQueries({ queryKey: key }); },
  });
  return { ...query, mutation };
}
