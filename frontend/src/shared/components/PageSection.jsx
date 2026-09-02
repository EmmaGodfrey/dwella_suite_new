import React from "react";
import { Card, Text, Title3 } from "@fluentui/react-components";

export const PageSection = ({ title, note, actions, children, className = "", as: Heading = "h2" }) => (
  <Card className={`dwella-card dwella-panel dwella-section ${className}`.trim()} appearance="outline">
    {(title || note || actions) ? (
      <header className="dwella-panel-heading">
        <div>
          {title ? <Title3 as={Heading}>{title}</Title3> : null}
          {note ? <Text size={200}>{note}</Text> : null}
        </div>
        {actions ? <div className="dwella-panel-actions">{actions}</div> : null}
      </header>
    ) : null}
    {children}
  </Card>
);
