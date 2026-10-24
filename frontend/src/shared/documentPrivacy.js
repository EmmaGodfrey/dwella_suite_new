export function isPublicSigningPath(pathname, basePath = "/") {
  const base = basePath.replace(/\/+$/, "");
  return pathname.startsWith(`${base}/sign/`);
}
