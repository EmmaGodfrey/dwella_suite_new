// Maintenance vocabulary shared by the board, the request detail and drawers.

export const boardColumns = [
  { value: "new", label: "New", tone: "var(--dwella-info)" },
  { value: "scheduled", label: "Scheduled", tone: "var(--dwella-violet)" },
  { value: "in_progress", label: "In progress", tone: "var(--dwella-warning)" },
  { value: "completed", label: "Done this week", tone: "var(--dwella-accent-strong)" },
];

export const requestStatuses = [
  { value: "new", label: "New", color: "informative" },
  { value: "scheduled", label: "Scheduled", color: "important" },
  { value: "in_progress", label: "In progress", color: "warning" },
  { value: "completed", label: "Done", color: "success" },
  { value: "cancelled", label: "Cancelled", color: "subtle" },
];

export const priorities = [
  { value: "urgent", label: "Urgent", color: "danger" },
  { value: "high", label: "High", color: "warning" },
  { value: "normal", label: "Normal", color: "subtle" },
  { value: "low", label: "Low", color: "subtle" },
];

export const categories = [
  { value: "plumbing", label: "Plumbing" },
  { value: "electrical", label: "Electrical" },
  { value: "roofing", label: "Roofing" },
  { value: "appliances", label: "Appliances" },
  { value: "security", label: "Security & locks" },
  { value: "painting", label: "Painting & walls" },
  { value: "pest_control", label: "Pest control" },
  { value: "grounds", label: "Grounds & cleaning" },
  { value: "general", label: "General" },
];

export const sources = [
  { value: "landlord", label: "Me or my team" },
  { value: "tenant", label: "Tenant" },
  { value: "caretaker", label: "Caretaker" },
  { value: "inspection", label: "Inspection" },
];

const find = (list, value) => list.find((item) => item.value === value);

export const statusBadgeProps = (status) => {
  const item = find(requestStatuses, status) || { color: "subtle", label: status };
  return { color: item.color, children: item.label };
};

export const priorityBadgeProps = (priority) => {
  const item = find(priorities, priority) || { color: "subtle", label: priority };
  return { color: item.color, children: item.label };
};

export const categoryLabel = (value) => find(categories, value)?.label || "General";
export const sourceLabel = (value) => find(sources, value)?.label || value;

export const locationLabel = (request) =>
  request.unit_name ? `${request.unit_name} · ${request.property_name}` : `${request.property_name} · Common area`;

const dayTime = new Intl.DateTimeFormat("en-GB", { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
const weekday = new Intl.DateTimeFormat("en-GB", { weekday: "short" });

export const formatVisit = (value) => (value ? dayTime.format(new Date(value)) : "—");

// "2 h ago", "Yesterday", "3 days" — the board's age stamp.
export const ageLabel = (value) => {
  const hours = (Date.now() - new Date(value).getTime()) / 3_600_000;
  if (hours < 1) return "Just now";
  if (hours < 24) return `${Math.floor(hours)} h ago`;
  const days = Math.floor(hours / 24);
  return days === 1 ? "Yesterday" : `${days} days`;
};

// "Started Mon", "Closed today".
export const dayLabel = (prefix, value) => {
  if (!value) return "";
  const date = new Date(value);
  const today = new Date();
  const same = date.toDateString() === today.toDateString();
  return `${prefix} ${same ? "today" : weekday.format(date)}`;
};

// <input type="datetime-local"> wants local time without a zone.
export const toLocalInput = (value) => {
  if (!value) return "";
  const date = new Date(value);
  const pad = (n) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
};
