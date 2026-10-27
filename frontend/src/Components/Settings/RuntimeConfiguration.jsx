import React, { useEffect, useState } from "react";
import {
  Button,
  Field,
  Input,
  Select,
  Switch,
  Textarea,
} from "@fluentui/react-components";
import { toast } from "react-toastify";
import { usePlatformList, usePlatformMutation } from "../../Services/platform";
import { useFormErrors } from "../../shared/useFormErrors";
import { AdminState } from "../Platform/AdminUI";

const fields = {
  assistant: ["assistant_url", "assistant_title", "assistant_suggestions"],
  support: [
    "support_email",
    "support_phone",
    "support_whatsapp",
    "support_help_url",
  ],
  messaging: [
    "email_sender_name",
    "email_from_address",
    "email_reply_to",
    "email_daily_limit",
    "messaging_email_enabled",
    "sms_enabled",
    "sms_sender_id",
    "whatsapp_enabled",
    "whatsapp_template",
    "whatsapp_language",
  ],
  beta: [
    "beta_open_date",
    "launch_date",
    "beta_registration_open",
    "beta_emails_enabled",
    "beta_countdown_days",
    "beta_send_hour",
  ],
};
const labels = {
  assistant_url: "Handy connection address",
  assistant_title: "Assistant title",
  support_email: "Support email",
  support_phone: "Support phone",
  support_whatsapp: "Support WhatsApp number",
  support_help_url: "Help link",
  email_sender_name: "Sender display name",
  email_from_address: "Approved sender address",
  email_reply_to: "Reply-to address",
  email_daily_limit: "Daily email allowance",
  sms_sender_id: "Approved SMS sender",
  whatsapp_template: "Approved reminder template",
  whatsapp_language: "Template language",
  beta_open_date: "Beta opening date",
  launch_date: "Public launch date",
  beta_send_hour: "Email send hour (Africa/Lusaka)",
};
const toggles = {
  messaging_email_enabled: "Allow email reminders and notices",
  sms_enabled: "Allow SMS delivery",
  whatsapp_enabled: "Allow WhatsApp delivery",
  beta_registration_open: "Allow self-service registration",
  beta_emails_enabled: "Allow beta signup emails",
};
const groups = {
  assistant: [
    [
      "Handy connection",
      "Changing the address turns the assistant off until the saved connection is checked.",
      fields.assistant,
    ],
  ],
  support: [
    [
      "Support contacts",
      "Shown in the app and on the Dwella website. Leave unused contacts blank.",
      fields.support,
    ],
  ],
  messaging: [
    [
      "Email identity and allowance",
      "Account emails, lease signing and notices share the SMTP allowance. Sender addresses must be approved for this environment.",
      fields.messaging.slice(0, 5),
    ],
    [
      "SMS",
      "Use a registered sender. API credentials remain protected on the server.",
      ["sms_sender_id", "sms_enabled"],
    ],
    [
      "WhatsApp Business",
      "Use an approved reminder template and language. Recipient consent still applies.",
      ["whatsapp_template", "whatsapp_language", "whatsapp_enabled"],
    ],
  ],
  beta: [
    [
      "Beta access and emails",
      "The app, website countdown and scheduled emails use this opening date. Saving sends no email; old missed steps stay withheld.",
      fields.beta,
    ],
  ],
};

export default function RuntimeConfiguration({ section }) {
  const query = usePlatformList("runtime-settings", {}, { retry: false });
  return (
    <AdminState query={query}>
      {query.data && (
        <ConfigurationForm
          key={`${section}:${JSON.stringify(query.data)}`}
          section={section}
          data={query.data}
        />
      )}
    </AdminState>
  );
}

