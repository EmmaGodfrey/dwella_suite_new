import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button, Field, Input, Select } from "@fluentui/react-components";
import {
  CheckmarkCircle20Regular,
  ArrowRight20Regular,
} from "@fluentui/react-icons";
import { useCurrentUserQuery, useSetupQuery } from "../../Services/queries";
import { useSaveSetupMutation } from "../../Services/mutations";
import { useFormErrors } from "../../shared/useFormErrors";
import { scopedStorageKey } from "../../shared/storage";
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
const fields = Object.keys(initial);

function SetupForm({ status, user }) {
  const navigate = useNavigate();
  const draftKey = scopedStorageKey(`dwella_setup_draft_${user.id}`);
  const [form, setForm] = useState(() => {
    try {
      return {
        ...initial,
        business_name: status.business_name,
        email: status.email,
        phone_number: status.phone_number,
        ...JSON.parse(sessionStorage.getItem(draftKey) || "{}"),
      };
    } catch {
      return { ...initial, email: status.email };
    }
  });
  const [step, setStep] = useState(0);
  const { validate, fieldProps, clearError, showServerErrors } =
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
      showServerErrors(error.data, fields);
      setStep(0);
    },
  });
  const update = (name, value) => {
    setForm((previous) => ({ ...previous, [name]: value }));
    clearError(name);
  };
  const input = (name, label, props = {}) => (
    <Field label={label} {...fieldProps(name)}>
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
    const required = (name, limit) =>
      form[name].trim() && form[name].trim().length <= limit
        ? ""
        : `Enter up to ${limit} characters.`;
    const rules =
      step === 0
        ? {
            business_name: () => required("business_name", 180),
            email: () =>
              !form.email || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)
                ? ""
                : "Enter a valid email address.",
            phone_number: () =>
              !form.phone_number || /^\+?[\d\s-]{7,40}$/.test(form.phone_number)
                ? ""
                : "Enter a valid phone number.",
          }
        : step === 1
          ? {
              property_name: () => required("property_name", 180),
              address: () => required("address", 1000),
              town: () =>
                form.town.length <= 120 ? "" : "Use up to 120 characters.",
            }
          : {
              unit_name: () => required("unit_name", 80),
              rent_amount: () =>
                /^\d{1,10}(\.\d{1,2})?$/.test(form.rent_amount)
                  ? ""
                  : "Enter a rent amount of zero or more, with up to two decimal places.",
            };
    if (!validate(rules, event.currentTarget)) return;
    if (step < 2) setStep(step + 1);
    else
      mutation.mutate(
        Object.fromEntries(
          Object.entries(form).map(([name, value]) => [name, value.trim()]),
        ),
      );
  };
  const titles = [
    "Tell us about your business",
    "Add your first property",
    "Set up your first unit",
  ];
  return (
    <div className="dwella-setup-grid">
      <nav aria-label="Setup progress">
        <p className="dwella-muted-copy">Set up your workspace</p>
        <ol className="dwella-setup-steps">
          {["Business details", "First property", "First unit"].map(
            (label, index) => (
              <li
                key={label}
                aria-current={step === index ? "step" : undefined}
              >
                <span>
                  {index < step ? <CheckmarkCircle20Regular /> : index + 1}
                </span>
                <div>
                  <strong>{label}</strong>
                  <small>
                    {
                      [
                        "Your name and contact details",
                        "Location and property type",
                        "Unit name and monthly rent",
                      ][index]
                    }
                  </small>
                </div>
              </li>
            ),
          )}
        </ol>
      </nav>
      <form
        className="dwella-surface dwella-setup-form"
        onSubmit={submit}
        noValidate
      >
        <span className="dwella-muted-copy">Step {step + 1} of 3</span>
        <h2>{titles[step]}</h2>
        <p className="dwella-muted-copy">
          {
            [
              "These details appear on your receipts. You can manage one property or a whole portfolio.",
              "Start with one property. You can add the rest from Properties.",
              "A unit can be a flat, office or an entire house. Add a tenant and lease after setup.",
            ][step]
          }
        </p>
        <div className="dwella-setup-fields">
          {step === 0 ? (
            <>
              {input("business_name", "Business or landlord name", {
                maxLength: 180,
                autoFocus: true,
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
              {input("property_name", "Property name", {
                maxLength: 180,
                autoFocus: true,
              })}
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
                autoFocus: true,
              })}
              {input("rent_amount", "Monthly asking rent (ZMW)", {
                inputMode: "decimal",
                placeholder: "e.g. 3900.00",
              })}
              <p className="dwella-muted-copy">
                {form.property_name} · {form.address}
                {form.town ? `, ${form.town}` : ""}
              </p>
            </>
          )}
        </div>
        {mutation.isError ? (
          <p role="alert" className="dwella-alert danger">
            {mutation.error.message}
          </p>
        ) : null}
        <div className="dwella-setup-actions">
          <Button
            disabled={step === 0 || mutation.isPending}
            onClick={() => setStep(step - 1)}
          >
            Back
          </Button>
          <Button
            type="submit"
            appearance="primary"
            icon={<ArrowRight20Regular />}
            iconPosition="after"
            disabled={mutation.isPending}
          >
            {mutation.isPending
              ? "Creating workspace…"
              : step === 2
                ? "Create workspace"
                : "Continue"}
          </Button>
        </div>
      </form>
      <aside className="dwella-setup-help">
        <h3>
          {
            [
              "Your business, on every receipt",
              "Build your portfolio",
              "Make it useful",
            ][step]
          }
        </h3>
        <p>
          {
            [
              "Tenants see who received their payment. Use your business name or your own name if you manage property independently.",
              "Keep every property and unit together, with rent, tenants and repairs in one place.",
              "Next, add your tenant, activate their lease and generate your first rent invoice. We’ll guide you through it.",
            ][step]
          }
        </p>
        <p>Your progress on this form is saved in this browser tab.</p>
      </aside>
    </div>
  );
}

export default function Setup() {
  const query = useSetupQuery();
  const { data: user } = useCurrentUserQuery();
  if (query.isLoading || !user)
    return <p role="status">Loading your workspace…</p>;
  if (query.isError)
    return (
      <div role="alert">
        <p>Could not load setup.</p>
        <Button onClick={() => query.refetch()}>Retry</Button>
      </div>
    );
  if (query.data.needs_setup)
    return <SetupForm status={query.data} user={user} />;
  const steps = query.data.steps;
  const complete = steps.every((item) => item.done);
  const next = steps.find((item) => !item.done);
  return (
    <section className="dwella-setup-checklist">
      <h2>
        {complete ? "Your workspace is ready" : "Make Dwella work for you"}
      </h2>
      <p className="dwella-muted-copy">
        {complete
          ? "Your properties, tenants and rent are connected. Keep managing your portfolio from the dashboard."
          : "Your first property is in. Follow these steps to start tracking rent."}
      </p>
      <ol>
        {steps.map((item, index) => (
          <li key={item.key}>
            <span className={item.done ? "is-complete" : ""}>
              {item.done ? <CheckmarkCircle20Regular /> : index + 1}
            </span>
            <div>
              <strong>{item.label}</strong>
              <small>{item.done ? "Complete" : "Still to do"}</small>
            </div>
            {!item.done && item.path !== "/setup" ? (
              <Link to={item.path}>Get started →</Link>
            ) : null}
          </li>
        ))}
      </ol>
      <Button
        as={Link}
        to={next?.path && next.path !== "/setup" ? next.path : "/dashboard"}
        appearance="primary"
      >
        {complete ? "Go to dashboard" : "Continue setup"}
      </Button>
    </section>
  );
}
