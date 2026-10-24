// Presentation hints only. Backend roles, capability checks and limits remain authoritative.
export function canUseFeature(snapshot, feature, now = Date.now()) {
  const value = snapshot?.features?.[feature];
  if (value?.enabled !== true) return false;
  if (value.expires_at == null) return true;
  const expiry = Date.parse(value.expires_at);
  return Number.isFinite(expiry) && expiry > now;
}

export function canAddRecords(snapshot, resource, additional = 1) {
  const value = snapshot?.limits?.[resource];
  if (!value || !Number.isInteger(additional) || additional < 0) return false;
  if (!Number.isInteger(value.used) || value.used < 0) return false;
  if (value.limit === null) return true;
  return Number.isInteger(value.limit) && value.limit >= 0 && value.used + additional <= value.limit;
}
