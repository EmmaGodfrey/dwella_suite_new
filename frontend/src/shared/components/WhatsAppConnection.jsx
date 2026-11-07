import React, { useEffect, useState } from "react";
import { Button, Checkbox, Field, Input } from "@fluentui/react-components";
import { useConnectNotificationPhone, useDisconnectWhatsApp, useNotificationPhone } from "../../Services/settings";
import { useFormErrors } from "../useFormErrors";
import "./whatsappConnection.scss";

export default function WhatsAppConnection({ onboarding = false }) {
  const query = useNotificationPhone();
  const connect = useConnectNotificationPhone();
  const disconnect = useDisconnectWhatsApp();
  const [phone, setPhone] = useState("");
  const [consent, setConsent] = useState(false);
  const [challenge, setChallenge] = useState(null);
  const [checking, setChecking] = useState(false);
  const [notice, setNotice] = useState("");
  const [failure, setFailure] = useState("");
  const [now, setNow] = useState(Date.now());
  const errors = useFormErrors();
  const connected = query.data?.whatsapp_binding;
  const destination = typeof query.data?.whatsapp_destination === "string"
    ? query.data.whatsapp_destination.replace(/\D/g, "") : "";
  const available = /^[1-9]\d{7,14}$/.test(destination);
  const busy = connect.isPending || disconnect.isPending || checking;
  const challengeDestination = challenge?.destination?.replace(/\D/g, "") || "";
  const chatLink = /^[1-9]\d{7,14}$/.test(challengeDestination)
    ? `https://wa.me/${challengeDestination}?text=${encodeURIComponent(challenge.message)}` : "";
  const expired = challenge && Date.parse(challenge.expires_at) <= now;
  useEffect(() => {
    if (!challenge) return;
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, [challenge]);

  async function requestConnection(event) {
    event?.preventDefault();
    if (busy || !available) return;
    const targetPhone = challenge?.phone || phone;
    if (!errors.validate({
      phone: () => /^\+?[0-9 ()-]{9,24}$/.test(targetPhone) ? "" : "Enter a valid phone number, including its country code.",
    }, event?.currentTarget)) return;
    setFailure("");
    setNotice("");
    try {
      const result = await connect.mutateAsync({ channel: "whatsapp", phone: targetPhone, consent, actions: true });
      setChallenge({ ...result, phone: targetPhone });
      setNow(Date.now());
      connect.reset();
    } catch (error) {
      if (!errors.showServerErrors(error.data, ["phone"]))
        setFailure(error.message || "Could not start your connection. Please try again.");
      connect.reset();
    }
  }

  async function confirmConnection(event) {
    event.preventDefault();
    if (busy || !challenge || Date.parse(challenge.expires_at) <= Date.now()) return;
    setFailure("");
    setNotice("");
    setChecking(true);
    try {
      const result = await query.refetch();
      if (result.isError) throw new Error("Could not check your message. Please try again.");
      if (!result.data?.pending?.some(link => link.id === challenge.id && link.verified_at)) {
        setNotice("We haven't received your connection message yet. Send it from the number you entered, then check again.");
        return;
      }
      await connect.mutateAsync({ channel: "whatsapp", complete: challenge.id, actions: true });
      setChallenge(null);
      setNotice("WhatsApp connected. You can now open our chat and choose Menu.");
    } catch (error) {
      setFailure(error.message || "Could not complete your connection. Please try again.");
    } finally {
      setChecking(false);
      connect.reset();
    }
  }

  return (
    <section className={`dwella-whatsapp-connection${onboarding ? "" : " settings-section"}`} aria-labelledby={`whatsapp-title-${onboarding ? "setup" : "settings"}`}>
      <header>
        <h2 id={`whatsapp-title-${onboarding ? "setup" : "settings"}`}>Connect WhatsApp {onboarding && <span className="dwella-muted-copy">(optional)</span>}</h2>
        <p>Get invoices, receipts and updates, and use Dwella from your phone. Send a prefilled WhatsApp message to connect your number.</p>
      </header>
      {query.isLoading ? <p role="status">Loading your WhatsApp connection…</p> : query.isError ? (
        <p role="alert">Could not load your connection. <Button onClick={() => query.refetch()}>Retry</Button></p>
      ) : connected ? (
        <div className="dwella-whatsapp-connected">
          <div><strong>{connected.phone}</strong><p>Connected · {query.data.links?.some(link => link.channel === "whatsapp" && link.phone === connected.phone && link.allowed) ? "Optional notices enabled" : "Optional notices off"}</p></div>
          {/^[1-9]\d{7,14}$/.test(destination) && <Button as="a" href={`https://wa.me/${destination}?text=MENU`} target="_blank" rel="noreferrer">Open Dwella on WhatsApp</Button>}
          <Button disabled={busy} onClick={async () => {
            setFailure("");
            try {
              await disconnect.mutateAsync();
              setChallenge(null);
              setNotice("WhatsApp disconnected. Access and optional notices are disabled.");
            } catch (error) { setFailure(error.message || "Could not disconnect WhatsApp."); }
          }}>Disconnect</Button>
        </div>
      ) : !available ? (
        <p>WhatsApp is not connected yet. You can finish setup and connect later from Settings → Notifications.</p>
      ) : challenge ? (
        <form onSubmit={confirmConnection} noValidate>
          <p>Open WhatsApp and send the prefilled message from <strong>{challenge.phone}</strong>. Then return here to finish connecting. The message expires in 10 minutes.</p>
          <Field label="Connection message">
            <Input name="connection-message" value={challenge.message} readOnly autoComplete="off" />
          </Field>
          {expired && <p role="alert">This connection message has expired. Start again to get a new one.</p>}
          <div className="dwella-whatsapp-actions">
            {chatLink && !expired && <Button as="a" href={chatLink} target="_blank" rel="noreferrer" appearance="primary">Open WhatsApp</Button>}
            <Button type="submit" disabled={busy || expired}>{checking || connect.isPending ? "Checking…" : "I've sent the message"}</Button>
            <Button type="button" appearance="subtle" disabled={busy} onClick={() => { setPhone(challenge.phone); setChallenge(null); setFailure(""); setNotice(""); connect.reset(); }}>{expired ? "Start again" : "Change number"}</Button>
          </div>
          <p className="dwella-muted-copy">Send the message exactly as shown to Dwella. Do not share it with anyone else.</p>
        </form>
      ) : (
        <form onSubmit={requestConnection} noValidate>
          <Field label="Your WhatsApp number" {...errors.fieldProps("phone")}>
            <Input name="phone" type="tel" autoComplete="tel" maxLength={24} placeholder="e.g. +260 97 123 4567" value={phone}
              disabled={busy} onChange={(_, data) => { setPhone(data.value); errors.clearError("phone"); }} />
          </Field>
          <Checkbox label="Send me optional Dwella notifications on WhatsApp." checked={consent}
            disabled={busy} onChange={(_, data) => setConsent(Boolean(data.checked))} />
          <p className="dwella-muted-copy">Connecting verifies your number. Notifications are optional; you can turn them off in Settings or send STOP.</p>
          <Button type="submit" appearance="primary" disabled={busy}>{connect.isPending ? "Preparing…" : "Connect WhatsApp"}</Button>
        </form>
      )}
      {failure && <p role="alert" className="dwella-alert danger">{failure}</p>}
      {notice && <p role="status">{notice}</p>}
      {onboarding && <p className="dwella-muted-copy">This is optional and does not affect your workspace setup.</p>}
    </section>
  );
}
