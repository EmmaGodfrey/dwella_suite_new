import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, getApiBaseUrl } from "./apiClient";

const root = "/documents/versions/";
export const managementDocuments = {
  get: (id, operation, params = "") => api.get(`${root}${id}/${operation === "document" ? "" : `${operation}/`}${params}`, {
    ...(["pdf", "page"].includes(operation) ? { responseType: "blob" } : {}),
  }),
  post: (id, operation, payload) => api.post(
    operation === "source-preview" ? `${root}source-preview/` : `${root}${id}/${operation}/`, payload,
  ),
};

// No account token, cookies, support context or persistent browser storage on public links.
export function signingDocuments(token, session = "") {
  async function request(operation, { body, method = "GET", params = "" } = {}) {
    const headers = new Headers();
    if (session) headers.set("X-Dwella-Signing-Session", session);
    if (body && !(body instanceof FormData)) headers.set("Content-Type", "application/json");
    const response = await fetch(`${getApiBaseUrl()}/signing/${encodeURIComponent(token)}/${operation}/${params}`, {
      method, headers, body: body instanceof FormData ? body : body ? JSON.stringify(body) : undefined,
      credentials: "omit", cache: "no-store", referrerPolicy: "no-referrer",
    });
    if (response.ok && ["pdf", "page"].includes(operation)) return response.blob();
    const payload = await response.json();
    if (!response.ok) {
      const error = new Error(payload.response_message || "This signing request is unavailable.");
      error.status = response.status;
      error.data = payload.response_data;
      throw error;
    }
    return payload.response_data;
  }
  return {
    get: (_, operation, params) => request(operation, { params }),
    post: (_, operation, body) => request(operation, { method: "POST", body }),
  };
}

export function useLeaseDocuments(lease) {
  return useQuery({ queryKey: ["documents", "leases", lease], enabled: Boolean(lease),
    queryFn: () => api.get(`${root}?lease=${lease}&page_size=100`), staleTime: 0 });
}
export function useOriginalDocuments(lease) {
  return useQuery({ queryKey: ["documents", "originals", lease], enabled: Boolean(lease),
    queryFn: () => api.get(`/documents/originals/?lease=${lease}&page_size=100`) });
}
export function useDocumentSigners() {
  return useQuery({ queryKey: ["documents", "signers"], queryFn: () => api.get(`${root}signers/`) });
}
export function usePrepareDocument(options = {}) {
  const cache = useQueryClient();
  return useMutation({ mutationFn: (body) => api.post(root, body),
    onSuccess: (data) => { cache.invalidateQueries({ queryKey: ["documents"] }); options.onSuccess?.(data); },
    onError: options.onError });
}
export function useAttachOriginal(options = {}) {
  const cache = useQueryClient();
  return useMutation({ mutationFn: (body) => api.post("/documents/originals/", body),
    onSuccess: (data) => { cache.invalidateQueries({ queryKey: ["documents"] }); options.onSuccess?.(data); },
    onError: options.onError });
}
export function useInvoiceDocument(options = {}) {
  return useMutation({ mutationFn: (id) => api.post(`/billing/invoices/${id}/document/`, {}), ...options });
}
export function useDocumentAction(client, id, operation, options = {}) {
  const cache = useQueryClient();
  return useMutation({ mutationFn: (body) => client.post(id, operation, body),
    onSuccess: (data) => { cache.invalidateQueries({ queryKey: ["documents"] }); options.onSuccess?.(data); },
    onError: options.onError });
}
export function useSigningDocument(client, session, token) {
  return useQuery({ queryKey: ["signing-document", token, session], enabled: Boolean(session),
    queryFn: () => client.get(null, "document"), retry: false, gcTime: 0, staleTime: 0 });
}
export function useDocumentPage(client, doc, page, accessKey) {
  return useQuery({ queryKey: ["document-page", doc.id, doc.sha256, page, accessKey], gcTime: 0,
    queryFn: () => client.get(doc.id, "page", `?page=${page}&sha256=${doc.sha256}`), retry: false });
}
export function useDocumentDownload(client, doc, options = {}) {
  return useMutation({ mutationFn: async () => {
    const blob = await client.get(doc.id, "pdf");
    saveBlob(blob, `${doc.snapshot.reference}-v${doc.version}.pdf`);
  }, ...options });
}
export function useOriginalDownload(options = {}) {
  return useMutation({ mutationFn: async (id) => {
    const blob = await api.get(`/documents/originals/${id}/pdf/`, { responseType: "blob" });
    saveBlob(blob, "signed-lease-original.pdf");
  }, ...options });
}
function saveBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url; anchor.download = filename; anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export function documentError(error) {
  const data = error?.data;
  const details = data && typeof data === "object" ? Object.values(data).flat().filter(v => typeof v === "string").join(" ") : "";
  return details || error?.message || "Could not complete this request. Please try again.";
}
