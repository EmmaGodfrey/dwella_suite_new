export const propertyTypes = [
  { value: "", label: "All types" },
  { value: "apartment", label: "Apartment" },
  { value: "house", label: "House" },
  { value: "commercial", label: "Commercial" },
  { value: "mixed_use", label: "Mixed use" },
  { value: "land", label: "Land" },
];
export const managementStatuses = [
  { value: "", label: "All statuses" },
  { value: "managed", label: "Managed" },
  { value: "prospect", label: "Prospect" },
  { value: "archived", label: "Archived" },
];
export const orderOptions = [
  { value: "name", label: "Name A-Z" },
  { value: "-created_at", label: "Newest first" },
  { value: "management_status", label: "Status" },
];
export const optionLabel = (items, value) =>
  items.find((item) => item.value === value)?.label || "";
export const formatRent = (value) =>
  new Intl.NumberFormat("en-ZM", {
    style: "currency",
    currency: "ZMW",
    maximumFractionDigits: 0,
  }).format(Number(value || 0));
