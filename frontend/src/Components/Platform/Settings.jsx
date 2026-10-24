import React from "react";
import { Field, Switch } from "@fluentui/react-components";
import { toast } from "react-toastify";
import { usePlatformList, usePlatformMutation } from "../../Services/platform";
import { AdminHeader, AdminState } from "./AdminUI";

export default function PlatformSettings() {
  const query = usePlatformList("settings");
  const mutation = usePlatformMutation({ onSuccess: () => window.dispatchEvent(new Event("dwella:assistant-settings-changed")) });
  return <div className="admin-screen">
    <AdminHeader title="Platform settings" description="Manage platform-wide features." />
    <AdminState query={query}>
      <section className="admin-card">
        <h2>Handy assistant</h2>
        <p>Allow property managers to use the assistant. Turning it off hides the widget and blocks assistant actions.</p>
        {query.data && !query.data.handy_agent_configured ? <p>The assistant connection is not configured for this environment. It will stay disabled until setup is complete.</p> : null}
        <Field label="Assistant availability">
          <Switch checked={mutation.isPending ? Boolean(mutation.variables?.body.handy_agent_enabled) : Boolean(query.data?.handy_agent_enabled)} disabled={mutation.isPending || !query.data?.handy_agent_configured}
            label={query.data?.handy_agent_enabled ? "Enabled" : "Disabled"}
            onChange={async (_, data) => {
              try { await mutation.mutateAsync({ resource: "settings", method: "patch", body: { handy_agent_enabled: data.checked } }); }
              catch (error) { toast.error(error.message || "Could not save settings."); }
            }} />
        </Field>
      </section>
    </AdminState>
  </div>;
}
