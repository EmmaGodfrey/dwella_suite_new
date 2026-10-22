import test from "node:test";
import assert from "node:assert/strict";
import { getSupportRequestContext, getSupportWorkspace, isCurrentSupportContext,
  setSupportWorkspace, expireSupportContext } from "./supportContext.js";

const storage = new Map();
globalThis.sessionStorage = {
  getItem: (key) => storage.get(key) || null,
  setItem: (key, value) => storage.set(key, value),
  removeItem: (key) => storage.delete(key),
};
globalThis.window = new EventTarget();

test("workspace transitions abort previous requests and reject stale generations", () => {
  setSupportWorkspace("workspace-a");
  const previous = getSupportRequestContext();
  assert.equal(previous.workspace, "workspace-a");
  setSupportWorkspace("workspace-b");
  assert.equal(previous.signal.aborted, true);
  assert.equal(isCurrentSupportContext(previous.generation), false);
  const current = getSupportRequestContext();
  assert.equal(current.workspace, "workspace-b");
  assert.equal(current.signal.aborted, false);
  setSupportWorkspace(null);
  assert.equal(current.signal.aborted, true);
  assert.equal(getSupportWorkspace(), null);
});

test("expiry clears context and emits recovery once", () => {
  let calls = 0;
  window.addEventListener("dwella:support-expired", () => { calls += 1; });
  setSupportWorkspace("workspace-a");
  expireSupportContext();
  expireSupportContext();
  assert.equal(calls, 1);
  assert.equal(getSupportWorkspace(), null);
});
