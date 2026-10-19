---
name: dwella-design-engineering
description: Apply purposeful motion and interaction polish to Dwella Suite UI. Use for transitions, menus, drawers, feedback, state changes, and animation reviews; do not invoke for backend-only work.
---

# Dwella Design Engineering

Adapted from [Emil Kowalski's design-engineering skills](https://github.com/emilkowalski/skill), especially `emil-design-eng`.

## Intent

Make interactions feel immediate and coherent. Motion explains a state change or spatial relationship; it is not decoration by default.

## Decisions

1. Decide whether animation helps. Frequent actions should be instant or nearly instant. Never delay keyboard-driven actions.
2. Name the purpose: feedback, continuity, state indication, spatial origin, or reducing a jarring change.
3. Prefer transform and opacity. Avoid layout-triggering animation when a compositor-friendly option exists.
4. Use ease-out for entering/exiting UI, ease-in-out for movement already on screen, ease for color/hover changes, and linear for continuous progress.
5. Keep common UI motion short: press feedback 100-160ms, tooltips/popovers 125-200ms, selects/dropdowns 150-250ms, dialogs and major panels 200-300ms.
6. Respect `prefers-reduced-motion`; the interface must remain clear without animation.

## Craft Rules

- Animate only the properties that change; never use `transition: all`.
- Pressable controls need immediate visual feedback, but keep scaling subtle enough not to shift surrounding layout.
- Popovers should originate near their trigger; centered dialogs should remain centered.
- Do not animate from `scale(0)`. Pair a small scale change with opacity when scaling is appropriate.
- Keep exit motion slightly faster than entrance motion.
- Preserve focus, semantics, and click targets throughout transitions.
- Avoid staggered entrances in operational screens. Users come to Dwella to work, not watch content arrive.
- Test interrupted actions and rapid repeated clicks so state and animation cannot diverge.

## Review

When reviewing motion, report concrete changes in a `Before | After | Why` table. Verify timing, easing, reduced-motion behavior, keyboard use, and layout stability.

