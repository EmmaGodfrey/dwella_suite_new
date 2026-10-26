import React, { useState } from "react";
import { Link, Navigate, useSearchParams } from "react-router-dom";
import {
  Button,
  Field,
  Input,
  Switch,
  Tab,
  TabList,
  Textarea,
} from "@fluentui/react-components";
import { toast } from "react-toastify";
import { useCurrentUserQuery } from "../../Services/queries";
import { useSaveSettings, useSettingsResource } from "../../Services/settings";
import { getUserAccess } from "../../shared/access";
import { useFormErrors } from "../../shared/useFormErrors";
import { StatusBadge } from "../../shared/components";
import { AdminHeader, AdminState, when } from "../Platform/AdminUI";
import Profile from "../Profile";
import Security from "../Security";
import ReceivingDetails from "../Billing/ReceivingDetails";
import OutreachSettings from "../Outreach/Settings";
import AssistantSettings from "../Platform/Settings";
import "./settings.scss";

export function SettingsSection({ title, note, actions, children }) {
  return (
    <section className="settings-section">
      <header>
        <div>
          <h2>{title}</h2>
          {note && <p>{note}</p>}
        </div>
        {actions}
      </header>
      {children}
    </section>
  );
}

export function SettingsRow({ label, note, children }) {
  return (
    <div className="settings-row">
      <div>
        <strong>{label}</strong>
        {note && <small>{note}</small>}
      </div>
      <div>{children}</div>
    </div>
  );
}

function SavedForm({
  resource,
  data,
  children,
  validate,
  body = (value) => value,
}) {
  const initial = data.preferences || data;
  const [draft, setDraft] = useState(initial);
  const save = useSaveSettings(resource);
  const errors = useFormErrors();
  const change = (key, value) => {
    setDraft((v) => ({ ...v, [key]: value }));
    errors.clearError(key);
  };
  const dirty = JSON.stringify(draft) !== JSON.stringify(initial);
  return (
    <form
      noValidate
      onSubmit={async (event) => {
        event.preventDefault();
        if (
          save.isPending ||
          !dirty ||
          (validate && !errors.validate(validate(draft), event.currentTarget))
        )
          return;
        try {
          await save.mutateAsync(body(draft));
          toast.success("Settings saved.");
        } catch (error) {
          errors.showServerErrors(error.data, Object.keys(draft));
        }
      }}
    >
      {save.isError && (
        <p className="dwella-alert danger" role="alert">
          {save.error.message ||
            "Changes could not be saved. Your edits are kept."}
        </p>
      )}
      <fieldset disabled={save.isPending} className="settings-fields">
        {children({ draft, change, errors })}
      </fieldset>
      <footer className="settings-save">
        <span>Saving preferences never sends a message.</span>
        <Button
          disabled={save.isPending || !dirty}
          onClick={() => {
            setDraft(initial);
            errors.clearAll();
          }}
        >
          Discard
        </Button>
        <Button
          appearance="primary"
          type="submit"
          disabled={save.isPending || !dirty}
        >
          {save.isPending ? "Saving…" : "Save changes"}
        </Button>
      </footer>
    </form>
  );
}

const channelNames = { email: "Email", sms: "SMS", whatsapp: "WhatsApp" };
function ChannelRows({ draft, change, channels }) {
  return Object.entries(channelNames).map(([key, label]) => (
    <SettingsRow
      key={key}
      label={label}
      note={
        key === "whatsapp"
          ? "Requires recipient opt-in and approved reminder templates."
          : undefined
      }
    >
      <>
        <Switch
          aria-label={`${label} reminders`}
          checked={draft[`${key}_enabled`]}
          onChange={(_, d) => change(`${key}_enabled`, d.checked)}
        />
      {!channels[key] && (
        <>
          <StatusBadge color="subtle">Awaiting connection</StatusBadge>
          <span className="settings-inline-note">
            Preference saved. Reminders start once this channel is connected.
          </span>
        </>
      )}
      </>
    </SettingsRow>
  ));
}

