// Mirrors the server's next/back rules so a tour step moves the moment it is clicked.
// The server stays authoritative: its response replaces this, and an error restores it.
export function optimisticTourStep(tour, action) {
  const ids = tour?.steps?.map((step) => step.id) || [];
  const index = ids.indexOf(tour?.current_step);
  if (index < 0 || !["in_progress", "paused"].includes(tour.status)) return null;
  if (action === "back") return { ...tour, status: "in_progress", current_step: ids[Math.max(0, index - 1)] };
  if (action !== "next" || index === ids.length - 1) return null;
  const completed = tour.completed_steps.includes(tour.current_step) ? tour.completed_steps : [...tour.completed_steps, tour.current_step];
  return {
    ...tour, status: "in_progress", current_step: ids[index + 1], completed_steps: completed,
    pending_steps: ids.filter((id) => !completed.includes(id)),
  };
}
