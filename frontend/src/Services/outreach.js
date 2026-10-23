import { useMutation } from "@tanstack/react-query";
import { api } from "./apiClient";
import {
  usePlatformChoices,
  usePlatformDetail,
  usePlatformList,
  usePlatformMutation,
} from "./platform";

export const useOutreachList = (resource, filters = {}, options = {}) =>
  usePlatformList(`outreach/${resource}`, filters, options);
export const useOutreachChoices = (resource, filters = {}, options = {}) =>
  usePlatformChoices(`outreach/${resource}`, filters, options);
export const useOutreachDetail = (resource, id, options = {}) =>
  usePlatformDetail(`outreach/${resource}`, id, options);
export function useOutreachMutation() {
  const mutation = usePlatformMutation();
  return {
    ...mutation,
    mutateAsync: ({ resource, ...args }) =>
      mutation.mutateAsync({ resource: `outreach/${resource}`, ...args }),
  };
}
export function useOutreachPreview() {
  return useMutation({
    mutationFn: ({ resource, id, body }) =>
      api.post(
        `/platform/outreach/${resource}/${id ? `${id}/` : ""}preview/`,
        body,
      ),
  });
}
export async function readContactCSV(file) {
  if (file.size > 1_000_000) throw new Error("Choose a CSV smaller than 1 MB.");
  return file.text();
}
