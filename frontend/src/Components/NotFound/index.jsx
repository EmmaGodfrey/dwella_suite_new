import React from "react";
import { useNavigate } from "react-router-dom";
import { DocumentQuestionMark24Regular } from "@fluentui/react-icons";
import { EmptyState } from "../../shared/components";

// Shown inside the app shell for any address the app does not know, so the
// sidebar stays available instead of a blank screen.
export default function NotFound() {
  const navigate = useNavigate();
  return (
    <section aria-labelledby="dwella-not-found-title" className="dwella-not-found">
      <h1 id="dwella-not-found-title" className="dwella-visually-hidden">Page not found</h1>
      <EmptyState
        icon={<DocumentQuestionMark24Regular />}
        title="Page not found"
        description="This address doesn't match a page in Dwella. It may have moved, or the link may be mistyped."
        actionLabel="Go to home"
        onAction={() => navigate("/dashboard", { replace: true })}
      />
    </section>
  );
}
