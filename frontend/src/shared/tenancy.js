import { toIsoDate } from "./format";

export const tenantStatuses = [
  { value: "all", label: "All" },
  { value: "active", label: "Active" },
  { value: "applicant", label: "Applicants" },
  { value: "past", label: "Past" },
];

export const leaseStatuses = [
  { value: "all", label: "All" },
  { value: "active", label: "Active" },
  { value: "pending_signature", label: "Awaiting signature" },
  { value: "draft", label: "Draft" },
  { value: "ended", label: "Ended" },
];

const tenantBadge = {
  active: ["success", "Active"],
  applicant: ["informative", "Applicant"],
  past: ["subtle", "Past"],
};

const leaseBadge = {
  active: ["success", "Active"],
  pending_signature: ["warning", "Awaiting signature"],
  draft: ["informative", "Draft"],
  ended: ["subtle", "Ended"],
};

export const tenantBadgeProps = (status) => {
  const [color, label] = tenantBadge[status] || ["subtle", status];
  return { color, children: label };
};

export const leaseBadgeProps = (status) => {
  const [color, label] = leaseBadge[status] || ["subtle", status];
  return { color, children: label };
};

// New leases default to a 12-month term starting on the 1st of next month,
// which is how most Zambian residential lets are written.
export const defaultLeaseDates = () => {
  const today = new Date();
  const start = new Date(today.getFullYear(), today.getMonth() + 1, 1);
  const end = new Date(start.getFullYear() + 1, start.getMonth(), 0);
  return { start_date: toIsoDate(start), end_date: toIsoDate(end) };
};

export const emptyLease = () => ({
  unit: "",
  ...defaultLeaseDates(),
  monthly_rent: "",
  deposit_amount: "",
  rent_due_day: "1",
  activate: true,
});

const isMoney = (value) => /^\d+(\.\d{1,2})?$/.test(String(value).replace(/,/g, "").trim());

// Mirrors the API's lease rules so most mistakes are caught before a request.
export const leaseRules = (lease, prefix = "") => ({
  [`${prefix}unit`]: () => (lease.unit ? "" : "Choose a unit."),
  [`${prefix}start_date`]: () => (lease.start_date ? "" : "Choose a start date."),
  [`${prefix}end_date`]: () =>
    !lease.end_date ? "Choose an end date." : lease.end_date <= lease.start_date ? "End date must be after the start date." : "",
  [`${prefix}monthly_rent`]: () =>
    !isMoney(lease.monthly_rent) || Number(String(lease.monthly_rent).replace(/,/g, "")) <= 0 ? "Enter the monthly rent." : "",
  [`${prefix}deposit_amount`]: () =>
    lease.deposit_amount === "" || isMoney(lease.deposit_amount) ? "" : "Enter an amount like 7800 or 7800.00.",
  [`${prefix}rent_due_day`]: () => {
    const day = Number(lease.rent_due_day);
    return Number.isInteger(day) && day >= 1 && day <= 28 ? "" : "Choose a day from 1 to 28.";
  },
});

export const leasePayload = (lease) => ({
  unit: lease.unit,
  start_date: lease.start_date,
  end_date: lease.end_date,
  monthly_rent: String(lease.monthly_rent).replace(/,/g, "").trim(),
  deposit_amount: String(lease.deposit_amount || "0").replace(/,/g, "").trim(),
  rent_due_day: Number(lease.rent_due_day),
  activate: lease.activate,
});

export const LEASE_FIELDS = ["unit", "start_date", "end_date", "monthly_rent", "deposit_amount", "rent_due_day"];
