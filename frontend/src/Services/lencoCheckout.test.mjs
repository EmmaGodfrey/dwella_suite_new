import assert from "node:assert/strict";
import { test } from "node:test";
import { openLencoCheckout, validateCheckout } from "./lencoCheckout.mjs";

const config = { script_url: "https://pay.sandbox.lenco.co/js/v1/inline.js", key: "public-test-key",
  reference: "rent-test", amount: "100.00", currency: "ZMW", email: "test@example.com" };

test("checkout only forwards server payment details and the public key", () => {
  const details = validateCheckout({ ...config, secret: "must-not-forward", arbitrary: "extra" });
  assert.equal(details.amount, 100);
  assert.equal(details.secret, undefined);
  assert.equal(details.arbitrary, undefined);
  assert.deepEqual(details.channels, ["mobile-money", "card"]);
});

test("checkout refuses another script origin, invalid references and invalid money", () => {
  for (const replacement of [{ script_url: "https://attacker.test/inline.js" },
    { reference: "bad/ref" }, { amount: "-1.00" }, { amount: "NaN" }, { currency: "USD" }]) {
    assert.throws(() => validateCheckout({ ...config, ...replacement }));
  }
});

test("new card checkout cannot offer a mobile-money option", () => {
  assert.deepEqual(validateCheckout({ ...config, channels: ["card"] }).channels, ["card"]);
});

test("callbacks only trigger verification once and never trust callback payloads", async () => {
  let options;
  globalThis.window = { LencoPay: { getPaid: (value) => { options = value; } } };
  globalThis.document = { createElement: () => ({ remove() {} }), head: { appendChild: (script) => queueMicrotask(() => script.onload()) } };
  const returns = [];
  await openLencoCheckout(config, (event) => { returns.push(event); });
  options.onSuccess({ reference: "wrong", amount: "999", status: "successful" });
  options.onClose();
  assert.deepEqual(returns, ["success"]);
  assert.equal(options.reference, "rent-test");
  assert.equal(options.amount, 100);
});

test("closing a drawer while the provider loads prevents opening checkout", async () => {
  const controller = new AbortController();
  controller.abort();
  let opened = false;
  window.LencoPay.getPaid = () => { opened = true; };
  await assert.rejects(openLencoCheckout(config, () => {}, controller.signal), { name: "AbortError" });
  assert.equal(opened, false);
});
