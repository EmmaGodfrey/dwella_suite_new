import React, { useState } from "react";
import { Button, Switch, Tab, TabList } from "@fluentui/react-components";
import { PersonAdd20Regular } from "@fluentui/react-icons";
import { toast } from "react-toastify";

import {
  useCoverSetting,
  useEndCover,
  useRemoveMember,
  useRevokeInvitation,
  useTeam,
  useTeamActivity,
} from "../../Services/team";
import { EmptyState, PageActions, StatusBadge } from "../../shared/components";
import { initials } from "../../shared/format";
import { AdminState, AdminTable, ConfirmAction, when } from "../Platform/AdminUI";
import { CoverDrawer, InviteDrawer, MemberDrawer } from "./TeamDrawers";
import "./team.scss";

const roleLabel = (role) => (role === "landlord" ? "Property admin" : "Property manager");
const listNames = (items) => items.map((item) => item.name).join(", ");

function Properties({ member }) {
  if (member.role === "landlord") return "All properties";
  if (!member.properties.length) return <StatusBadge color="warning">None assigned</StatusBadge>;
  return <span className="team-properties">{listNames(member.properties)}</span>;
}

function Members({ team, onEdit, onRemove }) {
  const columns = [
    {
      key: "name",
      label: "Name",
      render: (member) => (
        <div className="team-person">
          <span className={`dwella-avatar ${member.role === "landlord" ? "is-navy" : "is-green"}`} aria-hidden="true">{initials(member.name)}</span>
          <div>
            <strong>{member.name}</strong>{member.is_you ? <span className="team-you"> · You</span> : null}
            {member.email && member.email !== member.name ? <small>{member.email}</small> : null}
          </div>
        </div>
      ),
    },
    { key: "role", label: "Role", render: (member) => roleLabel(member.role) },
    { key: "properties", label: "Properties", render: (member) => <Properties member={member} /> },
    ...(team.can_manage ? [{
      key: "actions",
      label: "Actions",
      render: (member) => (
        <div className="team-row-actions">
          <Button size="small" onClick={() => onEdit(member)}>Edit</Button>
          {!member.is_you ? <Button size="small" appearance="subtle" onClick={() => onRemove(member)}>Remove</Button> : null}
        </div>
      ),
    }] : []),
  ];
  return <AdminTable columns={columns} rows={team.members} />;
}

function Covers({ team }) {
  const end = useEndCover();
  const me = team.members.find((member) => member.is_you);
  if (!team.covers.length) return null;
  return (
    <section className="team-section" aria-labelledby="team-covers">
      <header><h2 id="team-covers">Covering now</h2></header>
      <ul className="team-list">
        {team.covers.map((cover) => {
          const mine = cover.manager.id === me?.id;
          return (
            <li key={cover.id}>
              <div>
                <strong>{cover.manager.name} is covering for {cover.covering_for.name}</strong>
                <small>Until {when(cover.expires_at)} · {cover.reason}</small>
              </div>
              {team.can_manage || mine ? (
                <Button
                  size="small"
                  disabled={end.isPending}
                  onClick={() => end.mutate(cover.id, {
                    onSuccess: () => toast.success("Cover ended."),
                    onError: (error) => toast.error(error.message || "Could not end the cover."),
                  })}
                >
                  End cover
                </Button>
              ) : null}
            </li>
          );
        })}
      </ul>
    </section>
  );
}

function Invitations({ team }) {
  const revoke = useRevokeInvitation();
  if (!team.can_manage || !team.invitations.length) return null;
  return (
    <section className="team-section" aria-labelledby="team-invitations">
      <header><h2 id="team-invitations">Pending invitations</h2></header>
      <ul className="team-list">
        {team.invitations.map((invitation) => (
          <li key={invitation.id}>
            <div>
              <strong>{invitation.name || invitation.email}</strong>
              <small>
                {[invitation.name ? invitation.email : "", roleLabel(invitation.role),
                  invitation.role === "manager" ? (listNames(invitation.properties) || "No properties yet") : "",
                  `Expires ${when(invitation.expires_at)}`].filter(Boolean).join(" · ")}
              </small>
            </div>
            <Button
              size="small"
              appearance="subtle"
              disabled={revoke.isPending}
              onClick={() => revoke.mutate(invitation.id, {
                onSuccess: () => toast.success("Invitation cancelled."),
                onError: (error) => toast.error(error.message || "Could not cancel the invitation."),
              })}
            >
              Cancel invitation
            </Button>
          </li>
        ))}
      </ul>
    </section>
  );
}

function CoverSetting({ team }) {
  const setting = useCoverSetting();
  if (!team.can_manage) return null;
  return (
    <section className="team-section" aria-labelledby="team-cover-setting">
      <header><h2 id="team-cover-setting">Teammate cover</h2></header>
      <div className="team-setting">
        <div>
          <strong>Let property managers cover for each other</strong>
          <small>A manager can work on a teammate’s properties for up to 3 days. Each cover and every change made under it is recorded. Switching this off ends any open cover.</small>
        </div>
        <Switch
          aria-label="Let property managers cover for each other"
          checked={team.allow_teammate_cover}
          disabled={setting.isPending}
          onChange={(_, data) => setting.mutate(data.checked, {
            onSuccess: () => toast.success(data.checked ? "Teammate cover switched on." : "Teammate cover switched off."),
            onError: (error) => toast.error(error.message || "Could not save this setting."),
          })}
        />
      </div>
    </section>
  );
}

