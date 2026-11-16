import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@fluentui/react-components";
import { CheckmarkCircle20Regular } from "@fluentui/react-icons";
import { useCurrentUserQuery, useSetupQuery } from "../../Services/queries";
import WhatsAppConnection from "../../shared/components/WhatsAppConnection";
import AccountSetup from "./AccountSetup";
import "./setup.scss";

const taskNotes = {
  workspace: "Business identity, address, contact and regional details",
  payment_methods: "Bank, mobile money or cash arrangements",
  billing_preferences: "Invoice timing and reminder preferences",
  account_review: "Confirm the account is ready for your portfolio",
  property: "Property location, units and asking rent; bulk import is also available",
  tenant: "Identity, contact and billing details for the person renting",
  lease: "Connect a tenant and unit, set terms and record any opening balance",
  invoice: "Preview the issuer and payment details, then explicitly create your first invoice",
};
const taskPath = item => item?.key === "tenant" ? "/tenants?new=1" : item?.path || "/dashboard";

export default function Setup() {
  const query = useSetupQuery();
  const [reviewAccount, setReviewAccount] = useState(false);
  const userQuery = useCurrentUserQuery();
  if (query.isError || userQuery.isError)
    return (
      <div role="alert" className="dwella-surface">
        <p>Could not load setup.</p>
        <Button
          onClick={() => {
            query.refetch();
            userQuery.refetch();
          }}
        >
          Retry
        </Button>
      </div>
    );
  if (query.isLoading || !userQuery.data)
    return <p role="status">Loading your workspace…</p>;
  if (query.data.can_setup && (!query.data.account_ready || reviewAccount))
    return <AccountSetup status={query.data} onComplete={() => setReviewAccount(false)} onClose={query.data.account_ready ? () => setReviewAccount(false) : undefined} />;
  const steps = query.data.steps.filter(item => item.required !== false);
  const done = steps.filter((item) => item.done).length;
  const complete = done === steps.length;
  const next = steps.find((item) => !item.done);
  return (
    <section className="dwella-setup-checklist dwella-form-page">
      <header className="dwella-page-header">
        <div className="dwella-page-header-copy">
          <h1>
            {complete ? "Your workspace is ready" : "Make Dwella work for you"}
          </h1>
          <p>
            {complete
              ? "Your properties, tenants and rent are connected."
              : "Your account is ready. Continue with your properties, units, tenants and rent."}
          </p>
        </div>
      </header>
      <div className="dwella-setup-checklist-surface">
        <div className="dwella-setup-progress-heading">
          <div>
            <h2>
              {done} of {steps.length} complete
            </h2>
            <p>
              {complete
                ? "All setup tasks are complete."
                : `Continue with: ${next.label.toLowerCase()}.`}
            </p>
          </div>
          <Button as={Link} to={complete ? "/dashboard" : taskPath(next)} appearance="primary">
            {complete ? "Go to dashboard" : next.label}
          </Button>
        </div>
        <progress
          className="dwella-setup-progress"
          max={steps.length}
          value={done}
          aria-label="Workspace setup completion"
        />
        <ol>
          {steps.map((item, index) => (
            <li
              key={item.key}
              className={`${item.done ? "is-complete" : ""} ${item === next ? "is-next" : ""}`}
            >
              <span className="dwella-setup-task-number" aria-hidden="true">
                {item.done ? <CheckmarkCircle20Regular /> : index + 1}
              </span>
              <div className="dwella-setup-task-copy">
                <strong>{item.label}</strong>
                <small>{taskNotes[item.key]}</small>
              </div>
              <span className="dwella-setup-task-status">
                {item.done
                  ? "Complete"
                  : item === next
                    ? "Next step"
                    : "Still to do"}
              </span>
              {!item.done && item !== next && item.path !== "/setup" && (
                <Link to={taskPath(item)}>Open</Link>
              )}
            </li>
          ))}
        </ol>
        {query.data.can_setup && <div className="dwella-setup-review-actions">
          <Button onClick={() => setReviewAccount(true)}>Review account details</Button>
          <Link to="/team">Invite teammates (optional)</Link>
        </div>}
        <WhatsAppConnection onboarding />
      </div>
      <p className="dwella-muted-copy">
        Return here at any time from <Link to="/settings?tab=account">Settings</Link> using Review setup.
      </p>
    </section>
  );
}