function Notifications({ persona }) {
  const personal = useSettingsResource("personal");
  const reminders = useSettingsResource("reminders", {
    enabled: persona === "landlord",
  });
  const query =
    persona === "landlord" && (reminders.isPending || reminders.isError)
      ? reminders
      : personal;
  return (
    <AdminState query={query}>
      {personal.data && (persona !== "landlord" || reminders.data) && (
        <NotificationForm
          persona={persona}
          personal={personal.data}
          reminders={reminders.data}
        />
      )}
    </AdminState>
  );
}

const scheduleFields = [
  ["before_due_days", "Days before rent is due", 0, 30],
  ["due_hour", "Due-date hour (0–23)", 0, 23],
  ["overdue_every_days", "Days between overdue reminders", 1, 30],
  ["overdue_repeats", "Maximum overdue reminders", 0, 3],
];

function NotificationForm({ persona, personal, reminders }) {
  const initial = {
    personal: personal.preferences,
    reminders: reminders?.preferences,
  };
  const [draft, setDraft] = useState(initial);
  const [saved, setSaved] = useState(initial);
  const [notice, setNotice] = useState("");
  const savePersonal = useSaveSettings("personal");
  const saveReminders = useSaveSettings("reminders");
  const errors = useFormErrors();
  const busy = savePersonal.isPending || saveReminders.isPending;
  const dirty = JSON.stringify(draft) !== JSON.stringify(saved);
  const change = (section, key, value) => {
    setDraft((v) => ({ ...v, [section]: { ...v[section], [key]: value } }));
    errors.clearError(key);
    setNotice("");
  };
  return (
    <form
      className="settings-stack"
      noValidate
      onSubmit={async (event) => {
        event.preventDefault();
        if (busy || !dirty) return;
        if (
          draft.reminders &&
          !errors.validate(
            Object.fromEntries(
              scheduleFields.map(([key, , min, max]) => [
                key,
                () =>
                  Number.isInteger(draft.reminders[key]) &&
                  draft.reminders[key] >= min &&
                  draft.reminders[key] <= max
                    ? ""
                    : `Enter ${min}–${max}.`,
              ]),
            ),
            event.currentTarget,
          )
        )
          return;
        const changes = [
          ["personal", savePersonal],
          ["reminders", saveReminders],
        ].filter(
          ([key]) =>
            draft[key] &&
            JSON.stringify(draft[key]) !== JSON.stringify(saved[key]),
        );
        const results = await Promise.allSettled(
          changes.map(([key, mutation]) => mutation.mutateAsync(
            Object.fromEntries(Object.entries(draft[key]).filter(
              ([field, value]) => value !== saved[key][field],
            )),
          )),
        );
        const successful = {};
        let failed = false;
        results.forEach((result, i) => {
          const key = changes[i][0];
          if (result.status === "fulfilled") successful[key] = draft[key];
          else {
            failed = true;
            errors.showServerErrors(
              result.reason.data,
              Object.keys(draft[key]),
            );
          }
        });
        setSaved((v) => ({ ...v, ...successful }));
        if (failed)
          setNotice(
            "Some preferences could not be saved. Your remaining edits are kept; try saving again.",
          );
        else {
          setNotice("");
          toast.success("Notification preferences saved.");
        }
      }}
    >
      {notice && (
        <p role="alert" className="dwella-alert danger">
          {notice}
        </p>
      )}
      <fieldset disabled={busy} className="settings-fields">
        {draft.reminders && (
          <>
            <SettingsSection
              title="Tenant reminders"
              note="Channels Dwella uses to remind tenants about rent. Recipient preferences and consent also apply."
            >
              <ChannelRows
                draft={draft.reminders}
                change={(key, value) => change("reminders", key, value)}
                channels={reminders.channels}
              />
            </SettingsSection>
            <SettingsSection
              title="Reminder schedule"
              note="Save your preferred schedule now. Automatic delivery is not connected yet; these settings do not activate reminders."
            >
              <div className="dwella-form-grid">
                {scheduleFields.map(([key, label, min, max]) => (
                  <Field key={key} label={label} {...errors.fieldProps(key)}>
                    <Input
                      type="number"
                      min={min}
                      max={max}
                      value={String(draft.reminders[key])}
                      onChange={(_, d) =>
                        change(
                          "reminders",
                          key,
                          d.value === "" ? "" : Number(d.value),
                        )
                      }
                    />
                  </Field>
                ))}
              </div>
            </SettingsSection>
          </>
        )}
        <SettingsSection
          title="My alerts"
          note="These preferences control your own in-app alerts. Overdue invoice notices remain visible."
        >
          {[
            ["payment", persona === "tenant" ? "Payment notices" : "Payment received"],
            ["payout", "Payout needs attention"],
            ["lease", persona === "tenant" ? "Lease updates" : "Lease ending"],
            ["maintenance", "Maintenance updates"],
          ].filter(([key]) => persona !== "tenant" || key !== "payout").map(([key, label]) => (
            <SettingsRow label={label} key={key}>
              <Switch
                aria-label={label}
                checked={draft.personal[`in_app_${key}`]}
                onChange={(_, d) =>
                  change("personal", `in_app_${key}`, d.checked)
                }
              />
            </SettingsRow>
          ))}
        </SettingsSection>
        <SettingsSection
          title={persona === "tenant" ? "Rent reminders" : "Delivery channels"}
          note="Enable SMS or WhatsApp and save to agree to rent reminders and property notices from Dwella at your linked phone number. Disable either channel here to opt out. You can also reply STOP on WhatsApp."
        >
          <ChannelRows
            draft={draft.personal}
            change={(key, value) => change("personal", key, value)}
            channels={personal.channels}
          />
        </SettingsSection>
      </fieldset>
      <footer className="settings-save">
        <span>Saving preferences never sends a message.</span>
        <Button
          disabled={busy || !dirty}
          onClick={() => {
            setDraft(saved);
            errors.clearAll();
            setNotice("");
          }}
        >
          Discard
        </Button>
        <Button appearance="primary" type="submit" disabled={busy || !dirty}>
          {busy ? "Saving…" : "Save changes"}
        </Button>
      </footer>
    </form>
  );
}

