import { useMutation, useQuery } from "@tanstack/react-query";

import { api } from "./apiClient";
import { queryClient } from "./queryClient";
import { toSearchParams } from "./queries";

// Tenant self-service. Every call goes to /portal/, which only ever returns
// the signed-in tenant's own records.
const key = (...parts) => ["portal", ...parts];
const get = (path) => api.get(`/portal/${path}`);
// A tenant without a linked tenancy gets 403 `tenancy_not_linked`; pages show
// a dedicated state for it, so it is not retried.
const retry = (count, error) => error?.status !== 403 && error?.status !== 404 && count < 2;

export const isNotLinked = (error) => error?.status === 403;

export const usePortalOverview = (options = {}) =>
  useQuery({ queryKey: key("overview"), queryFn: () => get("overview/"), retry, staleTime: 30_000, ...options });
export const usePortalProfile = (options = {}) =>
  useQuery({ queryKey: key("profile"), queryFn: () => get("profile/"), retry, ...options });
export const usePortalLeases = (options = {}) =>
  useQuery({ queryKey: key("leases"), queryFn: () => get("leases/?page_size=50"), retry, staleTime: 60_000, ...options });
export const usePortalLeaseDocuments = (id, options = {}) =>
  useQuery({ queryKey: key("leases", id, "documents"), queryFn: () => get(`leases/${id}/documents/`), enabled: Boolean(id), retry, ...options });
export const usePortalInvoices = (filters = {}, options = {}) =>
  useQuery({ queryKey: key("invoices", filters), queryFn: () => get(`invoices/${toSearchParams(filters)}`), retry, staleTime: 30_000, ...options });
export const usePortalInvoice = (id, options = {}) =>
  useQuery({ queryKey: key("invoices", "detail", id), queryFn: () => get(`invoices/${id}/`), enabled: Boolean(id), retry, ...options });
export const usePortalPayments = (filters = {}, options = {}) =>
  useQuery({ queryKey: key("payments", filters), queryFn: () => get(`payments/${toSearchParams(filters)}`), retry, staleTime: 30_000, ...options });
export const usePortalReceipt = (id, options = {}) =>
  useQuery({ queryKey: key("payments", "detail", id), queryFn: () => get(`payments/${id}/`), enabled: Boolean(id), retry, ...options });
export const usePortalRequests = (filters = {}, options = {}) =>
  useQuery({ queryKey: key("maintenance", filters), queryFn: () => get(`maintenance/${toSearchParams(filters)}`), retry, staleTime: 15_000, ...options });
export const usePortalRequest = (id, options = {}) =>
  useQuery({ queryKey: key("maintenance", "detail", id), queryFn: () => get(`maintenance/${id}/`), enabled: Boolean(id), retry, ...options });

const portalMutation = (mutationFn, after) => (options = {}) =>
  useMutation({
    mutationFn,
    onSuccess: (data, variables, context) => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      after?.(data);
      options.onSuccess?.(data, variables, context);
    },
    onError: options.onError,
  });

export const useReportRepair = portalMutation(
  (payload) => api.post("/portal/maintenance/", payload),
  () => {
    queryClient.invalidateQueries({ queryKey: key("maintenance") });
    queryClient.invalidateQueries({ queryKey: key("overview") });
  },
);

// Messages and photos return the updated request, so the detail cache is
// replaced rather than refetched.
const putRequest = (data) => {
  queryClient.setQueryData(key("maintenance", "detail", data.id), data);
  queryClient.invalidateQueries({ queryKey: key("maintenance"), exact: false, refetchType: "none" });
};
export const useRepairMessage = portalMutation(
  ({ id, body }) => api.post(`/portal/maintenance/${id}/updates/`, { body }),
  putRequest,
);
export const useRepairPhoto = portalMutation(({ id, file }) => {
  const body = new FormData();
  body.append("image", file);
  return api.post(`/portal/maintenance/${id}/photos/`, body);
}, putRequest);

export const useUpdatePortalProfile = portalMutation(
  (payload) => api.patch("/portal/profile/", payload),
  (data) => queryClient.setQueryData(key("profile"), data),
);

// Document clients for the shared paper preview. Lease versions and invoices
// are fetched through the portal, never the management endpoints.
export const portalDocuments = {
  get: (id, operation, params = "") =>
    api.get(`/portal/documents/${id}/${operation}/${params}`, { responseType: "blob" }),
};
export const portalInvoiceDocuments = (invoiceId) => ({
  get: (_, operation, params = "") =>
    api.get(`/portal/invoices/${invoiceId}/${operation}/${params}`, {
      ...(["pdf", "page"].includes(operation) ? { responseType: "blob" } : {}),
    }),
});

export async function downloadPortalFile(path, filename) {
  const blob = await api.get(`/portal/${path}`, { responseType: "blob" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
