// UI feedback only. A provider callback is never evidence of a paid invoice.
export function paymentFeedback({ stage, collection, delayed = false, returnedKind, channel }) {
  if (stage === "opening") return { kind: "opening", working: true,
    title: channel === "mobile-money" ? "Requesting mobile-money payment" : "Opening secure checkout",
    message: channel === "mobile-money" ? "Sending your payment request. Please don’t submit it again." : "Getting your payment ready in Lenco…" };
  if (collection?.status === "successful" && collection.payment_id) return { kind: "confirmed",
    title: "Payment confirmed", message: "Your payment has been recorded. Your balance and receipt are up to date." };
  if (collection?.status === "review") return { kind: "review",
    title: "Your payment needs a check", message: "Contact your property manager before paying again. Keep your payment reference." };
  if (collection?.status === "failed") return { kind: "failed",
    title: "Payment was not completed", message: "Lenco reported that this payment failed. You can try again." };
  if (collection?.status === "expired") return { kind: "expired",
    title: "Checkout was not completed", message: "No payment was confirmed for this checkout. You can start a new payment." };
  if (stage === "provider") return { kind: "provider", working: true,
    title: "Complete payment in Lenco", message: "Return here after checkout to see your confirmation and receipt." };
  if (collection?.status === "pending" && collection.channel === "mobile-money") return { kind: "waiting", working: true,
    title: collection.provider_status === "pay-offline" ? "Approve payment on your phone" : "Confirming mobile-money payment",
    message: delayed
      ? "Still awaiting confirmation. If your phone shows a payment prompt, approve it there. Please don’t start another payment."
      : "Authorize the payment on your mobile-money phone. Your balance and receipt update after confirmation. Never share your PIN here." };
  if (stage === "error") return null;
  if (stage === "checking" || collection?.status === "pending") return { kind: "waiting", working: true,
    title: delayed ? "Still waiting for Lenco" : "Confirming payment with Lenco",
    message: returnedKind === "close"
      ? "We’re checking whether a payment was completed. If you closed Lenco before paying, you can resume the same checkout below."
      : delayed
        ? "Confirmation is taking a little longer. Please don’t pay again—we’ll keep checking and update your receipt here."
        : "Waiting for Lenco’s confirmation. Your balance and receipt will update once your payment is verified." };
  return null;
}
