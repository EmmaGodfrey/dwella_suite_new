import React, { useEffect, useRef } from "react";
import { Button } from "@fluentui/react-components";
import { PeopleSwap24Regular } from "@fluentui/react-icons";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "react-toastify";

import { queryKeys } from "../../Services/queryKeys";
import { resetPropertyScope, scopeSignature, teamKeys, useEndCover, useTeam } from "../../Services/team";
import { getUserAccess } from "../../shared/access";
import { when } from "../Platform/AdminUI";
import "./team.scss";

/**
 * Shown on every page while a property manager works under a cover. It also
 * watches both management roles: another admin can change assignments or roles,
 * end a cover or remove the person from another browser. This tab must let go
 * of the records it loaded before that.
 */
export default function CoverBanner({ user }) {
  const { role } = getUserAccess(user);
  const manager = role === "manager";
  const watching = manager || role === "landlord";
  const client = useQueryClient();
  const team = useTeam({
    enabled: watching,
    staleTime: 30_000,
    refetchInterval: 60_000,
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
  });
  const end = useEndCover();
  const me = team.data?.members.find((member) => member.is_you);
  const cover = manager && me ? team.data.covers.find((item) => item.manager.id === me.id) : null;
  const expiresAt = cover?.expires_at;
  const signature = watching && team.data ? scopeSignature(team.data) : "";
  const memberRole = me?.role;
  const seen = useRef("");
  const refused = watching && [401, 403].includes(team.error?.status);

  useEffect(() => {
    if (!signature) return;
    // The first team read may already reflect a role change made while this
    // tab still has the old account cached. It must clear that scope too.
    const roleChanged = team.isFetchedAfterMount && memberRole && memberRole !== role;
    const changed = (seen.current && seen.current !== signature) || roleChanged;
    seen.current = signature;
    if (!changed) return;
    // The role may have changed too, so the account is read again.
    resetPropertyScope(client).then(() => client.invalidateQueries({ queryKey: queryKeys.currentUser }));
  }, [signature, memberRole, role, team.isFetchedAfterMount, client]);

  useEffect(() => {
    // Removed from the team: drop what was loaded and let the shell re-check access.
    if (refused) resetPropertyScope(client).then(() => client.invalidateQueries({ queryKey: queryKeys.currentUser }));
  }, [refused, client]);

  useEffect(() => {
    if (!expiresAt) return undefined;
    // When the cover runs out the scope shrinks on the server; read the team
    // again so the change is noticed above and the old records are dropped.
    const wait = Math.min(new Date(expiresAt).getTime() - Date.now() + 1000, 2 ** 31 - 1);
    const timer = setTimeout(() => client.invalidateQueries({ queryKey: teamKeys.team }), Math.max(wait, 0));
    return () => clearTimeout(timer);
  }, [expiresAt, client]);

  if (!cover) return null;
  return (
    <section className="admin-support-banner" aria-label="Teammate cover">
      <span className="admin-support-shield" aria-hidden="true"><PeopleSwap24Regular /></span>
      <div>
        <strong>Covering for {cover.covering_for.name}</strong>
        <p>Reason: {cover.reason} · Changes on their properties are recorded under your name</p>
      </div>
      <span className="admin-support-time">Until {when(cover.expires_at)}</span>
      <Button
        disabled={end.isPending}
        onClick={() => end.mutate(undefined, {
          onSuccess: () => toast.success("Cover ended."),
          onError: (error) => toast.error(error.message || "Could not end the cover."),
        })}
      >
        {end.isPending ? "Ending…" : "End cover"}
      </Button>
    </section>
  );
}
