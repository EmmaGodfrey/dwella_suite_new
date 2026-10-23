const basePath = import.meta.env?.VITE_BASE_PATH || "/";
const deploymentScope = basePath.replace(/^\/+|\/+$/g, "");

export function scopedStorageKey(key) {
  return deploymentScope ? `${key}:${deploymentScope}` : key;
}

export const USER_STORAGE_KEY = scopedStorageKey("dwella_user");
export const AUTHENTICATED_STORAGE_KEY = scopedStorageKey("authenticated");
