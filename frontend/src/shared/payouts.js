export const networks = { mtn: "MTN Mobile Money", airtel: "Airtel Money", zamtel: "Zamtel Money" };

const shortNetworks = { mtn: "MTN MoMo", airtel: "Airtel Money", zamtel: "Zamtel Money" };

/** "Airtel Money · •••• 4567" or "Zanaco · •••• 9210". */
export function destinationShort(destination) {
  if (!destination) return "—";
  const provider = destination.kind === "bank-account"
    ? destination.bank_name
    : shortNetworks[destination.operator] || destination.operator;
  return `${provider} · •••• ${destination.account_suffix}`;
}

/** "Airtel Money · MUTALE BANDA · number ending 4567". */
export function destinationLong(destination) {
  if (!destination) return "";
  const bank = destination.kind === "bank-account";
  const provider = bank ? destination.bank_name : networks[destination.operator] || destination.operator;
  return `${provider} · ${destination.account_name} · ${bank ? "account" : "number"} ending ${destination.account_suffix}`;
}

export const withdrawalStatus = {
  queued: { label: "Queued", color: "warning" },
  submitting: { label: "Sending", color: "warning" },
  pending: { label: "Processing", color: "warning" },
  successful: { label: "Delivered", color: "success" },
  failed: { label: "Failed · returned to balance", color: "danger" },
  review: { label: "Needs attention", color: "danger" },
  cancelled: { label: "Cancelled", color: "subtle" },
};

/** The fee column: the reserve while sending, what was charged once delivered. */
export function withdrawalFee(row, formatMoney) {
  if (row.status === "successful") return formatMoney(row.fee_charged);
  if (["queued", "submitting", "pending", "review"].includes(row.status)) return `${formatMoney(row.fee_reserved)} held`;
  return "—";
}

export const weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

const ordinal = (day) => {
  const tens = day % 100;
  const suffix = tens > 10 && tens < 14 ? "th" : ({ 1: "st", 2: "nd", 3: "rd" }[day % 10] || "th");
  return `${day}${suffix}`;
};

/** "Weekly · Monday at 08:00", "Monthly · last day at 08:00", "Hold until I request". */
export function timingLabel(plan) {
  if (!plan || plan.timing === "manual") return "Hold until I request";
  if (plan.timing === "settled") return "As funds settle";
  if (plan.timing === "weekly") return `Weekly · ${weekdays[plan.weekday]} at 08:00`;
  return `Monthly · ${plan.month_day ? `${ordinal(plan.month_day)} of the month` : "last day"} at 08:00`;
}
