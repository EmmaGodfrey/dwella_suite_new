import { useMutation } from "@tanstack/react-query";

import { api } from "./apiClient";
import { queryClient } from "./queryClient";
import { queryKeys } from "./queryKeys";

// CSV imports for units and tenants: template, preview, then one confirmation.
const bases = { units: "/properties/units", tenants: "/tenants", tenancies: "/tenants" };
const suffix = (kind) => kind === "tenancies" ? "?kind=tenancies" : "";

export function useImportTemplate(kind, options = {}) {
  return useMutation({
    mutationFn: async () => {
      const blob = await api.get(`${bases[kind]}/import-template/${suffix(kind)}`, { responseType: "blob" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `dwella-${kind}-template.csv`;
      anchor.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    },
    ...options,
  });
}

export function useImportPreview(kind, options = {}) {
  return useMutation({
    mutationFn: (file) => {
      const body = new FormData(); body.append("file", file);
      return api.post(`${bases[kind]}/import-preview/${suffix(kind)}`, body);
    },
    ...options,
  });
}

export function useImportConfirm(kind, options = {}) {
  return useMutation({
    mutationFn: (previewToken) => api.post(`${bases[kind]}/import-confirm/${suffix(kind)}`, { preview_token: previewToken }),
    onSuccess: (data, variables, context) => {
      queryClient.invalidateQueries({ queryKey: [kind === "units" ? "properties" : "tenants"] });
      if (kind === "tenancies") for (const key of ["properties", "leases", "reports"]) queryClient.invalidateQueries({ queryKey: [key] });
      queryClient.invalidateQueries({ queryKey: queryKeys.onboarding });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboardSummary });
      queryClient.invalidateQueries({ queryKey: queryKeys.workspaceEntitlements });
      options.onSuccess?.(data, variables, context);
    },
    onError: options.onError,
  });
}
