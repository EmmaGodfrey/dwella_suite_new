// Kept free of the API client so it can be tested without a browser.
const isTeamQuery = (query) => query.queryKey[0] === "organizations" && query.queryKey[1] === "team";

// Which properties a person may work on has changed (a cover started or ended,
// an assignment or role changed). Marking queries stale would keep the old
// records in memory, and on screen if a refetch failed, so everything held from
// the previous scope is cancelled and emptied; mounted screens load again.
export async function resetPropertyScope(client) {
  const outside = (query) => !isTeamQuery(query);
  await client.cancelQueries({ predicate: outside });
  await client.resetQueries({ predicate: outside });
}

// What decides a manager's scope, as one comparable value: their role, their
// own properties, and the cover they are working under with its properties.
export function scopeSignature(team) {
  const me = team?.members?.find((member) => member.is_you);
  if (!me) return "";
  const ids = (member) => (member?.properties || []).map((item) => item.id).sort().join(",");
  const cover = team.allow_teammate_cover ? team.covers.find((item) => item.manager.id === me.id) : null;
  const teammate = cover ? team.members.find((member) => member.id === cover.covering_for.id) : null;
  return [me.role, ids(me), cover?.id || "", ids(teammate)].join("|");
}