function Workspace() {
  const query = useSettingsResource("workspace");
  return (
    <AdminState query={query}>
      {query.data && (
        <SavedForm
          resource="workspace"
          data={query.data}
          key={JSON.stringify(query.data)}
          body={({ currency, ...values }) => values}
          validate={(v) => ({
            email: () =>
              !v.email || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.email)
                ? ""
                : "Enter a valid email address.",
            phone_number: () =>
              !v.phone_number || /^\+?[0-9 ()-]{7,40}$/.test(v.phone_number)
                ? ""
                : "Enter a valid phone number.",
            timezone: () => {
              try {
                Intl.DateTimeFormat("en", { timeZone: v.timezone });
                return "";
              } catch {
                return "Choose a valid time zone.";
              }
            },
          })}
        >
          {({ draft, change, errors }) => (
            <>
              <SettingsSection
                title="Workspace details"
                note="How your business appears to tenants."
              >
                <div className="dwella-form-grid">
                  {[
                    ["display_name", "Display name", 180],
                    ["email", "Contact email", 254],
                    ["phone_number", "Contact phone", 40],
                    ["town", "Town", 120],
                    ["country", "Country", 80],
                  ].map(([key, label, max]) => (
                    <Field label={label} key={key} {...errors.fieldProps(key)}>
                      <Input
                        value={draft[key]}
                        maxLength={max}
                        onChange={(_, d) => change(key, d.value)}
                      />
                    </Field>
                  ))}
                  <Field label="Address" {...errors.fieldProps("address")}>
                    <Textarea
                      value={draft.address}
                      maxLength={2000}
                      onChange={(_, d) => change("address", d.value)}
                    />
                  </Field>
                </div>
              </SettingsSection>
              <SettingsSection
                title="Regional defaults"
                note="Times for this workspace use its selected time zone."
              >
                <SettingsRow label="Currency">{draft.currency}</SettingsRow>
                <Field label="Time zone" {...errors.fieldProps("timezone")}>
                  <Input
                    value={draft.timezone}
                    maxLength={80}
                    placeholder="Africa/Lusaka"
                    onChange={(_, d) => change("timezone", d.value)}
                  />
                </Field>
              </SettingsSection>
            </>
          )}
        </SavedForm>
      )}
    </AdminState>
  );
}