function ConfigurationForm({ section, data }) {
  const initial = Object.fromEntries(
    fields[section].map((key) => [key, data.values[key]]),
  );
  const [draft, setDraft] = useState(initial);
  const [suggestions, setSuggestions] = useState(
    (initial.assistant_suggestions || []).join("\n"),
  );
  const [days, setDays] = useState(
    (initial.beta_countdown_days || []).join(", "),
  );
  const [checkError, setCheckError] = useState("");
  const errors = useFormErrors();
  const mutation = usePlatformMutation({
    onSuccess: () =>
      window.dispatchEvent(new Event("dwella:assistant-settings-changed")),
  });
  const check = usePlatformMutation();
  const ready = data.readiness;
  const normalized = {
    ...draft,
    ...(section === "assistant"
      ? {
          assistant_suggestions: suggestions
            .split("\n")
            .map((s) => s.trim())
            .filter(Boolean),
        }
      : {}),
    ...(section === "beta"
      ? { beta_countdown_days: days.split(",").map((s) => Number(s.trim())) }
      : {}),
  };
  const dirty = JSON.stringify(normalized) !== JSON.stringify(initial);
  const pending = mutation.isPending || check.isPending;
  const change = (key, value) => {
    setDraft((v) => ({ ...v, [key]: value }));
    errors.clearError(key);
    setCheckError("");
  };
  useEffect(() => {
    setCheckError("");
  }, [section]);
  const validate = () => {
    const rules = {};
    for (const key of fields[section]) {
      if (
        key.endsWith("_email") ||
        ["email_from_address", "email_reply_to"].includes(key)
      )
        rules[key] = () =>
          !normalized[key] || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalized[key])
            ? ""
            : "Enter a valid email address.";
    }
    if (section === "assistant") {
      rules.assistant_url = () =>
        !draft.assistant_url || /^https:\/\/[^\s]+$/.test(draft.assistant_url)
          ? ""
          : "Use an HTTPS connection address.";
      rules.assistant_title = () =>
        draft.assistant_title?.trim() ? "" : "Enter an assistant title.";
      rules.assistant_suggestions = () =>
        normalized.assistant_suggestions.length <= 6 &&
        normalized.assistant_suggestions.every((s) => s.length <= 160)
          ? ""
          : "Use up to six questions, each at most 160 characters.";
    }
    if (section === "support") {
      rules.support_help_url = () =>
        !draft.support_help_url ||
        /^https:\/\/[^\s]+$/.test(draft.support_help_url)
          ? ""
          : "Use an HTTPS help link.";
      rules.support_whatsapp = () =>
        !draft.support_whatsapp ||
        /^\+?[1-9]\d{7,14}$/.test(draft.support_whatsapp)
          ? ""
          : "Use an international number, for example +260971234567.";
    }
    if (section === "messaging") {
      rules.email_daily_limit = () =>
        Number.isInteger(draft.email_daily_limit) &&
        draft.email_daily_limit >= 1 &&
        draft.email_daily_limit <= ready.email_daily_max
          ? ""
          : `Choose 1–${ready.email_daily_max} recipients per day.`;
      rules.whatsapp_template = () =>
        !draft.whatsapp_template ||
        /^[a-z0-9_]{1,120}$/.test(draft.whatsapp_template)
          ? ""
          : "Use a valid template name.";
      rules.whatsapp_language = () =>
        /^[a-z]{2,3}(?:_[A-Z]{2})?$/.test(draft.whatsapp_language || "")
          ? ""
          : "Use a language code such as en or en_US.";
      rules.sms_sender_id = () =>
        !draft.sms_sender_id ||
        /^[A-Za-z0-9 ._-]{1,20}$/.test(draft.sms_sender_id)
          ? ""
          : "Enter a valid sender ID.";
    }
    if (section === "beta") {
      rules.beta_open_date = () =>
        /^\d{4}-\d{2}-\d{2}$/.test(draft.beta_open_date || "")
          ? ""
          : "Choose the opening date.";
      rules.launch_date = () =>
        /^\d{4}-\d{2}-\d{2}$/.test(draft.launch_date || "") &&
        draft.launch_date >= draft.beta_open_date
          ? ""
          : "Choose a launch date on or after the beta opening.";
      rules.beta_send_hour = () =>
        Number.isInteger(draft.beta_send_hour) &&
        draft.beta_send_hour >= 0 &&
        draft.beta_send_hour <= 23
          ? ""
          : "Choose an hour from 0 to 23.";
      rules.beta_countdown_days = () =>
        normalized.beta_countdown_days.length === 3 &&
        normalized.beta_countdown_days.every(
          (n, i, a) =>
            Number.isInteger(n) && n >= 1 && n <= 60 && (!i || a[i - 1] > n),
        )
          ? ""
          : "Enter three different offsets, largest first, between 1 and 60.";
    }
    return rules;
  };
  const input = (key) => {
    if (toggles[key])
      return (
        <div key={key} className="runtime-toggle">
          <Switch
            label={toggles[key]}
            checked={Boolean(draft[key])}
            onChange={(_, d) => change(key, d.checked)}
          />
          <p
            role={
              errors.fieldProps(key).validationMessage ? "alert" : undefined
            }
          >
            {errors.fieldProps(key).validationMessage}
          </p>
        </div>
      );
    if (key === "assistant_suggestions")
      return (
        <Field
          key={key}
          label="Suggested questions"
          hint="One question per line, up to six."
          {...errors.fieldProps(key)}
        >
          <Textarea
            rows={5}
            value={suggestions}
            onChange={(_, d) => {
              setSuggestions(d.value);
              errors.clearError(key);
            }}
          />
        </Field>
      );
    if (key === "beta_countdown_days")
      return (
        <Field
          key={key}
          label="Countdown emails (days before opening)"
          hint="Three day offsets, for example 14, 7, 1."
          {...errors.fieldProps(key)}
        >
          <Input
            value={days}
            onChange={(_, d) => {
              setDays(d.value);
              errors.clearError(key);
            }}
          />
        </Field>
      );
    const approved =
      key === "email_from_address"
        ? ready.approved_email_senders
        : key === "sms_sender_id"
          ? ready.approved_sms_senders
          : null;
    if (approved?.length)
      return (
        <Field key={key} label={labels[key]} {...errors.fieldProps(key)}>
          <Select
            value={draft[key]}
            onChange={(e) => change(key, e.target.value)}
          >
            {key === "sms_sender_id" && (
              <option value="">Choose a sender</option>
            )}
            {approved.map((v) => (
              <option key={v} value={v}>
                {v}
              </option>
            ))}
          </Select>
        </Field>
      );
    const number = key === "email_daily_limit" || key === "beta_send_hour";
    const email = [
      "support_email",
      "email_from_address",
      "email_reply_to",
    ].includes(key);
    const length =
      {
        assistant_url: 500,
        assistant_title: 80,
        support_help_url: 500,
        support_phone: 40,
        support_whatsapp: 16,
        email_sender_name: 100,
        sms_sender_id: 20,
        whatsapp_template: 120,
        whatsapp_language: 6,
      }[key] || (email ? 254 : 120);
    return (
      <Field key={key} label={labels[key]} {...errors.fieldProps(key)}>
        <Input
          type={
            number
              ? "number"
              : key.endsWith("_date")
                ? "date"
                : email
                  ? "email"
                  : "text"
          }
          value={String(draft[key] ?? "")}
          min={number ? (key === "email_daily_limit" ? 1 : 0) : undefined}
          max={
            number
              ? key === "email_daily_limit"
                ? ready.email_daily_max
                : 23
              : undefined
          }
          placeholder={
            key === "assistant_url"
              ? "https://dwella.agents.handyagent.chat/agent"
              : undefined
          }
          maxLength={length}
          onChange={(_, d) =>
            change(
              key,
              number ? (d.value === "" ? "" : Number(d.value)) : d.value,
            )
          }
        />
      </Field>
    );
  };
  return (
    <form
      noValidate
      className="settings-stack"
      onSubmit={async (e) => {
        e.preventDefault();
        if (pending || !dirty || !errors.validate(validate(), e.currentTarget))
          return;
        try {
          await mutation.mutateAsync({
            resource: "runtime-settings",
            method: "patch",
            body: normalized,
          });
          toast.success("Settings saved.");
        } catch (error) {
          errors.showServerErrors(error.data, fields[section]);
        }
      }}
    >
      {(mutation.isError || checkError) && (
        <p role="alert" className="dwella-alert danger">
          {checkError ||
            mutation.error.message ||
            "Could not save settings. Your edits are kept."}
        </p>
      )}
      <fieldset disabled={pending} className="settings-fields">
        {groups[section].map(([title, note, keys]) => (
          <section key={title} className="settings-section">
            <header>
              <div>
                <h2>{title}</h2>
                <p>{note}</p>
              </div>
            </header>
            <div className="runtime-form-grid">{keys.map(input)}</div>
            {section === "assistant" && (
              <div className="runtime-check">
                <p>
                  {ready.assistant_configured
                    ? "Connection configured."
                    : "Save the address, verify HTTPS, then enable the assistant below."}
                </p>
                <Button
                  type="button"
                  disabled={pending || dirty || !draft.assistant_url}
                  onClick={async () => {
                    setCheckError("");
                    try {
                      await check.mutateAsync({
                        resource: "runtime-settings/assistant-check",
                      });
                      toast.success(
                        "HTTPS connection verified. No identity token was sent.",
                      );
                    } catch (error) {
                      setCheckError(
                        error.data?.assistant_url?.[0] ||
                          error.message ||
                          "Connection verification failed.",
                      );
                    }
                  }}
                >
                  {check.isPending ? "Checking…" : "Check saved connection"}
                </Button>
              </div>
            )}
            {section === "messaging" && title === "SMS" && (
              <p className="settings-note">
                Credentials:{" "}
                {ready.sms_credentials_configured
                  ? "Configured"
                  : "Awaiting server setup"}
                . Sender approval remains with Africa’s Talking.
              </p>
            )}
            {section === "messaging" && title === "WhatsApp Business" && (
              <p className="settings-note">
                Credentials:{" "}
                {ready.whatsapp_credentials_configured
                  ? "Configured"
                  : "Awaiting server setup"}
                .{" "}
                {ready.approved_whatsapp_templates.length
                  ? `Approved templates: ${ready.approved_whatsapp_templates.join(", ")}`
                  : "No templates approved for this environment yet."}
              </p>
            )}
          </section>
        ))}
      </fieldset>
      <footer className="settings-save">
        <span>Saving does not send messages or release old held requests.</span>
        <Button
          type="button"
          disabled={pending || !dirty}
          onClick={() => {
            setDraft(initial);
            setSuggestions((initial.assistant_suggestions || []).join("\n"));
            setDays((initial.beta_countdown_days || []).join(", "));
            errors.clearAll();
          }}
        >
          Discard
        </Button>
        <Button appearance="primary" type="submit" disabled={pending || !dirty}>
          {mutation.isPending ? "Saving…" : "Save changes"}
        </Button>
      </footer>
    </form>
  );
}
