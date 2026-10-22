import { api } from "./apiClient";
import { queryKeys } from "./queryKeys";
import { getSupportWorkspace, setSupportWorkspace } from "./supportContext";

export async function refreshSupportContext(cache, workspace) {
  await cache.cancelQueries();
  setSupportWorkspace(workspace);
  cache.clear();
  const user = await api.get("/accounts/me/");
  cache.setQueryData(queryKeys.currentUser, user);
  localStorage.setItem("dwella_user", JSON.stringify(user));
  return user;
}

export async function enterSupportWorkspace(cache, workspace, reason) {
  if (cache.isMutating()) throw new Error("Wait for the current change to finish before switching workspaces.");
  const previous = cache.getQueryData(queryKeys.currentUser)?.access?.acting_workspace;
  if (previous) {
    await api.post(`/platform/support-sessions/${previous.session_id}/end/`, {});
    await refreshSupportContext(cache, null);
  }
  const session = await api.post("/platform/support-sessions/", { organization: workspace, reason: reason.trim() });
  await refreshSupportContext(cache, workspace);
  return session;
}

export async function leaveSupportWorkspace(cache, session) {
  if (cache.isMutating()) throw new Error("Wait for the current change to finish before leaving the workspace.");
  if (session) await api.post(`/platform/support-sessions/${session}/end/`, {});
  if (getSupportWorkspace()) await refreshSupportContext(cache, null);
}
