import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "./apiClient";
import { queryClient } from "./queryClient";

const keys = (...parts) => ["onlinePayments", ...parts];

export const useReceivingDetails = (options = {}) => useQuery({
  queryKey: keys("destination"),
  queryFn: ({ signal }) => api.get("/payments/destination/", { signal }),
  retry: false,
  ...options,
});

export const useSaveReceivingDetails = () => useMutation({
  mutationFn: (details) => api.post("/payments/destination/", details),
  retry: false,
  onSuccess: () => Promise.all([
    queryClient.invalidateQueries({ queryKey: keys("destination") }),
    queryClient.invalidateQueries({ queryKey: keys("options") }),
  ]),
});

export const useTenantPaymentOptions = () => useQuery({
  queryKey: keys("options"), queryFn: () => api.get("/payments/tenant/options/"), retry: false,
});

export const useTenantCollections = (invoiceId) => useQuery({
  queryKey: keys("tenant", invoiceId),
  queryFn: () => api.get(`/payments/tenant/collections/?invoice=${invoiceId}`),
  enabled: Boolean(invoiceId), retry: false,
  refetchInterval: (query) => query.state.data?.results?.some((row) => row.status === "pending") ? 15_000 : false,
});

export const useManagerCollections = (invoiceId) => useQuery({
  queryKey: keys("manager", invoiceId),
  queryFn: () => api.get(`/payments/collections/?invoice=${invoiceId}`),
  enabled: Boolean(invoiceId), retry: false,
  refetchInterval: (query) => query.state.data?.results?.some((row) => row.status === "pending" ||
    (row.status === "successful" && !row.settled) || ["queued", "submitting", "pending"].includes(row.payout?.status)) ? 15_000 : false,
});

export const useStartRentCheckout = () => useMutation({
  mutationFn: ({ invoiceId, amount, idempotencyKey, channel, phone, operator }) => api.post(
    `/payments/tenant/invoices/${invoiceId}/checkout/`, {
      amount, idempotency_key: idempotencyKey, channel,
      ...(channel === "mobile-money" ? { phone, operator } : {}),
    }),
  retry: false,
  onSettled: () => queryClient.invalidateQueries({ queryKey: keys("tenant") }),
});

export const useRequestPaymentCheck = () => useMutation({
  mutationFn: (id) => api.post(`/payments/tenant/collections/${id}/`, {}),
  retry: false,
  onSuccess: () => queryClient.invalidateQueries({ queryKey: keys("tenant") }),
});

export function refreshPaymentRecords() {
  for (const key of [["portal"], ["billing"], ["reports"], ["properties", "dashboard"], ["notifications"]]) {
    queryClient.invalidateQueries({ queryKey: key });
  }
}
