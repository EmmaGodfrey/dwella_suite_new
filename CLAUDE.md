# Dwella Suite Claude Reference

Read `AGENTS.md` first; it is the shared source of project architecture, workflow, security, backend, frontend, and validation rules.

Project memory is shared with Codex in `.agents/memory/` (see "Shared Memory" in `AGENTS.md`). Save and update memories there, not in Claude's per-user auto-memory folder. The index is loaded below:

@.agents/memory/MEMORY.md

For UI work, load the relevant skill from `.claude/skills/`. Those lightweight entries point to canonical shared guidance under `.agents/skills/`, keeping Codex and Claude aligned without duplicating the rules.

- `dwella-impeccable-ui`: substantial UI design, redesign, critique, and polish.
- `dwella-taste-ui`: visual hierarchy and anti-generic frontend review.
- `dwella-design-engineering`: motion and interaction behavior.

Explicit user direction and the existing Dwella design system take precedence over skill defaults. Do not push changes unless the user explicitly asks.
