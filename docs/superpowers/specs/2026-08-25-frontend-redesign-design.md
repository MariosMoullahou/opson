# Opson — Frontend Redesign: Tokens, Type and Components

**Date:** 2026-08-25
**Repo:** https://github.com/MariosMoullahou/opson
**Branch:** `catalog/none/CC/model-redesign-s3-media-forms` (or a fresh branch off it)
**Status:** Design — two decisions open, see §0
**Companion:** the backend pass at `2026-08-24-model-redesign-s3-design.md`

---

## 0. Open decisions

Everything else in this document is settled. These two are not, and both are one-line token
changes by design — nothing downstream depends on which way they go.

| # | Decision | Default assumed here | Why it is open |
|---|---|---|---|
| D1 | **Ground:** light (`dust-grey`) or deep (`pine-teal`) | **Light (A)** | The palette can only produce a Spotify-style bright button on a dark ground (§4.3). Light is the safer choice for food; deep is the more striking one. |
| D2 | **Display face:** Sofia Sans or Google Sans | **Sofia Sans** | Both serve real Greek. Sofia Sans reaches weight 900; Google Sans is closer to Circular but stops at 700. |

The palette itself is deliberately isolated in one token block (§4.1) because the owner has said it
may change later. Swapping it must never require touching a component rule.

---

## 1. Context

Opson's stylesheet is not bad. It has a real token layer, 166 consistent classes, no framework and
no build step. What it lacks is a **voice**: there is no typeface at all (`Segoe UI`, i.e. whatever
the OS happens to supply), and every radius sits in the same soft middle, so nothing on the page
distinguishes itself.

The brief is *Spotify's mechanics without Spotify's black*. What actually transfers, once the black
is removed, is four things — and only one of them is colour:

1. Full-pill controls against near-square surfaces.
2. A large weight jump between body and display type.
3. One accent used exclusively as a fill, never as ink.
4. Interaction expressed as scale, not shadow.

### Facts established before this spec

- Of 1942 Google Fonts families, **118 serve Greek**. Montserrat, Poppins, Outfit, Jost, DM Sans,
  Figtree, Urbanist, Sora and Space Grotesk — the usual "Circular alternative" recommendations —
  are all Latin-only and would silently drop Greek copy back to Segoe UI.
- Spotify's own stack includes `CircularSp-Grek`, a dedicated Greek cut.
- Encore, Spotify's design system, uses radii of 2/4/6/8/16px with buttons at 9999px. It is much
  **squarer** than it appears; the roundness lives almost entirely in buttons and avatars.

---

## 2. Radius — decided

Taken from Encore's shipped tokens, remapped onto Opson's naming.

```css
--radius-xs:    2px;    /* image corners inside cards */
--radius-sm:    4px;    /* inputs, selects, small tiles */
--radius-md:    8px;    /* cards, panels, dropdowns */
--radius-lg:   16px;    /* hero, large containers, modals */
--radius-full: 9999px;  /* buttons, category pills, badges, avatars */
```

**This replaces `8px / 14px / 22px`.** Every surface gets squarer; every control goes fully round.
The contrast between the two is the effect — applying only half of this change produces nothing.

| Element | Today | Becomes |
|---|---|---|
| Buttons (`.btn-primary`, `.product-add`, `.search-btn`) | 8–14px | `--radius-full` |
| Category pills, badges, cart count | already full | unchanged |
| Product / producer / event cards | 14–22px | `--radius-md` |
| Panels | 22px | `--radius-md` |
| Hero | flat | `--radius-lg` where it is inset |
| Product and cover images | inherit card | `--radius-xs` |
| Inputs, textareas, selects | 8px | `--radius-sm` |
| Producer avatars | — | `--radius-full` |

> Note the deliberate asymmetry: an image sits at 2px *inside* a card that sits at 8px. Encore does
> this so the image reads as a distinct plate rather than melting into its container.

---

## 3. Spacing — decided

Encore's scale, adopted wholesale. Opson currently has no spacing scale at all: templates carry 137
inline `style` attributes with ad-hoc values (`padding: 36px 24px`, `margin: 36px 0 16px`), which is
why the vertical rhythm wanders from page to page.