function Messaging() {
  const query = useSettingsResource("messaging");
  return (
    <AdminState query={query}>
      {query.data && (
        <SavedForm
          resource="messaging"
          data={query.data}
          key={JSON.stringify(query.data)}
          validate={(v) => ({
            quiet_from: () =>
              /^([01]\d|2[0-3]):[0-5]\d/.test(v.quiet_from || "")
                ? ""
                : "Choose a valid start time.",
            quiet_until: () =>
              !/^([01]\d|2[0-3]):[0-5]\d/.test(v.quiet_until || "")
                ? "Choose a valid ending time."
                : v.quiet_from.slice(0, 5) !== v.quiet_until.slice(0, 5)
                  ? ""
                  : "Choose a different ending time.",
          })}
        >
          {({ draft, change, errors }) => (
            <>
              <SettingsSection
                title="Email"
                note="Account emails, signing emails and reminders share the sending allowance."
              >
                <SettingsRow label="Routing">
                  {query.data.providers?.email.routing_enabled
                    ? `Google up to ${query.data.providers.email.google_limit} recipients, then Resend`
                    : "Existing email service; automatic routing awaits setup"}
                </SettingsRow>
                <SettingsRow label="Resend">
                  {query.data.providers?.email.resend_configured ? "Configured" : "Awaiting API key and verified sending domain"}
                </SettingsRow>
              </SettingsSection>
              {["SMS", "WhatsApp Business"].map((name) => (
                <SettingsSection
                  key={name}
                  title={name}
                  note={
                    name === "SMS"
                      ? "Rent reminders and on-demand text messages."
                      : "Business-initiated reminders need recipient opt-in and approved templates."
                  }
                >
                  <SettingsRow label="Connection">
                    <StatusBadge color="subtle">
                      {query.data.channels?.[name === "SMS" ? "sms" : "whatsapp"]
                        ? "Connected" : "Awaiting setup"}
                    </StatusBadge>
                  </SettingsRow>
                  <SettingsRow label="Provider">
                    {name === "SMS" ? "Africa’s Talking" : "Meta Cloud API"}
                  </SettingsRow>
                  <p className="settings-note">
                    {name === "SMS"
                      ? "Sender registration and provider setup are pending."
                      : "Rent reminders use an approved template. Custom notices require a tenant reply within the last 24 hours."}
                  </p>
                </SettingsSection>
              ))}
              <SettingsSection
                title="Sending controls"
                note="No messages are sent from this page."
              >
                <SettingsRow label="Automated reminders">
                  <Switch
                    label="Schedule reminders on connected channels"
                    checked={draft.reminders_enabled}
                    onChange={(_, data) => change("reminders_enabled", data.checked)}
                  />
                </SettingsRow>
                <div className="dwella-form-grid">
                  {[
                    ["quiet_from", "Quiet hours from"],
                    ["quiet_until", "Quiet hours until"],
                  ].map(([key, label]) => (
                    <Field label={label} key={key} {...errors.fieldProps(key)}>
                      <Input
                        type="time"
                        value={draft[key]?.slice(0, 5)}
                        onChange={(_, d) => change(key, d.value)}
                        required
                      />
                    </Field>
                  ))}
                </div>
                <p className="settings-note">
                  Quiet hours use each workspace’s time zone. Email is limited
                  to a daily allowance; messages over it wait in the queue.
                </p>
              </SettingsSection>
            </>
          )}
        </SavedForm>
      )}
    </AdminState>
  );
}

