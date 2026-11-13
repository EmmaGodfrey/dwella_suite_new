import React, { useEffect } from "react";
import { Button } from "@fluentui/react-components";
import { PeopleSwap24Regular } from "@fluentui/react-icons";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "react-toastify";

import { useEndCover, useTeam } from "../../Services/team";
import { getUserAccess } from "../../shared/access";
import { when } from "../Platform/AdminUI";
import "./team.scss";

/** Shown on every page while a property manager works under a cover. */
export default function CoverBanner({ user }) {
  const manager = getUserAccess(user).role === "manager";
  const client = useQueryClient();
  const team = useTeam({ enabled: manager, staleTime: 60_000 });
  const end = useEndCover();
  const me = team.data?.members.find((member) => member.is_you);
  const cover = manager && me ? team.data.covers.find((item) => item.manager.id === me.id) : null;
  const expiresAt = cover?.expires_at;

  useEffect(() => {
    if (!expiresAt) return undefined;
    // When the cover runs out the scope shrinks on the server; drop what is cached.
    const wait = Math.min(new Date(expiresAt).getTime() - Date.now() + 1000, 2 ** 31 - 1);
    const timer = setTimeout(() => client.invalidateQueries(), Math.max(wait, 0));
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
