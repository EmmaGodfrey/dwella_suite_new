import React, { useState } from "react";
import { Button, Checkbox, Field, Input, Radio, RadioGroup } from "@fluentui/react-components";
import { useConnectNotificationPhone, useNotificationPhone } from "../../Services/settings";
import { useFormErrors } from "../../shared/useFormErrors";
import { SettingsRow, SettingsSection } from "./index";

export default function NotificationPhone() {
  const query = useNotificationPhone();
  const connect = useConnectNotificationPhone();
  const [phone, setPhone] = useState("");
  const [channel, setChannel] = useState("whatsapp");
  const [consent, setConsent] = useState(false);
  const [challenge, setChallenge] = useState(null);
  const [notice, setNotice] = useState("");
  const errors = useFormErrors();

  async function submit(event) {
    event.preventDefault();
    setNotice("");
    if (!errors.validate({
      phone: () => /^\+?[0-9 ()-]{9,24}$/.test(phone) ? "" : "Enter your WhatsApp or SMS number.",
      consent: () => consent ? "" : "Agree to optional notifications to connect this number.",
    }, event.currentTarget)) return;
    try {
      setChallenge(await connect.mutateAsync({ phone, channel, consent }));
    } catch (error) {
      errors.showServerErrors(error.data, ["phone", "consent", "channel"]);
      setNotice(error.message || "Could not connect this number.");
    }
  }

  async function complete(link) {
    try {
      await connect.mutateAsync({ channel: link.channel, complete: link.id });
      setChallenge(null);
      setNotice("Number verified. Optional notifications are enabled.");
    } catch (error) {
      setNotice(error.message || "Could not complete verification.");
    }
  }

  return (
    <SettingsSection title="Optional phone notifications"
      note="Verify a number you control. This adds notifications alongside required email; it does not change your payment wallet.">
      {query.data?.links?.map((link) => (
        <SettingsRow key={`${link.channel}:${link.phone}`} label={link.phone}
          note={`${link.channel === "whatsapp" ? "WhatsApp" : "SMS"} · ${link.allowed ? "Connected" : "Opted out"}`} />
      ))}
      {query.isError && <p role="alert">Could not load connected numbers. <Button onClick={() => query.refetch()}>Retry</Button></p>}
      <form onSubmit={submit}>
        <fieldset disabled={connect.isPending} className="settings-fields">
          <Field label="Channel">
            <RadioGroup layout="horizontal" value={channel} onChange={(_, data) => setChannel(data.value)}>
              <Radio value="whatsapp" label="WhatsApp" /><Radio value="sms" label="SMS" />
            </RadioGroup>
          </Field>
          <Field label="Your phone number" validationMessage={errors.errors.phone}>
            <Input name="phone" type="tel" autoComplete="tel" value={phone}
              onChange={(_, data) => { setPhone(data.value); errors.clearError("phone"); }} />
          </Field>
          <Field validationMessage={errors.errors.consent}>
            <Checkbox label="I agree to optional Dwella notifications on this number."
              checked={consent} onChange={(_, data) => setConsent(Boolean(data.checked))} />
          </Field>
          <Button type="submit" disabled={connect.isPending}>Verify number</Button>
        </fieldset>
      </form>
      {challenge && <div role="status">
        <p>From {phone}, send <strong>{challenge.message}</strong> to {challenge.destination}. The code expires in 10 minutes.</p>
        {channel === "whatsapp" && <a target="_blank" rel="noreferrer"
          href={`https://wa.me/${challenge.destination.replace(/\D/g, "")}?text=${encodeURIComponent(challenge.message)}`}>
          Open WhatsApp
        </a>}
        <p>Then return here to complete the connection.</p>
      </div>}
      {query.data?.pending?.filter((link) => link.verified_at).map((link) => (
        <SettingsRow key={link.id} label={`Confirm ${link.phone}`}>
          <Button disabled={connect.isPending} onClick={() => complete(link)}>Complete connection</Button>
        </SettingsRow>
      ))}
      {notice && <p role="status">{notice}</p>}
    </SettingsSection>
  );
}
