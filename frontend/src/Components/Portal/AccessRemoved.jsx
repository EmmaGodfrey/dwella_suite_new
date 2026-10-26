import React from "react";
import { Button } from "@fluentui/react-components";

export default function AccessRemoved({ onLogout }) {
  return <main className="dwella-page-content" style={{ padding: "2rem" }}>
    <h1>Your tenant access has been removed</h1>
    <p>Contact your property manager if you need a new invitation.</p>
    <p>Your tenancy and payment records remain with the workspace.</p>
    <Button appearance="primary" onClick={onLogout}>Sign out</Button>
  </main>;
}
