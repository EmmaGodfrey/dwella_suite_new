import assert from "node:assert/strict";
import test from "node:test";
import { isPublicSigningPath } from "./documentPrivacy.js";

test("public signing is isolated at root and staging base paths", () => {
  assert.equal(isPublicSigningPath("/sign/private-link"), true);
  assert.equal(isPublicSigningPath("/test/sign/private-link", "/test/"), true);
  assert.equal(isPublicSigningPath("/test/sign/private-link", "/test"), true);
  assert.equal(isPublicSigningPath("/leases/sign"), false);
  assert.equal(isPublicSigningPath("/signature/preview"), false);
  assert.equal(isPublicSigningPath("/sign/private-link", "/test/"), false);
});
