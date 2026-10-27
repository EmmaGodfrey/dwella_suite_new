import { useQuery } from "@tanstack/react-query";
import { api } from "./apiClient";

export function usePublicConfiguration(options = {}) {
  return useQuery({
    queryKey: ["public-configuration"],
    queryFn: ({ signal }) => api.get("/marketing/configuration/", { signal }),
    staleTime: 60_000,
    refetchInterval: 60_000,
    retry: false,
    ...options,
  });
}

export function formatBetaDate(value) {
  if (!value) return "soon";
  return new Date(`${value}T00:00:00+02:00`).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "Africa/Lusaka",
  });
}
