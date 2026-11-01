import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./apiClient";

const base = "notifications/";
export function useMessageHistory(filters, platform = false, operational = false) {
  const resource = operational ? (platform ? "platform-operational-messages" : "operational-messages") : (platform ? "platform-messages" : "messages");
  return useQuery({ queryKey: ["messages", platform, operational, filters], queryFn: () => api.get(`${base}${resource}/?${new URLSearchParams(filters)}`) });
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
