import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, apiRequest } from "./apiClient";
import { queryKeys } from "./queryKeys";

const search = (filters) => {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== "" && value !== undefined && value !== null) params.set(key, value);
  });
  return params.size ? `?${params}` : "";
};

export function usePlatformList(resource, filters = {}, options = {}) {
  return useQuery({
    queryKey: ["platform", resource, filters],
    queryFn: ({ signal }) => api.get(`/platform/${resource}/${search(filters)}`, { signal }),
    ...options,
  });
}

export function usePlatformDetail(resource, id, options = {}) {
  return useQuery({
    queryKey: ["platform", resource, String(id)],
    queryFn: ({ signal }) => api.get(`/platform/${resource}/${id}/`, { signal }),
    enabled: Boolean(id),
    ...options,
  });
}

export function usePlatformMutation(options = {}) {
  const cache = useQueryClient();
  return useMutation({
    mutationFn: ({ resource, id, action, body = {}, method = "post" }) => api[method](
      `/platform/${resource}/${id ? `${id}/` : ""}${action ? `${action}/` : ""}`, body,
    ),
    ...options,
    onSuccess: async (data, variables) => {
      await cache.invalidateQueries({ queryKey: ["platform"] });
      await cache.invalidateQueries({ queryKey: queryKeys.currentUser });
      options.onSuccess?.(data, variables);
    },
  });
}

export async function downloadPlatformFile(path, filename) {
  const blob = await apiRequest(`/platform/${path}`, { responseType: "blob" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
