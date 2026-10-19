const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1";
const AUTH_TOKEN_KEY = "dwella_access_token";

export function getApiBaseUrl() {
  return API_BASE_URL.replace(/\/$/, "");
}

// The API serializes media as an absolute URL only when a request is in
// serializer context; otherwise it returns a bare path that would resolve
// against the frontend origin. Normalise both forms.
export function resolveMediaUrl(value) {
  if (!value) return "";
  if (/^https?:\/\//i.test(value)) return value;
  return `${getApiBaseUrl().replace(/\/api\/v1$/, "")}${value.startsWith("/") ? value : `/${value}`}`;
}

export function getAuthToken() {
  return localStorage.getItem(AUTH_TOKEN_KEY);
}

export function setAuthToken(token) {
  if (token) {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
    return;
  }

  localStorage.removeItem(AUTH_TOKEN_KEY);
}

export async function apiRequest(path, options = {}) {
  const token = getAuthToken();
  const headers = new Headers(options.headers || {});

  if (!headers.has("Content-Type") && options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  if (token) {
    headers.set("Authorization", `Token ${token}`);
  }

  const response = await fetch(`${getApiBaseUrl()}/${path.replace(/^\//, "")}`, {
    ...options,
    headers,
  });

  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : await response.text();

  if (!response.ok) {
    const message =
      typeof payload === "object"
        ? payload.response_message || payload.detail || payload.message
        : payload;
    const error = new Error(message || "Request failed");
    // Field-level validation errors arrive in `response_data`; forms read them
    // from here to mark the offending field instead of only toasting.
    error.status = response.status;
    error.data = typeof payload === "object" ? payload.response_data : undefined;
    throw error;
  }

  if (payload && typeof payload === "object" && "response_data" in payload) {
    if (payload.pagination) {
      return {
        results: payload.response_data,
        pagination: payload.pagination,
      };
    }
    return payload.response_data;
  }

  return payload;
}

export const api = {
  get: (path, options) => apiRequest(path, { ...options, method: "GET" }),
  post: (path, body, options) =>
    apiRequest(path, {
      ...options,
      method: "POST",
      body: body instanceof FormData ? body : JSON.stringify(body),
    }),
  patch: (path, body, options) =>
    apiRequest(path, {
      ...options,
      method: "PATCH",
      body: body instanceof FormData ? body : JSON.stringify(body),
    }),
  delete: (path, options) => apiRequest(path, { ...options, method: "DELETE" }),
};
