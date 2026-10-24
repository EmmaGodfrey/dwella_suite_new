import React, { createContext, useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Field, Input } from "@fluentui/react-components";
import { ShieldLock24Regular } from "@fluentui/react-icons";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "react-toastify";
import { usePlatformList } from "../../Services/platform";
import { enterSupportWorkspace, leaveSupportWorkspace, refreshSupportContext } from "../../Services/support";
import { getSupportWorkspace } from "../../Services/supportContext";
import { AdminDrawer, AdminState, workspaceName } from "./AdminUI";

const SupportAccessContext = createContext({ open: () => {}, banner: null });
export const useSupportAccess = () => useContext(SupportAccessContext).open;
export const SupportBanner = () => useContext(SupportAccessContext).banner;

export function SupportAccessProvider({ user, children }) {
  const cache = useQueryClient();
  const navigate = useNavigate();
  const [selection, setSelection] = useState(null);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [now, setNow] = useState(Date.now());
  const [leaving, setLeaving] = useState(false);
  const session = user?.access?.acting_workspace;
  const admin = user?.access?.persona === "platform_admin";
  const query = usePlatformList("workspaces", { active: "true", search, page, page_size: 30 }, { enabled: admin && selection?.picker === true });
  const recover = async () => {
    try { await refreshSupportContext(cache, null); }
    catch (error) { toast.error(error.message); }
    navigate("/dashboard", { replace: true });
    setSelection({ picker: true });
    toast.info("Support access ended or expired. Choose a workspace to continue.");
  };
  useEffect(() => {
    if (!admin) return undefined;
    const handler = () => { recover(); };
    window.addEventListener("dwella:support-expired", handler);
    return () => window.removeEventListener("dwella:support-expired", handler);
  }, [admin, cache, navigate]);
  useEffect(() => {
    if (admin && getSupportWorkspace() && user && !session) recover();
  }, [admin, session, user]);
  useEffect(() => {
    if (!session) return undefined;
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, [session]);
  useEffect(() => {
    if (session && new Date(session.expires_at).getTime() <= now) recover();
  }, [now, session?.expires_at]);
  const remaining = session ? Math.min(240, Math.max(0, Math.ceil((new Date(session.expires_at).getTime() - now) / 60000))) : 0;
  const open = (workspace) => setSelection(workspace || { picker: true });
  const banner = session && <section className="admin-support-banner" aria-label="Support workspace">
      <span className="admin-support-shield" aria-hidden="true"><ShieldLock24Regular /></span>
      <div><strong>Support access · {session.name}</strong><p>Reason: {session.reason} · Every change is recorded in the audit log</p></div>
      <span className="admin-support-time">{Math.floor(remaining / 60)}h {remaining % 60}m left</span>
      <Button disabled={leaving} onClick={async () => {
        setLeaving(true);
        try { await leaveSupportWorkspace(cache, session.session_id); navigate("/dashboard"); }
        catch (error) { toast.error(error.message); }
        finally { setLeaving(false); }
      }}>{leaving ? "Leaving…" : "Leave workspace"}</Button>
    </section>;
  return <SupportAccessContext.Provider value={{ open, banner }}>
    {children}
    {admin && selection?.picker && <AdminDrawer title="Choose workspace" fields={[]} submitLabel="Close" onClose={() => setSelection(null)} onSubmit={async () => setSelection(null)}>
      <Field label="Search workspaces"><Input value={search} placeholder="Workspace, owner or town" onChange={(_, d) => { setSearch(d.value); setPage(1); }} /></Field>
      <AdminState query={query} empty={!query.data?.results?.length} title="No active workspaces found">
        <div className="admin-workspace-picker">{query.data?.results?.map((w) => <Button key={w.id} appearance="subtle" onClick={() => setSelection(w)}>{workspaceName(w)}</Button>)}</div>
        <div className="admin-card-actions"><Button disabled={!query.data?.pagination?.previous} onClick={() => setPage((p) => p - 1)}>Previous</Button>
          <Button disabled={!query.data?.pagination?.next} onClick={() => setPage((p) => p + 1)}>Next</Button></div>
      </AdminState>
    </AdminDrawer>}
    {admin && selection && !selection.picker && <AdminDrawer modal title={`Open ${workspaceName(selection)}`} fields={[
      { key: "reason", label: "Reason for support access", type: "textarea", required: true, minLength: 5, maxLength: 300 },
    ]} initial={{ reason: "" }} submitLabel="Open workspace" onClose={() => setSelection(null)} onSubmit={async (values) => {
      await enterSupportWorkspace(cache, selection.id, values.reason);
      setSelection(null); navigate("/workspace/dashboard");
    }}><p>Work in this workspace with owner access for up to four hours. Your identity stays visible and every change is recorded.</p></AdminDrawer>}
  </SupportAccessContext.Provider>;
}
