export function isPublicSigningPath(pathname, basePath = "/") {
  const base = basePath.replace(/\/+$/, "");
  return pathname.startsWith(`${base}/sign/`);
}

export function isSensitiveAccessPath(pathname, basePath = "/") {
  const base = basePath.replace(/\/+$/, "");
  return isPublicSigningPath(pathname, basePath) || ["/verify-email", "/accept-invitation", "/login", "/register"].some((path) => pathname === `${base}${path}`);
}
