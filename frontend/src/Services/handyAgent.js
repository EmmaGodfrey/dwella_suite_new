import { api, getAuthToken } from "./apiClient";
import { queryClient } from "./queryClient";
import { isPublicSigningPath } from "../shared/documentPrivacy";

const SCRIPT_ID = "dwella-handy-agent-widget";
const SCRIPT_URL = "https://handyai.wazabanda.dev/widget/v1/agent.js";
const AGENT_URL = (import.meta.env.VITE_HANDY_AGENT_URL || "").replace(/\/+$/, "");
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
let allowed = false;

async function getWidgetToken() {
  if (!allowed || !getAuthToken()) return null;
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
  if (isPublicSigningPath(window.location.pathname, import.meta.env.VITE_BASE_PATH || "/")) return undefined;
  if (import.meta.env.VITE_HANDY_AGENT_ENABLED !== "true") return undefined;
  if (!AGENT_URL) {
    console.warn("Handy widget is enabled but VITE_HANDY_AGENT_URL is missing.");
    return undefined;
  }

  // The official widget expects the unwrapped short-lived token response.
  // Dwella's durable login token is only used by our own API client.
  window.HandyAgent = { ...window.HandyAgent, getToken: getWidgetToken };
  const onDataChanged = () => { if (getAuthToken()) queryClient.invalidateQueries(); };
  window.addEventListener("agent:data-changed", onDataChanged);

  const ensureScript = () => {
    if (document.getElementById(SCRIPT_ID)) return;
    const script = document.createElement("script");
    script.id = SCRIPT_ID;
    script.src = SCRIPT_URL;
    script.defer = true;
    script.dataset.api = AGENT_URL;
    script.dataset.title = "Dwella assistant";
    script.dataset.theme = "auto";
    script.dataset.suggestions = JSON.stringify(SUGGESTIONS);
    document.body.appendChild(script);
  };
  let disposed = false;
  const updateAvailability = async () => {
    const current = generation;
    let next = false;
    try { next = Boolean(getAuthToken() && (await api.get("/accounts/handy-agent/config/")).enabled); }
    catch { next = false; }
    if (disposed || current !== generation) return;
    const changed = next !== allowed;
    allowed = next;
    const root = document.getElementById("handy-agent");
    if (root) root.style.display = allowed ? "" : "none";
    if (allowed) ensureScript();
    if (changed) refreshWidget();
  };
  const onAuthChanged = () => {
    allowed = false;
    const root = document.getElementById("handy-agent");
    if (root) root.style.display = "none";
    refreshWidget();
    updateAvailability();
  };
  window.addEventListener("dwella:auth-changed", onAuthChanged);
  window.addEventListener("dwella:assistant-settings-changed", updateAvailability);
  window.addEventListener("focus", updateAvailability);
  const timer = window.setInterval(updateAvailability, 30_000);
  updateAvailability();

  return () => {
    disposed = true;
    window.clearInterval(timer);
    window.removeEventListener("dwella:auth-changed", onAuthChanged);
    window.removeEventListener("dwella:assistant-settings-changed", updateAvailability);
    window.removeEventListener("focus", updateAvailability);
    window.removeEventListener("agent:data-changed", onDataChanged);
  };
}
