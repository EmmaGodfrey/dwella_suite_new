import { api, getAuthToken } from "./apiClient";

const SCRIPT_ID = "dwella-handy-agent-widget";
const SCRIPT_URL = "https://handyai.wazabanda.dev/widgets/v1/agent.js";
const AGENT_URL = "https://dwella.handyagents.wazabanda.dev/agent";
const SUGGESTIONS = [
  "Which tenants are overdue on rent this month?",
  "How many units are vacant right now?",
  "Which leases end in the next 60 days?",
  "How much rent did I collect last month?",
  "Show open maintenance requests for my properties",
];

export function refreshHandyAgent() {
  window.HandyAgent?.refresh?.();
}

export function installHandyAgent() {
  if (import.meta.env.VITE_HANDY_AGENT_ENABLED !== "true") return;

  window.HandyAgent = {
    ...window.HandyAgent,
    getToken: async () => {
      if (!getAuthToken()) return null;

      try {
        return await api.post("/accounts/handy-agent/token/", {});
      } catch {
        return null;
      }
    },
  };

  if (document.getElementById(SCRIPT_ID)) {
    refreshHandyAgent();
    return;
  }

  const script = document.createElement("script");
  script.id = SCRIPT_ID;
  script.src = SCRIPT_URL;
  script.defer = true;
  script.dataset.api = AGENT_URL;
  script.dataset.title = "Dwella assistant";
  script.dataset.suggestions = JSON.stringify(SUGGESTIONS);
  document.body.appendChild(script);
}