const describe = (event) => {
  const d = event.details;
  const role = d.role && typeof d.role === "object" ? `role changed to ${roleLabel(d.role.to).toLowerCase()}` : "";
  const added = d.properties?.added?.length ? `added ${d.properties.added.join(", ")}` : "";
  const removed = d.properties?.removed?.length ? `removed ${d.properties.removed.join(", ")}` : "";
  switch (event.action) {
    case "team.invitation_sent": return `invited ${d.email} as a ${roleLabel(d.role).toLowerCase()}`;
    case "team.invitation_revoked": return `cancelled the invitation for ${d.email}`;
    case "team.invitation_accepted": return `joined as a ${roleLabel(d.role).toLowerCase()}`;
    case "team.member_changed": return `updated ${d.member_name}: ${[role, added, removed].filter(Boolean).join("; ") || "no change"}`;
    case "team.member_removed": return `removed ${d.member_name} from the team`;
    case "team.cover_setting_changed": return `switched teammate cover ${d.allow_teammate_cover ? "on" : "off"}`;
    case "cover.started": return `started covering for ${d.on_behalf_of_name}${d.reason ? ` (${d.reason})` : ""}`;
    case "cover.ended": return d.why === "ended"
      ? `ended the cover for ${d.on_behalf_of_name}`
      : `cover for ${d.on_behalf_of_name} ended (${{ member_removed: "member removed", role_changed: "role changed", switched_off: "cover switched off" }[d.why] || "closed"})`;
    case "cover.change": return `made a change while covering for ${d.on_behalf_of_name}${event.property_names.length ? ` at ${event.property_names.join(", ")}` : ""}`;
    default: return event.action.replaceAll("_", " ").replace(".", ": ");
  }
};

function Activity({ canManage }) {
  const [page, setPage] = useState(1);
  const query = useTeamActivity(page);
  const rows = query.data?.results || [];
  return (
    <AdminState query={query}>
      {!rows.length ? (
        <EmptyState
          title="No team activity yet"
          description={canManage ? "Invitations, role and property changes and covers will be listed here." : "Covers you start, and covers made for you, will be listed here."}
        />
      ) : (
        <AdminTable
          columns={[
            { key: "created_at", label: "When", render: (event) => when(event.created_at) },
            { key: "actor", label: "Who", render: (event) => <strong>{event.actor}</strong> },
            { key: "what", label: "What happened", render: describe },
          ]}
          rows={rows}
          pagination={query.data.pagination}
          setPage={setPage}
        />
      )}
    </AdminState>
  );
}

export default function Team() {
  const query = useTeam();
  const [tab, setTab] = useState("people");
  const [drawer, setDrawer] = useState(null); // null | "invite" | "cover" | { edit } | { remove }
  const remove = useRemoveMember();
  const team = query.data;
  const me = team?.members.find((member) => member.is_you);
  const teammates = team ? team.members.filter((member) => member.role === "manager" && !member.is_you) : [];
  const covering = team?.covers.some((cover) => cover.manager.id === me?.id);
  const canCover = Boolean(team && me?.role === "manager" && team.allow_teammate_cover && teammates.length && !covering);

  return (
    <div className="admin-screen team-screen">
      <PageActions>
        {canCover ? <Button onClick={() => setDrawer("cover")}>Cover for a teammate</Button> : null}
        {team?.can_manage ? (
          <Button appearance="primary" icon={<PersonAdd20Regular />} onClick={() => setDrawer("invite")}>Invite team member</Button>
        ) : null}
      </PageActions>
      <TabList selectedValue={tab} onTabSelect={(_, data) => setTab(data.value)} aria-label="Team sections">
        <Tab value="people">People</Tab>
        <Tab value="activity">Activity</Tab>
      </TabList>
      {tab === "activity" ? <Activity canManage={Boolean(team?.can_manage)} /> : (
        <AdminState query={query}>
          {team ? (
            <>
              {!team.can_manage ? (
                <p className="dwella-muted-copy">
                  You work on the properties assigned to you. A property admin manages the team, payouts and workspace settings.
                </p>
              ) : null}
              <Covers team={team} />
              <Members team={team} onEdit={(member) => setDrawer({ edit: member })} onRemove={(member) => setDrawer({ remove: member })} />
              <Invitations team={team} />
              <CoverSetting team={team} />
            </>
          ) : null}
        </AdminState>
      )}
      {drawer === "invite" ? <InviteDrawer onClose={() => setDrawer(null)} /> : null}
      {drawer === "cover" ? <CoverDrawer teammates={teammates} onClose={() => setDrawer(null)} /> : null}
      {drawer?.edit ? <MemberDrawer key={drawer.edit.id} member={drawer.edit} onClose={() => setDrawer(null)} /> : null}
      {drawer?.remove ? (
        <ConfirmAction
          title={`Remove ${drawer.remove.name}?`}
          description="They lose access to this workspace straight away and any cover they are part of ends. Records they created stay in place."
          label="Remove from team"
          onClose={() => setDrawer(null)}
          onConfirm={async () => {
            await remove.mutateAsync(drawer.remove.id);
            toast.success(`${drawer.remove.name} removed from the team.`);
            setDrawer(null);
          }}
        />
      ) : null}
    </div>
  );
}