```css
--space-3xs:   2px;
--space-2xs:   4px;
--space-xs:    6px;
--space-sm:    8px;
--space-md:   12px;
--space-base: 16px;   /* the base unit */
--space-lg:   24px;
--space-xl:   32px;
--space-2xl:  48px;
--space-3xl:  64px;
--space-4xl:  96px;
--space-5xl: 128px;
```

**Rule: no raw px value may appear in a template.** Spacing comes from these tokens, applied in the
stylesheet. See §8 for how the 137 inline styles are retired.

---

## 4. Colour

### 4.1 The palette block — swappable

The owner's Coolors palette. This block is the **only** place literal brand colours may appear.

```css
:root {
  /* ---- palette: replace this block wholesale to re-skin ---- */
  --dust-grey:    #dad7cd;
  --dry-sage:     #a3b18a;
  --fern:         #588157;
  --hunter-green: #3a5a40;
  --pine-teal:    #344e41;
}
```

### 4.2 Semantic tokens — what components actually reference

Components never name a palette colour. They name a role. This is what makes D1, and any future
palette change, cheap. Derived tints (a lighter ground, a muted ink) are allowed to be literals
*here* and nowhere else — re-skinning means editing §4.1 and these few tints, never a component.

```css
:root {
  --ground:       var(--dust-grey);   /* page background */
  --surface:      #f0eee7;            /* cards, panels: a lighter tint of ground */
  --surface-sunk: #dfe3d3;            /* image wells, empty states */
  --ink:          var(--pine-teal);   /* headings, body, prices */
  --ink-muted:    #5f6f61;            /* secondary copy */
  --line:         var(--fern);        /* borders, dividers, rules */
  --accent-fill:  var(--pine-teal);   /* button background (config A) */
  --accent-ink:   #f2f1ea;            /* text on the accent fill */
  --focus-ring:   var(--pine-teal);
}
```

Configuration B (deep ground) redefines **only this block** — no component rule changes:

```css
/* D1 = deep */
--ground:       var(--pine-teal);
--surface:      var(--hunter-green);
--surface-sunk: #44684b;
--ink:          var(--dust-grey);
--ink-muted:    #9db09f;
--line:         #46644f;
--accent-fill:  var(--dry-sage);
--accent-ink:   #1b2a1f;
--focus-ring:   var(--dust-grey);
```

### 4.3 The measured constraint behind D1

All ratios computed against WCAG 2.x relative luminance.

| Combination | Ratio | Verdict |
|---|---|---|
| `dry-sage` fill, dark ink on it | 6.59:1 | Legible on any ground |
| `dry-sage` fill on **`pine-teal`** ground | 3.98:1 | Passes 1.4.11 — button is findable |
| `dry-sage` fill on **`dust-grey`** ground | 1.58:1 | Fails — button vanishes |
| `pine-teal` fill, light ink on it | 9.08:1 | Excellent; this is config A's button |
| `dust-grey` text on `pine-teal` | 6.31:1 | Body copy on config B |
| `pine-teal` text on `dust-grey` | 6.31:1 | Body copy on config A |
| `fern` as body text on `dust-grey` | 3.11:1 | **Fails** — large sizes only |
| `fern` fill, dark ink on it | 3.36:1 | **Fails** |
| `fern` fill, white ink on it | 4.48:1 | Large text only |

**`fern` cannot carry text in any role.** It is demoted to borders, dividers and hairlines
(`--line`) and must never be used as a background behind copy, or as a text colour at body size.
This is the one casualty of the chosen palette and it should be stated plainly here rather than
discovered during implementation.

**Why config A has no bright button:** a fill bright enough to carry dark ink is necessarily light,
and therefore cannot separate from a light ground. This is arithmetic, not a limitation of this
palette — a search across the whole `fern` hue family at every lightness and saturation returned no
colour satisfying both constraints simultaneously. On a light ground the button must be dark; on a
dark ground it can be bright.

### 4.4 Semantic colours

Order-status colours stay as they are today — they are semantic, not brand, and the existing set is
already legible. They are exempt from the palette block.

---

## 5. Typography

### 5.1 Families

| Role | Family | Weights | Greek |
|---|---|---|---|
| Display | **Sofia Sans** (D2) | 800, 900 | native |
| Body | **Manrope** | 400, 500, 700, 800 | yes |

Both are variable (`wght` axis), so one file per family covers every weight.

