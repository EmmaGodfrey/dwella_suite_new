import { scopedStorageKey } from "../shared/storage.js";

const KEY = scopedStorageKey("dwella_support_workspace");
let controller = new AbortController();
let generation = 0;

export const getSupportWorkspace = () => sessionStorage.getItem(KEY);
export const getSupportRequestContext = () => ({
  workspace: getSupportWorkspace(), signal: controller.signal, generation,
});
export const isCurrentSupportContext = (value) => value === generation;

export function setSupportWorkspace(workspace) {
  controller.abort();
  controller = new AbortController();
  generation += 1;
  if (workspace) sessionStorage.setItem(KEY, workspace);
  else sessionStorage.removeItem(KEY);
}

export function expireSupportContext() {
  if (!getSupportWorkspace()) return;
  setSupportWorkspace(null);
  window.dispatchEvent(new Event("dwella:support-expired"));
}
