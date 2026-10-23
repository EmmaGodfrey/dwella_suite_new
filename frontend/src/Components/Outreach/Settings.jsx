import React, { useState } from "react";
import {
  Button,
  Field,
  Input,
  Switch,
  Textarea,
} from "@fluentui/react-components";
import { toast } from "react-toastify";
import { useOutreachList, useOutreachMutation } from "../../Services/outreach";
import { useFormErrors } from "../../shared/useFormErrors";
import { AdminHeader, AdminState } from "../Platform/AdminUI";
import { ErrorText, OutreachTabs } from "./OutreachUI";
import "./outreach.scss";

function SettingsForm({ settings }) {
  const [draft, setDraft] = useState(settings);
  const mutation = useOutreachMutation();
  const errors = useFormErrors();
  const change = (key, value) => {
    setDraft({ ...draft, [key]: value });
    errors.clearError(key);
  };
  return (
    <form
      className="admin-card outreach-form outreach-settings"
      noValidate
      onSubmit={async (e) => {
        e.preventDefault();
        if (mutation.isPending) return;
        const cap = Number(draft.daily_cap),
          start = Number(draft.send_from_hour),
          end = Number(draft.send_until_hour);
        if (
          !errors.validate(
            {
              daily_cap: () =>
                Number.isInteger(cap) && cap >= 1 && cap <= 25
                  ? ""
                  : "Choose 1–25 emails per day.",
              send_from_hour: () =>
                Number.isInteger(start) && start >= 8 && start <= 16
                  ? ""
                  : "Start between 08:00 and 16:00.",
              send_until_hour: () =>
                Number.isInteger(end) && end > start && end <= 17
                  ? ""
                  : "End after start, by 17:00.",
            },
            e.currentTarget,
          )
        )
          return;
        try {
          await mutation.mutateAsync({
            resource: "settings",
            method: "patch",
            body: {
              ...Object.fromEntries(
                [
                  "sender_name",
                  "sender_first_name",
                  "signature",
                  "signature_short",
                  "offer",
                  "paused",
                ].map((key) => [key, draft[key]]),
              ),
              daily_cap: cap,
              send_from_hour: start,
              send_until_hour: end,
            },
          });
          toast.success("Outreach settings saved.");
        } catch (error) {
          errors.showServerErrors(error.data, Object.keys(draft));
        }
      }}
    >
      <fieldset
        disabled={mutation.isPending}
        className="outreach-settings-fields"
      >
        <h2>Sender identity</h2>
        <p className="admin-note">
          Sender mailbox: {settings.from_address || "Not configured"}.{" "}
          {settings.enabled
            ? "Outreach is enabled on this server."
            : "Outreach sending is disabled on this server."}
        </p>
        <div className="dwella-form-grid">
          {[
            ["sender_name", "Sender display name", 150],
            ["sender_first_name", "Sender first name", 80],
          ].map(([key, label, max]) => (
            <Field key={key} label={label} {...errors.fieldProps(key)}>
              <Input
                value={draft[key]}
                maxLength={max}
                onChange={(_, d) => change(key, d.value)}
              />
            </Field>
          ))}
        </div>
        <div className="dwella-form-grid">
          <Field label="Signature" {...errors.fieldProps("signature")}>
            <Textarea
              value={draft.signature}
              rows={3}
              maxLength={2000}
              onChange={(_, d) => change("signature", d.value)}
            />
          </Field>
          <Field
            label="Short signature"
            {...errors.fieldProps("signature_short")}
          >
            <Textarea
              value={draft.signature_short}
              rows={3}
              maxLength={500}
              onChange={(_, d) => change("signature_short", d.value)}
            />
          </Field>
        </div>
        <Field
          label="Influencer partnership offer"
          {...errors.fieldProps("offer")}
        >
          <Textarea
            value={draft.offer}
            rows={3}
            maxLength={2000}
            onChange={(_, d) => change("offer", d.value)}
          />
        </Field>
        <h2>Sending limits</h2>
        <div className="outreach-setting-limits">
          {[
            ["daily_cap", "Daily cap", 1, 25],
            ["send_from_hour", "From hour (Lusaka)", 8, 16],
            ["send_until_hour", "Until hour (Lusaka)", 9, 17],
          ].map(([key, label, min, max]) => (
            <Field key={key} label={label} {...errors.fieldProps(key)}>
              <Input
                type="number"
                min={min}
                max={max}
                value={String(draft[key])}
                onChange={(_, d) => change(key, d.value)}
              />
            </Field>
          ))}
        </div>
        <p className="admin-note">
          Monday–Friday · Africa/Lusaka. First emails always require review.
        </p>
        <Switch
          label="Pause all outreach sending"
          checked={draft.paused}
          onChange={(_, d) => change("paused", d.checked)}
        />
        <Button type="submit" appearance="primary" disabled={mutation.isPending}>
          Save changes
        </Button>
        <ErrorText error={mutation.error} />
      </fieldset>
    </form>
  );
}
export default function Settings() {
  const query = useOutreachList("settings");
  return (
    <div className="admin-screen outreach-screen">
      <AdminHeader
        title="Outreach settings"
        description="Set the sender identity, signature and sending limits."
      />
      <OutreachTabs />
      <AdminState query={query}>
        {query.data && (
          <SettingsForm
            key={query.data.updated_at || "settings"}
            settings={query.data}
          />
        )}
      </AdminState>
    </div>
  );
}
