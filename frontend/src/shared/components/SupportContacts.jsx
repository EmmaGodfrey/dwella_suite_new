import React from "react";
import { usePublicConfiguration } from "../../Services/runtimeSettings";

export default function SupportContacts() {
  const { data } = usePublicConfiguration();
  if (
    !data ||
    ![
      data.support_email,
      data.support_phone,
      data.support_whatsapp,
      data.support_help_url,
    ].some(Boolean)
  )
    return null;
  return (
    <aside className="settings-support" aria-label="Dwella support">
      <strong>Need help?</strong>
      {data.support_email && (
        <a href={`mailto:${data.support_email}`}>Email support</a>
      )}
      {data.support_phone && (
        <a href={`tel:${data.support_phone}`}>{data.support_phone}</a>
      )}
      {data.support_whatsapp && (
        <a
          href={`https://wa.me/${data.support_whatsapp.replace(/^\+/, "")}`}
          target="_blank"
          rel="noopener noreferrer"
        >
          WhatsApp
        </a>
      )}
      {data.support_help_url && (
        <a
          href={data.support_help_url}
          target="_blank"
          rel="noopener noreferrer"
        >
          Help centre
        </a>
      )}
    </aside>
  );
}
