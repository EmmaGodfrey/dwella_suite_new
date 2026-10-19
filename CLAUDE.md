# Dwella Suite Claude Reference

Read `AGENTS.md` first; it is the shared source of project architecture, workflow, security, backend, frontend, and validation rules.

For UI work, load the relevant skill from `.claude/skills/`. Those lightweight entries point to canonical shared guidance under `.agents/skills/`, keeping Codex and Claude aligned without duplicating the rules.

- `dwella-impeccable-ui`: substantial UI design, redesign, critique, and polish.
- `dwella-taste-ui`: visual hierarchy and anti-generic frontend review.
- `dwella-design-engineering`: motion and interaction behavior.

Explicit user direction and the existing Dwella design system take precedence over skill defaults. Do not push changes unless the user explicitly asks.
