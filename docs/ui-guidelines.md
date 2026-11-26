# UI guidelines

Rules for the dashboard in `ui/`. They follow Apple's
[Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/) (HIG),
with the same feel as the Retro Arcade (`Novsochetra/fighting-games`, `apps/web/arcade/src/styles/`).
When a case is not here, do what the HIG does for iPadOS and macOS.

## Principles

- **Hierarchy:** the pixel art is the content. Controls stay quiet around it.
- **Harmony:** rounded, concentric shapes; system-like materials, colors and type.
- **Consistency:** one component for one job, used the same way on every screen.

## Layout

- Split view: sidebar (sections), content (the work), inspector (settings for what is selected).
- A toolbar sits on top of the content: title on the left, actions on the right, one primary action.
- Below 768px wide: the sidebar becomes a bottom tab bar (5 items at most), the inspector a sheet.
- Spacing comes from the `--space-*` tokens (a 4 and 8 px grid). Respect safe areas.

## Components

Reuse the components in `ui/src/components/`. Make a new one only when none fits, and only once.

- **Button:** filled (the one primary action), tinted, plain, and round glass for icon-only.
- **Segmented control:** 2 to 5 choices of the same kind (view, direction, filter).
- **Sheet:** a self-contained task. It has a grabber, drags down to close, and Esc closes it.
- **Popover and menu:** short choices next to their control.
- **Lists:** grouped, inset rows with hairline separators.
- **Toggle, slider, stepper, search field:** native-like, with a visible label.
- **Progress:** a bar when the amount is known, a spinner when not. Long work can be stopped.
- **Notice:** short status that floats and goes away. Errors stay until closed.
- **Pixel art:** `image-rendering: pixelated`, whole-number zoom, checkerboard behind transparency.

## Look

- Every color, size, radius, shadow, blur and timing is a token in `ui/src/styles/tokens.css`.
  No raw hex or magic numbers in components.
- Dark is the default; light must work as well. Use meaning-based colors (label, secondary label,
  separator, fill, tint). Tint (blue) marks only what you can press. Red marks only destructive acts.
- Type: Inter as the stand-in for SF Pro, on Apple text styles (large title, title 1 to 3, headline,
  body, callout, subheadline, footnote, caption). Regular, semibold and bold weights only.
- Glass (blur and saturate) is for bars, sheets and floating controls, never behind long text.
- Concentric corners: inner radius = outer radius minus padding.
- Icons look like SF Symbols: one stroke weight and one size per place. An icon-only button has an
  `aria-label` and a tooltip.

## Interaction

- Hit targets are at least 44 × 44 px.
- Press: scale to 0.96 and dim. Hover only lifts, and only under `@media (hover: hover)`.
- Each action answers within 100 ms. Work that takes longer shows progress.
- Destructive actions say what is lost and ask first; give undo when you can.
- The keyboard reaches everything, with a visible focus ring. Esc closes, ⌘↩ runs the primary action.
- Each gesture (drag to close, swipe, pinch to zoom) also has a button.

## Motion

- Motion shows where a thing comes from and where it goes. It never only decorates.
- Use springs or short eases (150 to 350 ms) from the motion tokens.
- Motion never blocks input.
- With `prefers-reduced-motion`, a fade replaces movement.

## Accessibility

- Text contrast is at least 4.5:1 (3:1 for large text). Color is never the only sign of a state.
- Use semantic HTML. Each input has a label. Each image has alt text (for example the character name).
- Sizes in `rem`, so the page still works at 200% zoom.

## Words

- Sentence case. Buttons are verbs: "Generate", "Stop", not "Submit" or "OK".
- Short and plain. An empty state says what to do next.
