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
  if (["pending", "prospect", "vacant"].includes(value)) return "warning";
  if (["archived", "inactive", "rejected"].includes(value)) return "danger";
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
