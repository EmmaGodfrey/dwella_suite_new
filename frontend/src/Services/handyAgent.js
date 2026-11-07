import { api, getAuthToken } from "./apiClient";
import { queryClient } from "./queryClient";
import { isSensitiveAccessPath } from "../shared/documentPrivacy";

const SCRIPT_ID = "dwella-handy-agent-widget";
const SCRIPT_URL = "https://handyai.wazabanda.dev/widget/v1/agent.js";

let credentials = null;
let pending = null;
let generation = 0;
let controller = new AbortController();
let allowed = false;
let activeRevision = null;

async function getWidgetToken() {
  if (isSensitiveAccessPath(window.location.pathname, import.meta.env.VITE_BASE_PATH || "/")) return null;
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
  if (import.meta.env.VITE_HANDY_AGENT_ENABLED !== "true") return undefined;

  // The official widget expects the unwrapped short-lived token response.
  // Dwella's durable login token is only used by our own API client.
  window.HandyAgent = { ...window.HandyAgent, getToken: getWidgetToken };
  const onDataChanged = () => { if (getAuthToken()) queryClient.invalidateQueries(); };
  window.addEventListener("agent:data-changed", onDataChanged);

  const ensureScript = (config) => {
    const existing = document.getElementById(SCRIPT_ID);
    const script = existing || document.createElement("script");
    if (!existing) {
      script.id = SCRIPT_ID;
      script.src = SCRIPT_URL;
      script.defer = true;
    }
    // The provider reads this live DOMStringMap again when refresh() remounts.
    script.dataset.api = config.url;
    script.dataset.title = config.title;
    script.dataset.theme = "auto";
    script.dataset.suggestions = JSON.stringify(config.suggestions || []);
    if (!existing) document.body.appendChild(script);
  };
  let disposed = false;
  const updateAvailability = async () => {
    const current = generation;
    let next = false;
    let config;
    try {
      if (!isSensitiveAccessPath(window.location.pathname, import.meta.env.VITE_BASE_PATH || "/") && getAuthToken()) {
        config = await api.get("/accounts/handy-agent/config/");
        next = Boolean(config.enabled && config.url?.startsWith("https://"));
      }
    }
    catch { next = false; }
    if (disposed || current !== generation) return;
    const changed = next !== allowed;
    const connectionChanged = next && config.revision !== activeRevision;
    allowed = next;
    const root = document.getElementById("handy-agent");
    if (root) root.style.display = allowed ? "" : "none";
    if (allowed) {
      ensureScript(config);
      activeRevision = config.revision;
    }
    if (changed || connectionChanged) refreshWidget();
  };
  const onAuthChanged = () => {
    allowed = false;
    const root = document.getElementById("handy-agent");
    if (root) root.style.display = "none";
    refreshWidget();
    updateAvailability();
  };
  window.addEventListener("dwella:auth-changed", onAuthChanged);
  window.addEventListener("dwella:route-changed", onAuthChanged);
  window.addEventListener("dwella:assistant-settings-changed", updateAvailability);
  window.addEventListener("focus", updateAvailability);
  const timer = window.setInterval(updateAvailability, 30_000);
  updateAvailability();

  return () => {
    disposed = true;
    window.clearInterval(timer);
    window.removeEventListener("dwella:auth-changed", onAuthChanged);
    window.removeEventListener("dwella:route-changed", onAuthChanged);
    window.removeEventListener("dwella:assistant-settings-changed", updateAvailability);
    window.removeEventListener("focus", updateAvailability);
    window.removeEventListener("agent:data-changed", onDataChanged);
  };
}
