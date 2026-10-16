# PatchPilot UI design spec

Goal: look like a hand-built developer tool, not a default Streamlit app or a generated landing page.

## Research summary

Sources are third-party write-ups; none are official specs, so values are borrowed as direction, not copied.

**Common "vibe-coded" tells** ([Fountain Institute](https://www.thefountaininstitute.com/blog/signs-vibe-coded-ui), [impeccable.style](https://impeccable.style/slop), [Robots on Payroll](https://robotsonpayroll.substack.com/p/how-to-avoid-that-vibe-coded-look)):
purple/indigo gradients, gradient text, emoji used as icons, glassmorphism, colored neon glows on dark, soft grey card shadows, pill badges everywhere, everything centered, inconsistent spacing, default alert boxes, too many colors.

**What hand-designed dev tools do instead:**
- Linear ([summary](https://opendesigner.io/design-systems/linear-app)): near-all-grey palette, layered near-black surfaces, faint translucent-white 1px dividers, ONE accent reserved for CTAs and active states, green only for status, tight tracking on headings, medium (500-ish) weights.
- Vercel/Geist ([summary](https://vercel.com/design.md)): 4px-based spacing scale (4, 8, 12, 16, 24, 32, 40, 64), 6px control radius, 1px outlines, mono font for technical labels.
- Raycast ([summary](https://opendesigner.io/design-systems/raycast)): near-black background, accent used sparingly, mono for code elements.
- GitHub diff view: red/green tinted line backgrounds, a line-number gutter on each side, monospace, hunk header rows. (I could not verify GitHub's exact token values via search; the tints below are my own approximations.)
- Sentry / timeline logs: vertical rail with a status dot per step, short summary line, details collapsed. (Not verified against a Sentry source; this is the general pattern.)

Note: Inter is itself listed as a common AI-UI default by some critics. The brief asks for Inter + JetBrains Mono, so I keep them and differentiate through weight, tracking, size discipline and restraint.

## Palette

| Token | Hex / value | Use |
|---|---|---|
| `--bg` | `#0b0c0e` | page |
| `--surface-1` | `#111316` | sidebar, panels, editor |
| `--surface-2` | `#171a1e` | headers, inputs, hover |
| `--surface-3` | `#1e2227` | active, pills |
| `--border` | `rgba(255,255,255,0.08)` | all dividers |
| `--border-strong` | `rgba(255,255,255,0.16)` | hover, focus rings base |
| `--text` | `#e6e8eb` | primary |
| `--text-muted` | `#9aa1a9` | secondary |
| `--text-faint` | `#6c737b` | labels, line numbers |
| `--accent` | `#5b9bf5` | primary button, focus, active tab only |
| `--accent-hover` | `#78adf7` | |
| `--green` | `#3fb27f` | passed (status only) |
| `--red` | `#e5604f` | failed (status only) |
| `--amber` | `#d9a441` | running / warning (status only) |

Diff tints: added `rgba(63,178,127,0.14)`, removed `rgba(229,96,79,0.14)`, gutter tints at 0.22.
No gradients, no glows, no purple.

## Type

- UI: Inter, fallbacks `system-ui, -apple-system, "Segoe UI", sans-serif`.
- Code: JetBrains Mono, fallbacks `ui-monospace, "SF Mono", Menlo, Consolas, monospace`.
- Scale (px / line-height): 11/16 label (uppercase, +0.06em), 12/16 meta, 13/20 body-sm and code, 14/22 body, 16/24 h3, 20/28 h2, 24/32 wordmark.
- Headings weight 600, letter-spacing -0.02em; body 400; labels 500.

## Spacing, radius, borders

- Scale: 4 / 8 / 12 / 16 / 24 / 32 / 48.
- Radius: 8px controls, 10px panels. Pills fully rounded only for status pills.
- Borders: 1px `--border`. No box-shadows except focus ring (`0 0 0 2px` accent at 35%).

## Components

- **Wordmark**: inline SVG mark (accent rounded square with a plus "patch" glyph) + "PatchPilot" 600, tagline in muted 13px. "Demo only" as a small outlined pill, not an alert.
- **Sidebar**: quiet control panel. Uppercase section labels, sample select, attempts slider, usage meter (thin bar, 5 segments), model as a mono badge.
- **Editor**: panel with a header bar (file name `main.py`, line counter `n / 200`), textarea in JetBrains Mono 13px/1.6, no default textarea chrome.
- **Primary button**: solid accent, dark text, 8px radius, hover lighter, focus ring, disabled at 40% opacity.
- **Timeline**: vertical rail; each step has a dot (amber pulsing = running, red = failed, green = passed), title, one-line diagnosis, `<details>` collapsed for error, patched code, output. Thin indeterminate bar while running.
- **Result banner**: compact row with status dot, "Fixed in N attempts" / "Could not fix", tinted border only. Tabs: Diff, Original vs Fixed, Output.
- **Diff**: GitHub-style table, two line-number gutters, +/- column, hunk headers.
- **Empty state**: dashed border panel with a short instruction and 3 numbered steps.
- **Footer**: single muted line with repo link.
- **Hidden chrome**: toolbar/deploy/menu, decoration and footer. The header strip stays (transparent) so the sidebar toggle works on mobile.

## Layout

Wide layout, sidebar left, main split into two equal panes (editor | results) at >= 900px; stacks on narrow screens. 24px gutters desktop, 16px mobile.
