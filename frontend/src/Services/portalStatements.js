import { useMutation, useQuery } from "@tanstack/react-query";

import { api } from "./apiClient";
import { toSearchParams } from "./queries";
import { downloadPortalFile } from "./portal";
import { portalStatementData } from "../shared/statement.mjs";

const retry = (count, error) => (!error?.status || error.status >= 500) && count < 1;

export function useStatementAccounts(page = 1) {
  return useQuery({
    queryKey: ["portal", "statement-accounts", page],
    queryFn: async ({ signal }) => {
      const response = await api.get(`/portal/statements/?page_size=50&page=${page}`, { signal });
      if (!Array.isArray(response?.results) || !Number.isInteger(response.pagination?.count)
          || !response.results.every((row) => row.id && typeof row.name === "string")) {
        throw new Error("Could not read your tenant accounts. Please try again.");
      }
      return response;
    },
    retry, staleTime: 0,
  });
}

export function usePortalStatement(accountId, period, page) {
  return useQuery({
    queryKey: ["portal", "statement", accountId, period, page],
    queryFn: async ({ signal }) => portalStatementData(await api.get(
      `/portal/statements/${accountId}/${toSearchParams({ ...period, page, page_size: 25 })}`,
      { signal },
    ), accountId),
    enabled: Boolean(accountId), retry, staleTime: 0,
  });
}

export function useExportStatement() {
  return useMutation({
    mutationFn: ({ accountId, date_from, date_to }) => downloadPortalFile(
      `statements/${accountId}/${toSearchParams({ date_from, date_to, export: "csv" })}`,
      `dwella-statement-${date_from}-${date_to}.csv`,
    ),
  });
}
