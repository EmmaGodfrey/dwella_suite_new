import React from "react";
import { Link } from "react-router-dom";
import { ArrowRight20Regular, ChevronRight20Regular, Clock20Regular, PersonAdd20Regular, ShieldCheckmark20Regular, Warning20Regular } from "@fluentui/react-icons";
import { usePlatformList } from "../../Services/platform";
import { AdminHeader, AdminState, money } from "./AdminUI";
import { RecentActivity } from "./AuditLog";

export default function Administration() {
  const query = usePlatformList("dashboard");
  const data = query.data;
  const counts = Object.fromEntries((data?.beta_signups || []).map((row) => [row.status, row.count]));
  const accepted = counts.accepted || 0;
  const waiting = (counts.new || 0) + (counts.contacted || 0);
  const declined = counts.declined || 0;
  const total = accepted + waiting + declined;
  const attention = data ? [
    [data.pending_identity_checks, "identity checks waiting", "Review submitted documents", "/admin/identity-checks", <ShieldCheckmark20Regular />, "info"],
    [data.open_support_sessions, "support sessions open", "Review recorded support activity", "/admin/audit-log", <Clock20Regular />, "info"],
    [waiting, "beta signups to review", "Help applicants get started", "/beta-signups", <PersonAdd20Regular />, "info"],
    [data.workspaces.suspended, "workspaces suspended", "Review workspace access", "/admin/workspaces", <Warning20Regular />, "warning"],
  ] : [];
  return <div className="admin-screen dwella-dashboard-v2 admin-dashboard">
    <AdminHeader title="Administration" description="Workspace health, onboarding and support across Dwella." />
    <AdminState query={query}>
      <section className="dwella-portfolio-pulse" aria-label="Platform at a glance">
        <div className="dwella-pulse-lead">
          <span>Beta applicants</span><div className="dwella-pulse-figure"><strong>{total}</strong><small>applicants · beta opens 18 November</small></div>
          <div className="dwella-pulse-bar" role="img" aria-label={`${accepted} accepted, ${waiting} waiting for review, ${declined} declined`}>
            {[["paid", accepted], ["due", waiting], ["overdue", declined]].map(([key, value]) => value > 0 && <span key={key} className={`is-${key}`} style={{flexGrow:value}} />)}
          </div>
          <ul className="dwella-pulse-legend"><li className="is-paid">{accepted} accepted</li><li className="is-due">{waiting} waiting for review</li><li className="is-overdue">{declined} declined</li></ul>
        </div>
        <dl className="dwella-pulse-stats">
          {[
            ["Active workspaces", data?.workspaces.active, `${data?.workspaces.suspended} suspended`, "/admin/workspaces"],
            ["Users", data?.users.total, `${data?.users.active} active`, "/admin/users"],
            ["Collected", money(data?.collections_this_month), "this month, all workspaces"],
          ].map(([label, value, note, path]) => <div className="dwella-pulse-stat" key={label}><dt>{label}</dt><dd><strong>{path ? <Link to={path}>{value}</Link> : value}</strong><small>{note}</small></dd></div>)}
        </dl>
      </section>
      <div className="dwella-dashboard-row is-top-aligned">
        <RecentActivity filters={{}} showWorkspace />
        <section className="dwella-dashboard-card"><header className="dwella-dashboard-section-heading"><div><h3>Needs attention</h3><p>{data?.workspaces.new_this_week} new workspaces this week</p></div></header>
          <ul className="dwella-attention-list">{attention.map(([count, label, detail, path, icon, tone]) => <li key={label}>
            <Link className="dwella-attention-item" to={path}><span className={`dwella-attention-chip is-${tone}`}>{icon}</span>
              <span className="dwella-attention-copy"><strong>{count} {label}</strong><small>{detail}</small></span><ChevronRight20Regular className="dwella-attention-arrow" />
            </Link></li>)}</ul>
          <Link to="/admin/identity-checks">Open identity checks <ArrowRight20Regular /></Link>
        </section>
      </div>
    </AdminState>
  </div>;
}
