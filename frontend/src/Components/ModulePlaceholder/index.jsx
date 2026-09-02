import React from "react";
import { Button, Text, Title2 } from "@fluentui/react-components";
import { ArrowRight24Regular, Clock24Regular } from "@fluentui/react-icons";

import { PageSection } from "../../shared/components";

const ModulePlaceholder = ({ title, description }) => (
  <div className="dwella-screen">
    <PageSection className="dwella-module-placeholder">
      <span><Clock24Regular /></span>
      <div>
        <Text className="dwella-kicker">Module workspace</Text>
        <Title2>{title}</Title2>
        <Text>{description}</Text>
      </div>
      <Button appearance="secondary" icon={<ArrowRight24Regular />} iconPosition="after">Coming next</Button>
    </PageSection>
  </div>
);

export default ModulePlaceholder;
