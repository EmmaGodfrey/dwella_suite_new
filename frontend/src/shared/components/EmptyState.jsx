import React from "react";
import { Button, Text, Title3 } from "@fluentui/react-components";

export const EmptyState = ({ icon, title, description, actionLabel, onAction }) => (
  <div className="dwella-empty-state">
    {icon}
    <Title3>{title}</Title3>
    {description ? <Text>{description}</Text> : null}
    {actionLabel && onAction ? <Button appearance="primary" onClick={onAction}>{actionLabel}</Button> : null}
  </div>
);
