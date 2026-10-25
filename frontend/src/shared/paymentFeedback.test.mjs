import assert from "node:assert/strict";
import { test } from "node:test";
import { paymentFeedback } from "./paymentFeedback.mjs";

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
