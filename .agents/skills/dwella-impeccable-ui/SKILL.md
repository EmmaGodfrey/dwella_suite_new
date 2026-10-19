---
name: dwella-impeccable-ui
description: Shape, critique, redesign, or polish Dwella Suite frontend surfaces with a complete product-UI workflow. Use for dashboards, forms, app shells, responsive layouts, and substantial UI changes.
---

# Dwella Impeccable UI

Adapted from [Impeccable](https://github.com/pbakaus/impeccable).

## Operating Mode

Dwella Suite is an operational property-management product. Optimize for scanning, comparison, repeated action, clear ownership, and compact information density. Brand expression belongs in typography, color, imagery, and details rather than decorative composition.

## Workflow

1. Read the request, current screen, nearby components, design tokens, and real API data before proposing a visual direction.
2. Classify the work:
   - **Shape:** clarify information architecture and workflows before code.
   - **Critique:** identify hierarchy, usability, accessibility, and consistency issues.
   - **Refine:** preserve existing behavior and identity while improving execution.
   - **Redesign:** preserve product truth and functionality while replacing the visual structure.
3. State the user task and primary action. Make secondary actions visually quieter.
4. Reuse Fluent UI and shared Dwella components. Extend tokens or components only when reuse is real.
5. Implement complete states: loading, empty, error, success, disabled, pending, and populated.
6. Validate in bounded passes: build and inspect the affected desktop/mobile surfaces once, fix the observed defects together, then do at most one confirmation pass. Use Playwright only when visual or interaction verification materially helps.

## Quality Floor

- Do not nest cards, wrap every section in a card, or use borders as the default grouping tool.
- Prefer hierarchy through alignment, spacing, typography, soft surface shifts, and selective dividers.
- Keep controls predictable and accessible. Use familiar icons, useful labels, and tooltips for unfamiliar icon-only actions.
- Keep content real. Do not invent analytics, trends, testimonials, statuses, or product capabilities.
- Preserve compact typography and stable dimensions so dynamic content does not shift the layout.
- Make responsive behavior explicit for every multi-column region.
- Keep light and dark themes coherent, including menus, overlays, charts, icons, and focus states.
- Treat text overflow, long names, empty datasets, request failures, and permission limits as normal product states.

## Completion

Run the production frontend build and the relevant tests. Summarize what changed, what was validated, and any remaining data or product constraint. Never push without the user's explicit instruction.

