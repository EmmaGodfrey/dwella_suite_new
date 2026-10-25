const scripts = new Set([
  "https://pay.lenco.co/js/v1/inline.js",
  "https://pay.sandbox.lenco.co/js/v1/inline.js",
]);
let loadedUrl;
let loading;

export function validateCheckout(config) {
  if (!config || !scripts.has(config.script_url)) throw new Error("Unrecognised payment provider.");
  if (!/^[A-Za-z0-9._-]{1,50}$/.test(config.reference || "")) throw new Error("Invalid payment reference.");
  if (!/^\d{1,10}\.\d{2}$/.test(config.amount) || Number(config.amount) <= 0) throw new Error("Invalid payment amount.");
  if (config.currency !== "ZMW" || !config.email || !config.key) throw new Error("Payment details are incomplete.");
  return { key: config.key, reference: config.reference, email: config.email,
    amount: Number(config.amount), currency: config.currency, bearer: "merchant",
    channels: ["mobile-money", "card"] };
}

function loadScript(url) {
  if (!scripts.has(url)) return Promise.reject(new Error("Unrecognised payment provider."));
  if (loadedUrl && loadedUrl !== url) return Promise.reject(new Error("Reload this page before opening checkout again."));
  if (loading) return loading;
  loadedUrl = url;
  loading = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = url;
    script.async = true;
    const timeout = setTimeout(() => fail(), 20_000);
    const fail = () => {
      clearTimeout(timeout);
      script.remove();
      loadedUrl = undefined;
      loading = undefined;
      reject(new Error("Could not open Lenco. Check your connection and try again."));
    };
    script.onerror = fail;
    script.onload = () => {
      clearTimeout(timeout);
      if (typeof window.LencoPay?.getPaid !== "function") return fail();
      resolve();
    };
    document.head.appendChild(script);
  });
  return loading;
}

export async function openLencoCheckout(config, onReturn, signal) {
  const details = validateCheckout(config);
  await loadScript(config.script_url);
  if (signal?.aborted) throw new DOMException("Checkout closed", "AbortError");
  // Every callback merely asks our backend to verify the saved reference.
  // Callback amounts/status/references never modify Dwella's ledger.
  let returned = false;
  const verify = (event) => { if (!returned) { returned = true; onReturn(event); } };
  window.LencoPay.getPaid({ ...details,
    onSuccess: () => verify("success"),
    onConfirmationPending: () => verify("pending"),
    onClose: () => verify("close"),
  });
}
