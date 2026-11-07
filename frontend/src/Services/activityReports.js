import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "./apiClient";
import { toSearchParams } from "./queries";
import { activityReportData, activityReportFilters } from "../shared/activityReports.mjs";

const path = (report, filters, csv = false) => `/reports/${report}/${toSearchParams(activityReportFilters(report, filters, csv))}`;

export function useActivityReport(report, filters) {
  return useQuery({
    queryKey: ["reports", report, activityReportFilters(report, filters)],
    queryFn: async ({ signal }) => activityReportData(await api.get(path(report, filters), { signal }), report, filters.tenant),
    enabled: report !== "tenant-statement" || Boolean(filters.tenant),
    retry: (count, error) => (!error?.status || error.status >= 500) && count < 1,
    staleTime: 0,
  });
}

export function useExportActivityReport() {
  return useMutation({
    mutationFn: async ({ report, filters }) => {
      const blob = await api.get(path(report, filters, true), { responseType: "blob" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url; link.download = `dwella-${report}-${filters.date_from}-${filters.date_to}.csv`;
      document.body.appendChild(link); link.click(); link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    },
  });
}
