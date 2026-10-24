import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button, Field, Input, Select } from "@fluentui/react-components";
import { CheckmarkCircle20Regular } from "@fluentui/react-icons";
import { useCurrentUserQuery, useSetupQuery } from "../../Services/queries";
import { useSaveSetupMutation } from "../../Services/mutations";
import { useFormErrors } from "../../shared/useFormErrors";
import { scopedStorageKey } from "../../shared/storage";
import { firstErrorStep, ruleErrors } from "../../shared/formFlow";
import { FormPage } from "../../shared/components/FormFlow";
import "./setup.scss";

const initial = {
  business_name: "",
  email: "",
  phone_number: "",
  property_name: "",
  property_type: "apartment",
  address: "",
  town: "",
  unit_name: "",
  rent_amount: "",
};
const groups = [
  ["business_name", "email", "phone_number"],
  ["property_name", "property_type", "address", "town"],
  ["unit_name", "rent_amount"],
];
const taskNotes = {
  workspace: "Business and receipt details",
  property: "Property location, unit and asking rent",
  tenant: "Contact details for the person renting",
  lease: "Connect a tenant, unit and lease terms",
  invoice: "Create the invoice from Billing",
};
const taskPath = (item) =>
  item?.key === "tenant" && item.path === "/tenants"
    ? "/tenants?new=1"
    : item?.path && item.path !== "/setup"
      ? item.path
      : "/dashboard";