```css
--font-display: 'Sofia Sans', 'Noto Sans', system-ui, sans-serif;
--font-body:    'Manrope', 'Noto Sans', system-ui, sans-serif;
```

The fallback is **Noto Sans**, not a bare `sans-serif` — it has full Greek coverage, so a failed
font load degrades to something that still renders Greek correctly.

### 5.2 Self-hosting — required, not optional

**Do not use the Google Fonts CDN.** Two reasons:

1. **GDPR.** Serving Google Fonts from `fonts.gstatic.com` transmits visitor IP addresses to a
   third country. A German court (LG München I, 2022) found this unlawful without consent, and the
   reasoning applies across the EU. Opson is a Greek consumer marketplace; this is a real exposure,
   not a theoretical one.
2. **Performance.** A third-party connection on the critical path, for two files.

Download the `latin`, `latin-ext` and `greek` subsets as variable woff2 and serve them from
`static/fonts/`, with `@font-face` declarations carrying `font-display: swap` and an explicit
`unicode-range` per subset so the browser fetches only what a page needs.

```
static/fonts/
    sofia-sans-latin.woff2
    sofia-sans-greek.woff2
    manrope-latin.woff2
    manrope-greek.woff2
```

`DEPLOY.md` gains a note that these are committed binaries; `collectstatic` picks them up with
everything else.

### 5.3 Type scale

```css
--text-xs:   0.75rem;   /* eyebrows, badges — uppercase, 0.1em tracking */
--text-sm:   0.85rem;   /* meta, captions */
--text-base: 1rem;      /* body */
--text-lg:   1.125rem;  /* lead paragraphs */
--text-xl:   1.35rem;   /* card titles */
--text-2xl:  1.75rem;   /* section titles */
--text-3xl:  2.25rem;   /* page titles */
--text-hero: clamp(2.4rem, 6vw, 4rem);
```

**The weight jump is the mechanic.** Body is 400. Display is 800–900. Nothing sits at 600 pretending
to be emphasis — that middle ground is what makes a page look tentative. Headings additionally take
`letter-spacing: -0.02em` and `text-wrap: balance`.

Prices and any tabular figure take `font-variant-numeric: tabular-nums`.

---

## 6. Components

Every component below is defined once in the stylesheet and referenced by class. No component
carries a literal colour, radius or spacing value.

### 6.1 Buttons

```css
.btn {
  border-radius: var(--radius-full);
  font-family: var(--font-body);
  font-weight: 800;
  padding: var(--space-md) var(--space-lg);
  transition: transform .18s cubic-bezier(.2,.7,.3,1), filter .18s ease;
}
.btn:hover  { transform: scale(1.045); filter: brightness(1.08); }
.btn:active { transform: scale(.99); }
.btn:focus-visible { outline: 3px solid var(--focus-ring); outline-offset: 3px; }
```

Three variants only: `.btn-primary` (accent fill), `.btn-secondary` (surface + border), `.btn-ghost`
(text only). The current `nav-btn-outline` / `nav-btn-filled` / `nav-btn-amber` trio collapses into
these — three near-identical button systems is one reason the header reads as busy.

`prefers-reduced-motion: reduce` disables the transform and the transition.

### 6.2 Cards

`--radius-md`, `--surface` background, `1px` `--line` border, no shadow at rest. Hover is
`scale(1.02)` — **not** a shadow change. Opson currently uses three shadow tokens plus a translate
on hover; that is the generic soft-SaaS card look, and it goes.

Images inside cards: `--radius-xs`, `object-fit: cover`.

### 6.3 Category pills

Already correct in shape. Active state becomes `--accent-fill` + `--accent-ink`; inactive is
transparent with a `--line` border.

### 6.4 Forms

The backend pass moved all four forms onto Django `Form`/`ModelForm` rendered via `{{ field }}`,
with `core.forms.StyledFieldsMixin` attaching `form-input` / `form-select` / `form-textarea`. Those
classes now take `--radius-sm` and the token spacing. The stray `<style>` block in
`templates/auth/signup.html` is deleted — it duplicates `.form-input` with hardcoded values.

Error styling (`.form-error`, `.form-errors`) already exists from the backend pass and moves onto
semantic tokens.

### 6.5 Toast

