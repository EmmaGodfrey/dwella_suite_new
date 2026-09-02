import React from "react";
import { Card, Caption1, Text, Title2 } from "@fluentui/react-components";

export const MetricCard = ({ icon, label, value, detail, className = "" }) => (
  <Card className={`dwella-card dwella-metric ${className}`.trim()} appearance="outline">
    {icon ? <span className="dwella-metric-icon">{icon}</span> : null}
    <Text size={200}>{label}</Text>
    <Title2>{value}</Title2>
    {detail ? <Caption1>{detail}</Caption1> : null}
  </Card>
);
