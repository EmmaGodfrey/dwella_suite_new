import assert from "node:assert/strict";
import { test } from "node:test";
import { paymentFeedback } from "./paymentFeedback.mjs";

test("native phone authorization remains pending until verified receipt", () => {
  const collection = { channel: "mobile-money", status: "pending", provider_status: "pay-offline" };
  for (const delayed of [false, true]) {
    const feedback = paymentFeedback({ stage: "idle", collection, delayed });
    assert.equal(feedback.title, "Approve payment on your phone");
    assert.equal(feedback.kind, "waiting");
  }
  assert.equal(paymentFeedback({ stage: "error", collection }).kind, "waiting");
});

test("provider return and elapsed time cannot create a success state", () => {
  for (const returnedKind of ["success", "pending", "close"]) {
    for (const delayed of [false, true]) {
      const state = paymentFeedback({ stage: "checking", returnedKind, delayed,
        collection: { status: "pending" } });
      assert.equal(state.kind, "waiting");
      assert.equal(state.working, true);
    }
  }
  assert.notEqual(paymentFeedback({ stage: "checking", collection: { status: "successful" } }).kind, "confirmed");
});

test("confirmed server receipt wins over a waiting state", () => {
  assert.equal(paymentFeedback({ stage: "checking", delayed: true,
    collection: { status: "successful", payment_id: "server-receipt" } }).kind, "confirmed");
  assert.equal(paymentFeedback({ stage: "provider",
    collection: { status: "successful", payment_id: "server-receipt" } }).kind, "confirmed");
});

test("terminal server outcomes stop the waiting indicator", () => {
  for (const status of ["failed", "review", "expired"]) {
    const state = paymentFeedback({ stage: "checking", collection: { status } });
    assert.equal(state.kind, status);
    assert.notEqual(state.working, true);
  }
});

test("new checkout does not show a previous partial payment as its result", () => {
  assert.equal(paymentFeedback({ stage: "opening", collection: {
    status: "successful", payment_id: "earlier-receipt"
  } }).kind, "opening");
});

test("a fresh open payment refreshes every two seconds, then backs off", async () => {
  const { checkoutRefresh } = await import("./paymentFeedback.mjs");
  const now = Date.parse("2026-11-15T18:10:00Z");
  const row = (status, minutesAgo) => ({ status, created_at: new Date(now - minutesAgo * 60_000).toISOString() });
  assert.equal(checkoutRefresh([row("pending", 0.5)], now), 2_000);
  assert.equal(checkoutRefresh([row("pending", 5)], now), 5_000);
  assert.equal(checkoutRefresh([row("pending", 20)], now), 15_000);
  // The newest open payment sets the pace.
  assert.equal(checkoutRefresh([row("pending", 20), row("pending", 1)], now), 2_000);
  // Nothing open: no refresh at all.
  assert.equal(checkoutRefresh([row("successful", 0.5), row("failed", 1)], now), false);
  assert.equal(checkoutRefresh(undefined, now), false);
});
