---
name: dwella-taste-ui
description: Detect and remove generic AI-looking frontend patterns in Dwella Suite. Use during UI implementation and review for typography, color, spacing, cards, visual rhythm, forms, and responsive states.
---

# Dwella Taste UI

Adapted from [Taste Skill](https://github.com/Leonxlnx/taste-skill) and [tasteskill.dev](https://www.tasteskill.dev/).

## Preserve The Product

Use Dwella's established Fluent UI foundation, evergreen and gold brand palette, compact typography, and existing domain language. These rules correct generic output; they do not authorize replacing the brief or design system.

## Anti-Generic Checks

- Do not make every metric, section, toolbar, or field group a bordered rounded rectangle.
- Cards must communicate a real repeated object or elevation level. Otherwise use whitespace, alignment, bands, typography, or a restrained divider.
- Do not nest cards inside cards.
- Avoid oversized headings in operational screens, excessive eyebrow labels, hero-like dashboard headers, decorative gradients, floating blobs, and arbitrary icon tiles.
- Use one deliberate radius system. Pills are for statuses, compact choices, and appropriate actions, not every container.
- Use the existing type family and scale. Establish hierarchy with weight, size, grouping, and whitespace rather than many unrelated styles.
- Use color to communicate meaning and hierarchy. Keep contrast WCAG AA and verify both themes.
- Avoid repetition: consecutive sections should not all use the same card grid or split layout.
- Use real property imagery where it helps recognition; provide a restrained placeholder when no image exists.

## Product UI Checks

- Put field labels above inputs; placeholders are examples, never labels.
- Keep primary actions singular and obvious. Duplicate labels should represent the same action consistently.
- Show loading shapes that resemble the final content, useful empty states, inline validation, contextual errors, and pending states that prevent double submission.
- Ensure long property names, currency values, translations, and narrow viewports do not overlap or clip.
- Use server data for filtering, pagination, and metrics when scale or correctness requires it.
- Keep dense tables and directories easy to scan with column alignment, restrained row treatment, and clear hover/focus states.

## Preflight

Before finishing, scan for excessive `border`, `box-shadow`, `border-radius`, uppercase tracking, one-off colors, and duplicate component styles. Every occurrence should have a purpose. Check desktop and mobile layout, keyboard focus, contrast, empty/error/loading states, and theme consistency.

