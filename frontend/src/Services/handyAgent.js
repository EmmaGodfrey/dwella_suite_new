import { api, getAuthToken } from "./apiClient";
import { queryClient } from "./queryClient";

const SCRIPT_ID = "dwella-handy-agent-widget";
const SCRIPT_URL = "https://handyai.wazabanda.dev/widget/v1/agent.js";
const AGENT_URL = "https://dwella.handyagents.wazabanda.dev/agent";
const SUGGESTIONS = [
  "Which tenants are overdue on rent this month?",
  "How many units are vacant right now?",
  "Which leases end in the next 60 days?",
  "How much rent did I collect last month?",
  "Show open maintenance requests for my properties",
];

let credentials = null;
let pending = null;
let generation = 0;
let controller = new AbortController();

async function getWidgetToken() {
  if (!getAuthToken()) return null;
  if (credentials && Date.parse(credentials.expires_at) - Date.now() > 60_000) return credentials;
  if (pending) return pending;

  const current = generation;
  const request = api.post("/accounts/handy-agent/token/", {}, { signal: controller.signal })
    .then((value) => {
      if (current !== generation || !getAuthToken()) return null;
      credentials = value;
      return value;
    })
    .catch(() => null)
    .finally(() => { if (current === generation) pending = null; });
  pending = request;
  return request;
}

function refreshWidget() {
  generation += 1;
  controller.abort();
  controller = new AbortController();
  credentials = null;
  pending = null;
  window.HandyAgent?.refresh?.();
}

export function installHandyAgent() {
  if (import.meta.env.VITE_HANDY_AGENT_ENABLED !== "true") return undefined;

  // The official widget expects the unwrapped short-lived token response.
  // Dwella's durable login token is only used by our own API client.
  window.HandyAgent = { ...window.HandyAgent, getToken: getWidgetToken };
  const onDataChanged = () => { if (getAuthToken()) queryClient.invalidateQueries(); };
  window.addEventListener("dwella:auth-changed", refreshWidget);
  window.addEventListener("agent:data-changed", onDataChanged);

  if (!document.getElementById(SCRIPT_ID)) {
    const script = document.createElement("script");
    script.id = SCRIPT_ID;
    script.src = SCRIPT_URL;
    script.defer = true;
    script.dataset.api = AGENT_URL;
    script.dataset.title = "Dwella assistant";
    script.dataset.theme = "auto";
    script.dataset.suggestions = JSON.stringify(SUGGESTIONS);
    document.body.appendChild(script);
  } else {
    refreshWidget();
  }

  return () => {
    window.removeEventListener("dwella:auth-changed", refreshWidget);
    window.removeEventListener("agent:data-changed", onDataChanged);
  };
}
