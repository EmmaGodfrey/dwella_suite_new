import React from "react";
import { Button } from "@fluentui/react-components";

import { isNotLinked } from "../../Services/portal";
import "../../shared/records.scss";
import "./portal.scss";

export function NotLinked() {
  return (
    <section className="dwella-surface dwella-portal-unlinked">
      <h3>Your account is not linked to a tenancy yet</h3>
      <p className="dwella-muted-copy">
        Your property manager links your account by sending an invitation to your email. Once you accept it, your
        lease, payments and repairs appear here.
      </p>
      <p className="dwella-muted-copy">
        Already accepted an invitation? Your manager may have removed access or archived the record. Ask them to send
        a new one.
      </p>
    </section>
  );
}

// Loading, not-linked and error states shared by every tenant page.
export default function PortalState({ query, label, children, skeleton = 240 }) {
  if (query.isLoading) {
    return (
      <div className="dwella-portal" aria-busy="true">
        <span className="dwella-skeleton" style={{ height: skeleton, width: "100%" }} />
      </div>
    );
  }
  if (isNotLinked(query.error)) return <NotLinked />;
  if (query.isError) {
    return (
      <div className="dwella-alert danger" role="alert">
        Could not load {label}. <Button size="small" onClick={() => query.refetch()}>Retry</Button>
      </div>
    );
  }
  return children(query.data);
}
