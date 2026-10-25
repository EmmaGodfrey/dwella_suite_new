import { useMutation } from "@tanstack/react-query";

import { api } from "./apiClient";
import { queryClient } from "./queryClient";
import { queryKeys } from "./queryKeys";

// CSV imports for units and tenants: template, preview, then one confirmation.
const bases = { units: "/properties/units", tenants: "/tenants" };

export function useImportTemplate(kind, options = {}) {
  return useMutation({
    mutationFn: async () => {
      const blob = await api.get(`${bases[kind]}/import-template/`, { responseType: "blob" });
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
    mutationFn: (csv) => api.post(`${bases[kind]}/import-preview/`, { csv }),
    ...options,
  });
}

export function useImportConfirm(kind, options = {}) {
  return useMutation({
    mutationFn: (previewToken) => api.post(`${bases[kind]}/import-confirm/`, { preview_token: previewToken }),
    onSuccess: (data, variables, context) => {
      queryClient.invalidateQueries({ queryKey: [kind === "units" ? "properties" : "tenants"] });
      queryClient.invalidateQueries({ queryKey: queryKeys.onboarding });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboardSummary });
      queryClient.invalidateQueries({ queryKey: queryKeys.workspaceEntitlements });
      options.onSuccess?.(data, variables, context);
    },
    onError: options.onError,
  });
}
