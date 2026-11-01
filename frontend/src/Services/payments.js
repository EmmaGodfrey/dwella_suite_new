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

// Ways tenants pay the workspace directly; printed on every invoice.
const instructionKey = ["billing", "payment-instructions"];

export const usePaymentInstructions = () => useQuery({
  queryKey: instructionKey,
  queryFn: ({ signal }) => api.get("/billing/payment-instructions/", { signal }),
  retry: false,
});

export const useSavePaymentInstruction = () => useMutation({
  mutationFn: ({ id, ...data }) => id
    ? api.patch(`/billing/payment-instructions/${id}/`, data)
    : api.post("/billing/payment-instructions/", data),
  retry: false,
  onSuccess: () => queryClient.invalidateQueries({ queryKey: instructionKey }),
});

export const useRemovePaymentInstruction = () => useMutation({
  mutationFn: (id) => api.delete(`/billing/payment-instructions/${id}/`),
  retry: false,
  onSuccess: () => queryClient.invalidateQueries({ queryKey: instructionKey }),
});

// Security deposits (held for the tenant, separate from rent).
const depositKey = (leaseId) => ["deposits", leaseId];

export const useDeposit = (leaseId, options = {}) => useQuery({
  queryKey: depositKey(leaseId),
  queryFn: ({ signal }) => api.get(`/billing/deposits/${leaseId}/`, { signal }),
  enabled: Boolean(leaseId),
  retry: false,
  ...options,
});

// action: "request" | "opening" | "deductions" | "refunds"
export const useDepositAction = (leaseId) => useMutation({
  mutationFn: ({ action, ...data }) => api.post(`/billing/deposits/${leaseId}/${action}/`, data),
  retry: false,
  onSuccess: (data) => {
    queryClient.setQueryData(depositKey(leaseId), data);
    // A deposit request issues an invoice.
    queryClient.invalidateQueries({ queryKey: ["billing", "invoices"] });
  },
});

export const useDeductionDecision = (leaseId) => useMutation({
  mutationFn: ({ id, decision, ...data }) => api.post(`/billing/deposit-deductions/${id}/${decision}/`, data),
  retry: false,
  onSuccess: (data) => queryClient.setQueryData(depositKey(leaseId), data),
});

export const useTenantDeposits = () => useQuery({
  queryKey: ["portal", "deposits"],
  queryFn: ({ signal }) => api.get("/portal/deposits/", { signal }),
  retry: false,
});

export const useRespondToDeduction = () => useMutation({
  mutationFn: ({ id, ...data }) => api.post(`/portal/deposit-deductions/${id}/respond/`, data),
  retry: false,
  onSuccess: () => queryClient.invalidateQueries({ queryKey: ["portal", "deposits"] }),
});

// Photos and receipts behind a deduction. Files are sent one at a time so one
// bad file does not lose the others.
export async function uploadDeductionEvidence(leaseId, deductionId, files) {
  const failed = [];
  let latest = null;
  for (const file of files) {
    const body = new FormData();
    body.append("file", file);
    try {
      latest = await api.post(`/billing/deposit-deductions/${deductionId}/evidence/`, body);
    } catch (error) {
      failed.push({ name: file.name, message: error.data?.file?.[0] || error.message });
    }
  }
  if (latest) queryClient.setQueryData(depositKey(leaseId), latest);
  return failed;
}

// scope: "billing" (manager) or "portal" (tenant). Opens in a new tab when the
// browser can show it, otherwise downloads it.
export async function openDepositEvidence(scope, item) {
  const tab = window.open("", "_blank");
  try {
    const blob = await api.get(`/${scope}/deposit-evidence/${item.id}/`, { responseType: "blob" });
    const url = URL.createObjectURL(new Blob([blob], { type: item.content_type }));
    if (tab) tab.location.href = url;
    else {
      const anchor = document.createElement("a");
      anchor.href = url; anchor.download = item.name; anchor.click();
    }
    setTimeout(() => URL.revokeObjectURL(url), 60_000);
  } catch (error) {
    tab?.close();
    throw error;
  }
}
