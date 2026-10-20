import React from "react";
import { Badge } from "@fluentui/react-components";

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

// The class is what lets dense rows hide the badge at narrow widths; without it
// the rule in dashboard.scss has nothing to match.
export const StatusBadge = ({ value, color, children, className = "" }) => (
  <Badge
    className={`dwella-status-badge ${className}`.trim()}
    appearance="tint"
    color={color || defaultStatusColor(value)}
  >
    {children || labelize(value)}
  </Badge>
);
