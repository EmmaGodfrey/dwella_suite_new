const basePath = import.meta.env?.VITE_BASE_PATH || "/";
const deploymentScope = basePath.replace(/^\/+|\/+$/g, "");

export function scopedStorageKey(key) {
  return deploymentScope ? `${key}:${deploymentScope}` : key;
}

// Raw hrefs (new tab, middle-click, copy link) bypass the router's basename,
// so a staging "/dashboard" would otherwise open production.
export function appHref(to) {
  return `${basePath.replace(/\/+$/, "")}${to}`;
}

export const USER_STORAGE_KEY = scopedStorageKey("dwella_user");
export const AUTHENTICATED_STORAGE_KEY = scopedStorageKey("authenticated");