Keep the existing JS. Restyle to `--radius-md` and `--surface`.

---

## 7. Motion

| Interaction | Treatment |
|---|---|
| Button hover | `scale(1.045)` + `brightness(1.08)` |
| Card hover | `scale(1.02)` |
| Icon button hover | `scale(1.12)` |
| Active / press | `scale(0.99)` |
| Duration | 180ms, `cubic-bezier(.2,.7,.3,1)` |

No entrance animations, no scroll reveals, no parallax. The entire motion budget is spent on hover
and press feedback. Everything sits behind a `prefers-reduced-motion` guard.

---

## 8. Retiring the inline styles

137 `style="..."` attributes across 13 templates, and 137 hardcoded px values. These are the reason
the site cannot be re-skinned by editing tokens today.

Rule: **a template may not contain a `style` attribute.** Each one is replaced by a class in the
stylesheet. Most collapse into a handful of reusable utilities:

```css
.stack        /* flex column + gap — replaces roughly 40 of them */
.row          /* flex row + gap + align */
.grid-auto    /* the repeat(auto-fill, minmax(...)) pattern, used 4× today */
.page-section /* the padding: 36px 24px pattern */
.measure      /* max-width for running text */
```

Worst offenders, in order: `cart.html` (24), `dashboard.html` (22), `order_detail.html` (19),
`my_orders.html` (11), `checkout.html` (11).

**Rename `gaiaroots.css` → `opson.css`.** The file is named after a project this one is no longer
called; the reference in `base.html` moves with it.

---

## 9. Accessibility floor

Non-negotiable, and checkable without running the app:

- Body text ≥ 4.5:1 against its surface; large text ≥ 3:1.
- Every control's fill ≥ 3:1 against the ground behind it (WCAG 1.4.11).
- `:focus-visible` on every interactive element. The current stylesheet sets `outline: none` on
  `button` globally with no replacement, which leaves the site effectively keyboard-unusable today.
- `prefers-reduced-motion` respected on every transform.
- The category nav is a horizontal scroller and must keep keyboard access.

The global `outline: none` is a real bug this pass fixes, not a style preference.

---

## 10. Explicitly out of scope

- Dark mode as a *user setting*. D1 picks one ground; a toggle is a later pass.
- Any change to template HTML structure beyond swapping `style` attributes for classes.
- The hardcoded `REELS` / `EVENTS` / `DEMO_REVIEWS` lists in `catalog/views.py` — still fixtures.
- Responsive rework beyond what the existing grids already do.
- Logo, wordmark, iconography.
- Product photography and art direction.

---

## 11. Build order

1. **Tokens.** Rewrite the `:root` block: palette, semantic layer, radius, spacing, type scale.
   Nothing else changes yet — the site should look almost identical, which is what proves the token
   layer is wired correctly.
2. **Fonts.** Download the four woff2 subsets, add `@font-face`, point `body` at `--font-body`.
   This alone is the single largest visible change in the whole pass.
3. **Radius sweep.** Apply the new scale across all 166 classes.
4. **Buttons.** Collapse the three button systems into `.btn` plus three variants; update templates.
5. **Cards.** Squarer surfaces, scale-on-hover, drop the shadow tokens.
6. **Forms.** Token spacing and radius; delete the `<style>` block in `signup.html`.
7. **Inline-style sweep**, template by template, worst first: `cart`, `dashboard`, `order_detail`,
   `my_orders`, `checkout`, then the rest.
8. **Focus states** and the `prefers-reduced-motion` guards.
9. **Rename** `gaiaroots.css` → `opson.css`; update `base.html`.
10. Manual pass at 360px, 768px and 1280px.

Steps 1–2 are worth doing and reviewing on their own: they are cheap, they carry most of the visible
improvement, and they de-risk everything after them.

---

## 12. Verification

There is no test suite for CSS and none is proposed. Verification is:

- `grep -r 'style="' templates/` returns nothing.
- No literal hex value appears outside the two token blocks in §4.1 and §4.2. The semantic
  block legitimately holds derived tints (`--surface`, `--ink-muted`, `--accent-ink`); component
  rules hold none.
- No raw `px` value appears outside the token definitions.
- The contrast table in §4.3 re-computed against the final tokens.
- A manual check of every page at the three widths above, in Greek.
