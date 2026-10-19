import React from "react";
import "./modulePlaceholder.scss";
import { Clock20Regular } from "@fluentui/react-icons";

// The topbar already names the module and describes it, so this says the one
// thing it cannot: the workspace is not built yet. It said so three ways
// before -- an eyebrow, a heading, and a badge -- for a single fact.
const ModulePlaceholder = ({ description }) => (
  <div className="dwella-screen">
    <section className="dwella-module-placeholder">
      <Clock20Regular />
      <div>
        <strong>Not available yet</strong>
        <p>{description}</p>
      </div>
    </section>
  </div>
);

export default ModulePlaceholder;
