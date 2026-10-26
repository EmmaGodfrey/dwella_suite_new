import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "./apiClient";
import { queryClient } from "./queryClient";
import { toSearchParams } from "./queries";

const keys = (...parts) => ["onlinePayments", ...parts];

export function usePlatformTransactions(filters) {
  return useQuery({ queryKey: keys("platform", filters),
    queryFn: ({ signal }) => api.get(`/payments/platform/transactions/${toSearchParams(filters)}`, { signal }),
    retry: false });
}

export function usePaymentRecord(path, options = {}) {
  return useQuery({ queryKey: keys("record", path),
    queryFn: ({ signal }) => api.get(`/payments/platform/${path}`, { signal }),
    enabled: Boolean(path), retry: false, refetchOnWindowFocus: false, gcTime: 0, ...options });
}

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
    queryClient.invalidateQueries({ queryKey: keys("payouts") }),
  ]),
});

export const useCheckReceivingAccount = () => useMutation({
  mutationFn: (details) => api.post("/payments/destination/check/", details),
  retry: false,
});

export const useBanks = (options = {}) => useQuery({
  queryKey: keys("banks"),
  queryFn: ({ signal }) => api.get("/payments/banks/", { signal }),
  staleTime: 60 * 60_000,
  retry: false,
  ...options,
});

const sending = (rows) => rows?.some((row) => ["queued", "submitting", "pending"].includes(row.status));

export const usePayoutSummary = () => useQuery({
  queryKey: keys("payouts", "summary"),
  queryFn: ({ signal }) => api.get("/payments/payouts/", { signal }),
  retry: false,
  refetchInterval: (query) => Number(query.state.data?.processing) > 0 ? 20_000 : false,
});

export const useWithdrawals = (page) => useQuery({
  queryKey: keys("payouts", "withdrawals", page),
  queryFn: ({ signal }) => api.get(`/payments/withdrawals/?page=${page}&page_size=20`, { signal }),
  retry: false,
  placeholderData: (previous) => previous,
  refetchInterval: (query) => sending(query.state.data?.results) ? 20_000 : false,
});

export const usePreviewWithdrawal = () => useMutation({
  mutationFn: (amount) => api.post("/payments/withdrawals/preview/", { amount }),
  retry: false,
});

const refreshPayouts = () => queryClient.invalidateQueries({ queryKey: keys("payouts") });

export const useRequestWithdrawal = () => useMutation({
  mutationFn: ({ amount, fee, idempotencyKey }) => api.post("/payments/withdrawals/", {
    amount, fee, idempotency_key: idempotencyKey,
  }),
  retry: false,
  onSettled: refreshPayouts,
});

export const useCancelWithdrawal = () => useMutation({
  mutationFn: (id) => api.post(`/payments/withdrawals/${id}/cancel/`, {}),
  retry: false,
  onSettled: refreshPayouts,
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
