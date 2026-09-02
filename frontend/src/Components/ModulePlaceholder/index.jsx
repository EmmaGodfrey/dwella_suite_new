import React from "react";
import { Button, Card, Text, Title2 } from "@fluentui/react-components";
import { ArrowRight24Regular, Clock24Regular } from "@fluentui/react-icons";

const ModulePlaceholder = ({ title, description }) => (
  <div className="dwella-screen">
    <Card className="dwella-card dwella-module-placeholder" appearance="outline">
      <span><Clock24Regular /></span>
      <div>
        <Text className="dwella-kicker">Module workspace</Text>
        <Title2>{title}</Title2>
        <Text>{description}</Text>
      </div>
      <Button appearance="secondary" icon={<ArrowRight24Regular />} iconPosition="after">Coming next</Button>
    </Card>
  </div>
);

export default ModulePlaceholder;
