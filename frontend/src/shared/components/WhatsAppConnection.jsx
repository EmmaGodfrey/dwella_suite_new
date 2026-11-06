import React, { useEffect, useState } from "react";
import { Button, Checkbox, Field, Input } from "@fluentui/react-components";
import { useDisconnectWhatsApp, useNotificationPhone, useWhatsAppVerification } from "../../Services/settings";
import { useFormErrors } from "../useFormErrors";
import "./whatsappConnection.scss";

export default function WhatsAppConnection({ onboarding = false }) {
  const query = useNotificationPhone();
  const verify = useWhatsAppVerification();
  const disconnect = useDisconnectWhatsApp();
  const [phone, setPhone] = useState("");
  const [consent, setConsent] = useState(false);
  const [challenge, setChallenge] = useState(null);
  const [code, setCode] = useState("");
  const [notice, setNotice] = useState("");
  const [failure, setFailure] = useState("");
  const [retryAt, setRetryAt] = useState(0);
  const [now, setNow] = useState(Date.now());
  const errors = useFormErrors();
  const connected = query.data?.whatsapp_binding;
  const destination = typeof query.data?.whatsapp_destination === "string"
    ? query.data.whatsapp_destination.replace(/\D/g, "") : "";
  const available = query.data?.whatsapp_verification_available;
  const busy = verify.isPending || disconnect.isPending;
  const remaining = Math.max(0, Math.ceil((retryAt - now) / 1000));
  const expired = challenge && Date.parse(challenge.expires_at) <= now;
  useEffect(() => {
    if (!challenge && !retryAt) return;
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, [challenge, retryAt]);

  async function requestCode(event) {
    event?.preventDefault();
    if (busy || remaining || !available) return;
    const targetPhone = challenge?.phone || phone;
    if (!errors.validate({
      phone: () => /^\+?[0-9 ()-]{9,24}$/.test(targetPhone) ? "" : "Enter a valid phone number, including its country code.",
    }, event?.currentTarget)) return;
    setFailure("");
    setNotice("");
    try {
      const result = await verify.mutateAsync({ phone: targetPhone, consent });
      setChallenge(result);
      setCode("");
      setNow(Date.now());
      setRetryAt(Date.now() + result.retry_after * 1000);
    } catch (error) {
      if (!errors.showServerErrors(error.data, ["phone"]))
        setFailure(error.message || "Could not request a code. Please try again.");
      verify.reset();
    }
  }

  async function confirmCode(event) {
    event.preventDefault();
    if (busy || expired || !challenge) return;
    if (!errors.validate({ code: () => /^\d{6}$/.test(code) ? "" : "Enter the six-digit code from WhatsApp." }, event.currentTarget)) return;
    setFailure("");
    try {
      await verify.mutateAsync({ complete: challenge.id, code });
      setChallenge(null);
      setCode("");
      setRetryAt(0);
      setNotice("WhatsApp connected. You can now open our chat and choose Menu.");
      verify.reset();
    } catch (error) {
      if (!errors.showServerErrors(error.data, ["code"]))
        setFailure(error.message || "Could not verify this code. Please try again.");
      verify.reset();
    }
  }

  return (
    <section className={`dwella-whatsapp-connection${onboarding ? "" : " settings-section"}`} aria-labelledby={`whatsapp-title-${onboarding ? "setup" : "settings"}`}>
      <header>
        <h2 id={`whatsapp-title-${onboarding ? "setup" : "settings"}`}>Connect WhatsApp {onboarding && <span className="dwella-muted-copy">(optional)</span>}</h2>
        <p>Get invoices, receipts and updates, and use Dwella from your phone. We send you a code; enter it here to connect.</p>
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
              setCode("");
              setNotice("WhatsApp disconnected. Access and optional notices are disabled.");
            } catch (error) { setFailure(error.message || "Could not disconnect WhatsApp."); }
          }}>Disconnect</Button>
        </div>
      ) : !available ? (
        <p>WhatsApp verification is being connected. You can finish setup and connect later from Settings → Notifications.</p>
      ) : challenge ? (
        <form onSubmit={confirmCode} noValidate>
          <p role="status">Check WhatsApp on <strong>{challenge.phone}</strong> for your verification code. It expires in 10 minutes.</p>
          <Field label="Verification code" {...errors.fieldProps("code")}>
            <Input name="code" type="text" inputMode="numeric" autoComplete="one-time-code" maxLength={6}
              value={code} onChange={(_, data) => { setCode(data.value.replace(/\D/g, "")); errors.clearError("code"); }}
              disabled={busy || expired} autoFocus />
          </Field>
          {expired && <p role="alert">This code has expired. Request a new one.</p>}
          <div className="dwella-whatsapp-actions">
            <Button type="submit" appearance="primary" disabled={busy || expired}>{verify.isPending ? "Verifying…" : "Verify and connect"}</Button>
            <Button type="button" disabled={busy || remaining > 0} onClick={() => requestCode()}>{remaining ? `Resend in ${remaining}s` : "Send a new code"}</Button>
            <Button type="button" appearance="subtle" disabled={busy} onClick={() => { setPhone(challenge.phone); setChallenge(null); setCode(""); setFailure(""); }}>Change number</Button>
          </div>
          <p className="dwella-muted-copy">You do not need to send us a WhatsApp message. Never share this code with anyone.</p>
        </form>
      ) : (
        <form onSubmit={requestCode} noValidate>
          <Field label="Your WhatsApp number" {...errors.fieldProps("phone")}>
            <Input name="phone" type="tel" autoComplete="tel" maxLength={24} placeholder="e.g. +260 97 123 4567" value={phone}
              disabled={busy} onChange={(_, data) => { setPhone(data.value); errors.clearError("phone"); }} />
          </Field>
          <Checkbox label="Send me optional Dwella notifications on WhatsApp." checked={consent}
            disabled={busy} onChange={(_, data) => setConsent(Boolean(data.checked))} />
          <p className="dwella-muted-copy">Connecting verifies your number. Notifications are optional; you can turn them off in Settings or send STOP.</p>
          <Button type="submit" appearance="primary" disabled={busy || remaining > 0}>{verify.isPending ? "Requesting code…" : remaining ? `Send code in ${remaining}s` : "Send code on WhatsApp"}</Button>
        </form>
      )}
      {failure && <p role="alert" className="dwella-alert danger">{failure}</p>}
      {notice && <p role="status">{notice}</p>}
      {onboarding && <p className="dwella-muted-copy">This is optional and does not affect your workspace setup.</p>}
    </section>
  );
}
