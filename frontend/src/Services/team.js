import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./apiClient";
import { toSearchParams } from "./queries";

const TEAM = "/organizations/team/";
export const teamKeys = {
  team: ["organizations", "team"],
  activity: (page) => ["organizations", "team", "activity", page],
};

export const useTeam = (options = {}) => useQuery({
  queryKey: teamKeys.team,
  queryFn: ({ signal }) => api.get(TEAM, { signal }),
  retry: false,
  ...options,
});

export const useTeamActivity = (page = 1, options = {}) => useQuery({
  queryKey: teamKeys.activity(page),
  queryFn: ({ signal }) => api.get(`${TEAM}activity/${toSearchParams({ page, page_size: 25 })}`, { signal, raw: true }),
  retry: false,
  ...options,
});

// Every team change answers with the whole team, so the page never shows a
// half-updated list.
function useTeamChange(mutationFn, { everything = false } = {}) {
  const client = useQueryClient();
  return useMutation({
    mutationFn,
    retry: false,
    onSuccess: async (data) => {
      client.setQueryData(teamKeys.team, data);
      // A cover changes which properties this person can see: drop every list
      // held from before so nothing from the old scope stays on screen.
      if (everything) await client.invalidateQueries();
      else await client.invalidateQueries({ queryKey: ["organizations", "team", "activity"] });
    },
  });
}

export const useInviteMember = () => useTeamChange((payload) => api.post(`${TEAM}invitations/`, payload));
export const useRevokeInvitation = () => useTeamChange((id) => api.post(`${TEAM}invitations/${id}/revoke/`, {}));
export const useUpdateMember = () => useTeamChange(({ id, ...payload }) => api.patch(`${TEAM}members/${id}/`, payload));
export const useRemoveMember = () => useTeamChange((id) => api.delete(`${TEAM}members/${id}/`));
export const useCoverSetting = () => useTeamChange((allow) => api.patch(TEAM, { allow_teammate_cover: allow }), { everything: true });
export const useStartCover = () => useTeamChange((payload) => api.post(`${TEAM}cover/`, payload), { everything: true });
export const useEndCover = () => useTeamChange((id) => api.delete(id ? `${TEAM}cover/${id}/` : `${TEAM}cover/`), { everything: true });

export function useTeamInvitationPreview(options = {}) {
  return useMutation({ gcTime: 0, mutationFn: (token) => api.post("/accounts/team-invitations/preview/", { token }), ...options });
}

export function useTeamInvitationAccept(options = {}) {
  const client = useQueryClient();
  return useMutation({
    gcTime: 0,
    mutationFn: (payload) => api.post("/accounts/team-invitations/accept/", payload),
    ...options,
    onSuccess: (data) => { client.clear(); options.onSuccess?.(data); },
  });
}
