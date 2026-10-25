import assert from "node:assert/strict";
import test from "node:test";
import { optimisticTourStep } from "./tourState.js";

const tour = {
  status: "in_progress", current_step: "a", completed_steps: [], pending_steps: ["a", "b", "c"],
  steps: [{ id: "a" }, { id: "b" }, { id: "c" }],
};

test("next moves forward and records the step as completed", () => {
  const next = optimisticTourStep(tour, "next");
  assert.equal(next.current_step, "b");
  assert.deepEqual(next.completed_steps, ["a"]);
  assert.deepEqual(next.pending_steps, ["b", "c"]);
  assert.equal(optimisticTourStep(next, "next").current_step, "c");
});

test("back moves to the previous step and stops at the first", () => {
  assert.equal(optimisticTourStep({ ...tour, current_step: "b" }, "back").current_step, "a");
  assert.equal(optimisticTourStep(tour, "back").current_step, "a");
});

test("finishing, other actions and closed tours wait for the server", () => {
  assert.equal(optimisticTourStep({ ...tour, current_step: "c" }, "next"), null);
  assert.equal(optimisticTourStep(tour, "pause"), null);
  assert.equal(optimisticTourStep({ ...tour, status: "skipped" }, "next"), null);
  assert.equal(optimisticTourStep({ ...tour, current_step: "gone" }, "next"), null);
});
