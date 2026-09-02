import React from "react";
import { Badge } from "@fluentui/react-components";

export const labelize = (value) => String(value || "Not set").replace(/_/g, " ");

export const defaultStatusColor = (value) => {
  if (["active", "approved", "delivered", "managed", "occupied"].includes(value)) return "success";
  if (["pending", "prospect", "vacant"].includes(value)) return "warning";
  if (["archived", "inactive", "rejected"].includes(value)) return "danger";
  return "subtle";
};

export const StatusBadge = ({ value, color, children }) => (
  <Badge appearance="tint" color={color || defaultStatusColor(value)}>
    {children || labelize(value)}
  </Badge>
);
