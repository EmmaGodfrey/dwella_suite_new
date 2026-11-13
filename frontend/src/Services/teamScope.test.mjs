import test from "node:test";
import assert from "node:assert/strict";
import { QueryClient } from "@tanstack/react-query";
import { resetPropertyScope, scopeSignature } from "./teamScope.mjs";

const member = (id, properties, extra = {}) => ({ id, role: "manager", properties: properties.map((item) => ({ id: item })), ...extra });
const team = (extra = {}) => ({
  allow_teammate_cover: true,
  members: [member("me", ["alpha"], { is_you: true }), member("ben", ["beta"])],
  covers: [],
  ...extra,
});

test("resetting the scope empties cached records, even ones no screen is showing", async () => {
  const client = new QueryClient();
  client.setQueryData(["properties", "detail", "covered"], { name: "Covered property" });
  client.setQueryData(["documents", "version", "1"], { pdf: "private" });
  client.setQueryData(["organizations", "team"], { members: [] });
  await client.invalidateQueries();
  assert.ok(client.getQueryData(["properties", "detail", "covered"]), "invalidation alone keeps the old record");
  await resetPropertyScope(client);
  assert.equal(client.getQueryData(["properties", "detail", "covered"]), undefined);
  assert.equal(client.getQueryData(["documents", "version", "1"]), undefined);
  assert.deepEqual(client.getQueryData(["organizations", "team"]), { members: [] });
});

test("a refused refresh after the reset shows nothing from the old scope", async () => {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const key = ["leases", "detail", "covered"];
  let allowed = true;
  const queryFn = async () => { if (!allowed) throw new Error("403"); return { tenant: "Bob Beta" }; };
  await client.fetchQuery({ queryKey: key, queryFn });
  allowed = false;
  await resetPropertyScope(client);
  await assert.rejects(client.fetchQuery({ queryKey: key, queryFn }));
  assert.equal(client.getQueryData(key), undefined);
});

test("the scope signature changes with assignments, covers, the teammate's properties and role", () => {
  const base = scopeSignature(team());
  assert.equal(scopeSignature(team()), base);
  assert.notEqual(scopeSignature(team({ members: [member("me", [], { is_you: true }), member("ben", ["beta"])] })), base);
  const covering = team({ covers: [{ id: "c1", manager: { id: "me" }, covering_for: { id: "ben" } }] });
  assert.notEqual(scopeSignature(covering), base);
  const shrunk = { ...covering, members: [covering.members[0], member("ben", [])] };
  assert.notEqual(scopeSignature(shrunk), scopeSignature(covering));
  // Cover switched off for the workspace: the open cover no longer counts.
  assert.equal(scopeSignature({ ...covering, allow_teammate_cover: false }), base);
  assert.notEqual(scopeSignature(team({ members: [member("me", ["alpha"], { is_you: true, role: "landlord" })] })), base);
  // Someone else's cover does not change mine.
  assert.equal(scopeSignature(team({ covers: [{ id: "c2", manager: { id: "ben" }, covering_for: { id: "me" } }] })), base);
  assert.equal(scopeSignature(undefined), "");
  assert.equal(scopeSignature({ members: [] }), "");
});
