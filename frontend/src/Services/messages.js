import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./apiClient";

const base = "notifications/";
export function useMessageHistory(filters, platform = false) {
  return useQuery({ queryKey: ["messages", platform, filters], queryFn: () => api.get(`${base}${platform ? "platform-messages" : "messages"}/?${new URLSearchParams(filters)}`) });
}
export function useMessageRecipients(search, page = 1) {
  return useQuery({ queryKey: ["message-recipients", search, page], queryFn: () => api.get(`${base}message-recipients/?${new URLSearchParams({ search, page, page_size: 50 })}`) });
}
export function useMessageAction(action) {
  const client = useQueryClient();
  return useMutation({ mutationFn: ({ id, ...data }) => api.post(action === "preview" ? `${base}message-previews/` : action === "confirm" ? `${base}message-previews/${id}/confirm/` : `${base}messages/${id}/`, data), onSuccess: () => client.invalidateQueries({ queryKey: ["messages"] }) });
}
export function useMessageDetail(id) {
  return useQuery({ queryKey: ["messages", "detail", id], enabled: Boolean(id), queryFn: () => api.get(`${base}messages/${id}/`) });
}
