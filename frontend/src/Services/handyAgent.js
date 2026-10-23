import { api, getAuthToken } from "./apiClient";

const AGENT_URL = "https://dwella.handyagents.wazabanda.dev/agent";
const TOKEN_REFRESH_BUFFER_MS = 60_000;

let credentials = null;
let credentialsRequest = null;
let generation = 0;
let controller = new AbortController();

export const HANDY_AGENT_SUGGESTIONS = [
  "Which tenants are overdue on rent this month?",
  "How many units are vacant right now?",
  "Which leases end in the next 60 days?",
  "How much rent did I collect last month?",
  "Show open maintenance requests for my properties",
];

export function isHandyAgentEnabled() {
  return import.meta.env.VITE_HANDY_AGENT_ENABLED === "true";
}

export function resetHandyAgentCredentials() {
  generation += 1;
  controller.abort();
  controller = new AbortController();
  credentials = null;
  credentialsRequest = null;
}

function credentialsAreFresh(value) {
  if (!value?.token) return false;
  const expiresAt = new Date(value.expires_at).getTime();
  return Number.isFinite(expiresAt) && expiresAt - Date.now() > TOKEN_REFRESH_BUFFER_MS;
}

async function getCredentials() {
  if (!getAuthToken()) throw new Error("Sign in to use the Dwella assistant.");
  if (credentialsAreFresh(credentials)) return credentials;
  if (credentialsRequest) return credentialsRequest;

  const currentGeneration = generation;
  credentialsRequest = api.post("/accounts/handy-agent/token/", {}, { signal: controller.signal })
    .then((value) => {
      if (generation !== currentGeneration) throw new DOMException("Account changed", "AbortError");
      credentials = value;
      return value;
    })
    .finally(() => {
      if (generation === currentGeneration) credentialsRequest = null;
    });
  return credentialsRequest;
}

async function agentFetch(path, options = {}, retry = true) {
  const auth = await getCredentials();
  const headers = new Headers(options.headers || {});
  headers.set("Authorization", `Bearer ${auth.token}`);
  headers.set("X-Host-Authorization", auth.host_authorization || `Bearer ${auth.token}`);
  if (options.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");

  const response = await fetch(`${AGENT_URL}/${path.replace(/^\//, "")}`, {
    ...options,
    signal: controller.signal,
    headers,
  });

  if (response.status === 401 && retry) {
    resetHandyAgentCredentials();
    return agentFetch(path, options, false);
  }
  return response;
}

async function responseError(response) {
  const payload = await response.json().catch(() => ({}));
  return new Error(payload.detail || payload.message || `Assistant request failed (${response.status}).`);
}

export async function getHandyAgentIdentity() {
  const response = await agentFetch("/me/");
  if (!response.ok) throw await responseError(response);
  return response.json();
}

export async function listHandyAgentSessions() {
  const response = await agentFetch("/sessions/");
  if (!response.ok) throw await responseError(response);
  const payload = await response.json();
  return payload.sessions || [];
}

export async function getHandyAgentSession(id) {
  const response = await agentFetch(`/sessions/${encodeURIComponent(id)}/`);
  if (!response.ok) throw await responseError(response);
  return response.json();
}

export async function streamHandyAgent(path, payload, onEvent) {
  const response = await agentFetch(path, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw await responseError(response);

  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("text/event-stream") || !response.body) {
    return response.json().catch(() => null);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  const emit = (chunk) => {
    const data = chunk
      .split(/\r?\n/)
      .filter((line) => line.startsWith("data:"))
      .map((line) => line.slice(5).trimStart())
      .join("\n");
    if (!data) return;
    try {
      onEvent(JSON.parse(data));
    } catch {
      onEvent({ type: "error", message: "The assistant returned an unreadable response." });
    }
  };

  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    const chunks = buffer.split(/\r?\n\r?\n/);
    buffer = chunks.pop() || "";
    chunks.forEach(emit);
    if (done) break;
  }
  if (buffer.trim()) emit(buffer);
  return null;
}

export function chatWithHandyAgent(payload, onEvent) {
  return streamHandyAgent("/chat/", payload, onEvent);
}

export function approveHandyAgentAction(payload, onEvent) {
  return streamHandyAgent("/approve/", payload, onEvent);
}