function PaymentSettings() {
  const query = useSettingsResource("payments");
  const balance = useSettingsResource("balance");
  const data = query.data;
  return (
    <AdminState query={query}>
      {data && (
        <div className="settings-stack">
          <SettingsSection
            title="Payment gateway"
            note="Lenco handles tenant collections and landlord payouts."
            actions={
              <Button as={Link} to="/admin/transactions">
                View transactions
              </Button>
            }
          >
            <SettingsRow label="Gateway">{data.gateway}</SettingsRow>
            <SettingsRow label="Environment">
              <StatusBadge color="informative">{data.environment}</StatusBadge>
            </SettingsRow>
            <SettingsRow label="Collections">
              <StatusBadge
                color={data.collections_enabled ? "success" : "subtle"}
              >
                {data.collections_enabled ? "Enabled" : "Disabled"}
              </StatusBadge>
            </SettingsRow>
            <SettingsRow label="Payouts">
              <StatusBadge color={data.payouts_enabled ? "success" : "subtle"}>
                {data.payouts_enabled ? "Enabled" : "Disabled"}
              </StatusBadge>
            </SettingsRow>
            <SettingsRow label="Balance comparison">
              {balance.isError
                ? "Could not load"
                : balance.isPending
                  ? "Loading…"
                  : balance.data?.status?.replaceAll("_", " ") || "Not synced"}
            </SettingsRow>
          </SettingsSection>
          <SettingsSection
            title="Connection and access"
            note="Connection settings are managed on the server. Credentials never appear here."
          >
            <SettingsRow label="API credentials">
              {data.api_configured ? "Configured" : "Not configured"}
            </SettingsRow>
            <SettingsRow label="Platform receiving account">
              {data.account_configured ? "Configured" : "Not configured"}
            </SettingsRow>
            <SettingsRow label="Latest saved webhook">
              {when(data.last_webhook_at)}
            </SettingsRow>
          </SettingsSection>
        </div>
      )}
    </AdminState>
  );
}

export default function Settings() {
  const user = useCurrentUserQuery();
  const [params, setParams] = useSearchParams();
  const persona = getUserAccess(user.data).persona;
  const admin = persona === "platform_admin";
  const tabs = admin
    ? ["account", "security", "payments", "messaging", "outreach", "assistant"]
    : persona === "landlord"
      ? ["account", "workspace", "billing", "notifications", "security"]
      : ["account", "notifications", "security"];
  const tab = tabs.includes(params.get("tab")) ? params.get("tab") : "account";
  if (user.isPending) return <AdminState query={user} />;
  if (user.isError) return <AdminState query={user} />;
  return (
    <div className="dwella-settings admin-screen">
      <AdminHeader
        title="Settings"
        description={
          admin
            ? "Manage your account and platform configuration."
            : "Manage your account, workspace and preferences."
        }
      />
      <TabList
        selectedValue={tab}
        onTabSelect={(_, d) => setParams({ tab: d.value })}
        className="settings-tabs"
        aria-label="Settings sections"
      >
        {tabs.map((key) => (
          <Tab key={key} value={key}>
            {key[0].toUpperCase() + key.slice(1)}
          </Tab>
        ))}
      </TabList>
      <div key={tab} className="settings-content">
        {tab === "account" && (
          <>
            <Profile />
            {admin && <Notifications persona={persona} />}
          </>
        )}
        {tab === "security" && <Security />}
        {tab === "workspace" && <Workspace />}
      {tab === "billing" && <ReceivingDetails />}
        {tab === "notifications" && <Notifications persona={persona} />}
        {tab === "payments" && <PaymentSettings />}
        {tab === "messaging" && <Messaging />}
        {tab === "outreach" && <OutreachSettings embedded />}
        {tab === "assistant" && <AssistantSettings embedded />}
      </div>
    </div>
  );
}

export function LegacySettings({ tab }) {
  return <Navigate to={`/settings?tab=${tab}`} replace />;
}
