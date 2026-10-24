import assert from "node:assert/strict";
import test from "node:test";
import { isPublicSigningPath, isSensitiveAccessPath } from "./documentPrivacy.js";

test("public signing is isolated at root and staging base paths", () => {
  assert.equal(isPublicSigningPath("/sign/private-link"), true);
  assert.equal(isPublicSigningPath("/test/sign/private-link", "/test/"), true);
  assert.equal(isPublicSigningPath("/test/sign/private-link", "/test"), true);
  assert.equal(isPublicSigningPath("/leases/sign"), false);
  assert.equal(isPublicSigningPath("/signature/preview"), false);
  assert.equal(isPublicSigningPath("/sign/private-link", "/test/"), false);
});

test("account links and recovery screens exclude assistant access at each deployment base", () => {
  for (const path of ["/verify-email", "/accept-invitation", "/login", "/register"]) {
    assert.equal(isSensitiveAccessPath(path), true);
    assert.equal(isSensitiveAccessPath(`/test${path}`, "/test/"), true);
    assert.equal(isSensitiveAccessPath(path, "/test/"), false);
  }
  assert.equal(isSensitiveAccessPath("/security"), false);
  assert.equal(isSensitiveAccessPath("/leases"), false);
});