function SetupForm({ status, user }) {
  const navigate = useNavigate();
  const draftKey = scopedStorageKey(`dwella_setup_draft_${user.id}`);
  const [form, setForm] = useState(() => {
    const base = {
      ...initial,
      business_name: status.business_name || "",
      email: status.email || "",
      phone_number: status.phone_number || "",
    };
    try {
      const draft = JSON.parse(sessionStorage.getItem(draftKey) || "{}");
      return Object.fromEntries(
        Object.entries(base).map(([key, value]) => [
          key,
          typeof draft?.[key] === "string" ? draft[key] : value,
        ]),
      );
    } catch {
      return base;
    }
  });
  const [step, setStep] = useState(0);
  const { errors, validate, fieldProps, clearError, showServerErrors } =
    useFormErrors();
  useEffect(() => {
    sessionStorage.setItem(draftKey, JSON.stringify(form));
  }, [draftKey, form]);
  const mutation = useSaveSetupMutation({
    onSuccess: () => {
      sessionStorage.removeItem(draftKey);
      navigate("/setup", { replace: true });
    },
    onError: (error) => {
      showServerErrors(error.data, Object.keys(initial));
      setStep(firstErrorStep(error.data, groups, step));
    },
  });
  const update = (name, value) => {
    setForm((previous) => ({ ...previous, [name]: value }));
    clearError(name);
  };
  const input = (name, label, props = {}) => (
    <Field
      label={label}
      required={!["email", "phone_number", "town"].includes(name)}
      {...fieldProps(name)}
      className={`${["business_name", "address"].includes(name) ? "dwella-field-wide" : ""} ${fieldProps(name).className || ""}`}
    >
      <Input
        name={name}
        value={form[name]}
        onChange={(_, data) => update(name, data.value)}
        {...props}
      />
    </Field>
  );
  const submit = (event) => {
    event.preventDefault();
    if (mutation.isPending) return;
    const required = (name, limit) =>
      form[name].trim() && form[name].trim().length <= limit
        ? ""
        : `Enter up to ${limit} characters.`;
    const allRules = {
      business_name: () => required("business_name", 180),
      email: () =>
        !form.email || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)
          ? ""
          : "Enter a valid email address.",
      phone_number: () =>
        !form.phone_number || /^\+?[\d\s-]{7,40}$/.test(form.phone_number)
          ? ""
          : "Enter a valid phone number.",
      property_name: () => required("property_name", 180),
      address: () => required("address", 1000),
      town: () => (form.town.length <= 120 ? "" : "Use up to 120 characters."),
      unit_name: () => required("unit_name", 80),
      rent_amount: () =>
        /^\d{1,10}(\.\d{1,2})?$/.test(form.rent_amount)
          ? ""
          : "Enter rent of zero or more, with up to two decimal places.",
    };
    const rules =
      step === 2
        ? allRules
        : Object.fromEntries(
            Object.entries(allRules).filter(([name]) =>
              groups[step].includes(name),
            ),
          );
    if (!validate(rules, event.currentTarget)) {
      setStep(firstErrorStep(ruleErrors(rules), groups, step));
      return;
    }
    if (step < 2) setStep(step + 1);
    else
      mutation.mutate(
        Object.fromEntries(
          Object.entries(form).map(([name, value]) => [name, value.trim()]),
        ),
      );
  };
  return (
    <FormPage
      title="Set up your workspace"
      description="Start with your business, one property and one unit."
      steps={["Business", "Property", "Unit"]}
      step={step}
      errors={errors}
      busy={mutation.isPending}
      stepTitle={
        ["Business details", "Your first property", "Your first unit"][step]
      }
      stepDescription={
        [
          "These details appear on your receipts.",
          "You can add more properties after setup.",
          "A unit can be a flat, office or an entire house.",
        ][step]
      }
      onSubmit={submit}
      onBack={() => setStep(step - 1)}
      submitLabel="Create workspace"
      pendingLabel="Creating workspace…"
      notice={
        <>
          {mutation.isError && (
            <p role="alert" className="dwella-alert danger">
            {mutation.error.message}
          </p>
          )}
          <p className="dwella-muted-copy">
            Your progress is saved in this browser tab.
          </p>
        </>
      }
    >
      <div className="dwella-setup-form-layout">
        <div className="dwella-form-grid">
          {step === 0 ? (
            <>
              {input("business_name", "Business or property manager name", {
                maxLength: 180,
              })}
              {input("email", "Email for receipts (optional)", {
                type: "email",
                maxLength: 254,
              })}
              {input("phone_number", "Contact number (optional)", {
                type: "tel",
                maxLength: 40,
              })}
            </>
          ) : step === 1 ? (
            <>
              {input("property_name", "Property name", { maxLength: 180 })}
              <Field label="Property type">
                <Select
                  value={form.property_type}
                  onChange={(_, data) => update("property_type", data.value)}
                >
                  {[
                    ["apartment", "Apartment"],
                    ["house", "House"],
                    ["commercial", "Commercial"],
                    ["mixed_use", "Mixed use"],
                    ["land", "Land"],
                  ].map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </Select>
              </Field>
              {input("address", "Street address", { maxLength: 1000 })}
              {input("town", "Town or city (optional)", { maxLength: 120 })}
            </>
          ) : (
            <>
              {input("unit_name", "Unit name", {
                maxLength: 80,
                placeholder: "e.g. Flat 1 or Main house",
              })}
              {input("rent_amount", "Monthly asking rent (ZMW)", {
                inputMode: "decimal",
                placeholder: "e.g. 3900.00",
              })}
              <p className="dwella-muted-copy dwella-field-wide">
                {form.property_name} · {form.address}
                {form.town ? `, ${form.town}` : ""}
              </p>
            </>
          )}
        </div>
        <aside className="dwella-form-context">
          <h3>
            {
              [
                "On every receipt",
                "One place for your portfolio",
                "What happens next",
              ][step]
            }
          </h3>
          <p>
            {
              [
                "Use the business name your tenants recognise. Independent property managers can use their own name.",
                "Use a recognisable name. Property and unit details can be updated later.",
                "Add a tenant, activate their lease, then generate your first rent invoice.",
              ][step]
            }
          </p>
        </aside>
      </div>
    </FormPage>
  );
}

export default function Setup() {
  const query = useSetupQuery();
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
  if (query.data.needs_setup)
    return <SetupForm status={query.data} user={userQuery.data} />;
  const steps = query.data.steps;
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
              : "Your first property is in. Next, connect your tenants and rent."}
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
          <Button as={Link} to={taskPath(next)} appearance="primary">
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
      </div>
      <p className="dwella-muted-copy">
        Return here at any time from Get started in the sidebar.
      </p>
    </section>
  );
}
