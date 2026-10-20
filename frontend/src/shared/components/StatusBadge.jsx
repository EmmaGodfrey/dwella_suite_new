import React from "react";

export const labelize = (value) =>
  String(value || "Not set")
    .replace(/_/g, " ")
    .replace(/^./, (letter) => letter.toUpperCase());

export const defaultStatusColor = (value) => {
  if (
    ["active", "approved", "delivered", "managed", "occupied"].includes(value)
  )
    return "success";
  if (["pending", "vacant"].includes(value)) return "warning";
  if (["prospect"].includes(value)) return "informative";
  if (["maintenance", "rejected"].includes(value)) return "danger";
  if (["reserved"].includes(value)) return "important";
  return "subtle";
};

// The Figma status pill: a tinted fill, a dot, no outline. Drawn here rather
// than with Fluent's Badge so it takes the `--dwella-*` tones in both themes.
// `color` keeps Fluent's names (success, warning, danger, informative,
// important, subtle) so callers did not have to change.
export const StatusBadge = ({ value, color, children, className = "" }) => (
  <span className={`dwella-status-badge ${className}`.trim()} data-tone={color || defaultStatusColor(value)}>
    {children || labelize(value)}
  </span>
);
