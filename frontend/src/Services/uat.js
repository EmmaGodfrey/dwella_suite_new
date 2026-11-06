import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./apiClient";

const key = (userId) => ["uat", userId];

export function useUatChecklist(userId) {
  return useQuery({
    queryKey: key(userId),
    queryFn: ({ signal }) => api.get("/accounts/uat/", { signal }),
    enabled: Boolean(userId),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
    retry: false,
  });
}

export function useSaveUatResult(userId, caseId) {
  const client = useQueryClient();
  return useMutation({
    mutationKey: ["uat-result", userId, caseId],
    scope: { id: `uat-${userId}-${caseId}` },
    mutationFn: (data) => api.patch(`/accounts/uat/results/${caseId}/`, data),
    retry: false,
    onMutate: () => client.cancelQueries({ queryKey: key(userId), exact: true }),
    onSuccess: (row) => client.setQueryData(key(userId), (data) => data ? {
      ...data, results: [...data.results.filter((old) => old.case_id !== row.case_id), row],
    } : data),
  });
}

export function useExportUatResults() {
  return useMutation({
    mutationFn: async ({ email = "" } = {}) => {
      const address = email.trim();
      if (address && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(address))
        throw new Error("Enter a valid tester email, or leave it blank for all testers.");
      const suffix = address ? `?email=${encodeURIComponent(address)}` : "";
      const blob = await api.get(`/accounts/uat/export/${suffix}`, { responseType: "blob" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "dwella-test-results.csv";
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1_000);
    },
    retry: false,
  });
}
