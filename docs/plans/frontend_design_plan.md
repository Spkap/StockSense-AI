# StockSense — Frontend Design Plan
**From-scratch redesign. Effective: March 2026.**

---

## Part I: Intent Declaration

Before a single pixel or CSS variable is defined, we answer three mandatory questions.

**Who is this human?**
An analytically-minded investor, a technologist with portfolio positions, or a portfolio lab user who actively reads investment research. They open StockSense after hours, usually on a laptop, after having already read news and formed an opinion. They're skeptical of generic AI output. They want to be challenged, not agreed with. They expect precision.

**What must they accomplish?**
Enter a ticker → watch an adversarial debate unfold in real time → evaluate Bull vs. Bear claims → form or update their conviction. For returning users: monitor how their thesis holds against new evidence, and act on kill alerts before damage compounds.

**What should it feel like?**
*Cold, illuminated, authoritative.* Like a Bloomberg terminal if it were designed by a typographer who'd spent time in the research labs of a quantitative hedge fund. Dense where data lives. Spacious where reading happens. Nothing decorative. Every element earns its place.

---

## Part II: Domain Exploration

**Domain vocabulary:** Conviction, Adversarial Debate, Evidence Grade, Thesis, Kill Criteria, Information Asymmetry, Probability-Weighted Verdict, ReAct Loop, Iteration, Signal-to-Noise.

**Color world (from the physical domain):**
- The charcoal of a Bloomberg terminal at 2am
- The amber of a lit trading floor CRT
- The surgical acid-green of a gain indicator on a dark screen
- The flat matte red of a realized loss
- The off-white of a physical research report printed on bond paper
- The cool silver of a OHLCV data table
- Deep neutral navy — the color of institutional confidence

**Signature element:** The **Verdict Spectrum Bar** — a horizontal bar on the Debate view that doesn't show numbers but shows *weight distribution*. Bull mass on the left, Bear mass on the right, separated by a volatile boundary that shifts as evidence streams in. It is visual proof of the adversarial engine working. No other financial tool has one.

**Rejecting three defaults:**
1. **Default:** Light gray dashboard with floating white cards and a blue primary color. → **Alternative:** Near-black canvas (`#0A0A0A`), surfaces distinguished purely by subtle lightness shifts (+3%), borders at 4% white opacity.
2. **Default:** Icon-heavy sidebar navigation with labels. → **Alternative:** A command rail — 48px wide, symbols only, with a floating tooltip. The nav is felt, not seen.
3. **Default:** Loading spinners and placeholder skeleton cards. → **Alternative:** SSE stream renders line-by-line as each reasoning step appears — the *process becoming the experience*, not a loading state before the experience.

---

## Part III: Chosen Aesthetic Direction — "Obsidian Terminal"

**This is not negotiable. Every subsequent decision must validate against this.**

The interface is dark, dense, and precise. It feels like instruments. Not friendly, not cold — *calibrated*. The user is not browsing; they are operating. The design communicates: *we have done the hard work so you can make the hard call.*

- **Dark mode only.** No light mode. Dark is not a preference here — it is the product.
- **Monochrome foundation.** Color is a signal, not decoration. The only colors that appear are semantic (green for Bull/positive, red for Bear/negative/kill) and single amber accent for primary actions.
- **Typography as hierarchy.** Text contrast levels replace decorative elements. Four opacity levels carry all visual weight.
- **Motion is purposeful.** Streaming content reveals line-by-line. Transitions are 180ms max with deceleration easing. No loading spinners — the agent reasoning *is* the animation.

---

## Part IV: Design Token System

### CSS Custom Properties (all surfaces)

```css
/* Base canvas */
--canvas:        #0A0A0A;   /* The deepest surface — page bg */
--surface-1:     #111111;   /* Cards, panes */
--surface-2:     #181818;   /* Elevated: modals, dropdowns */
--surface-3:     #1F1F1F;   /* Inputs — inset feel, darker */

/* Borders — whisper quiet */
--border-subtle: rgba(255, 255, 255, 0.04);
--border-base:   rgba(255, 255, 255, 0.08);
--border-strong: rgba(255, 255, 255, 0.16);
--border-focus:  rgba(245, 180, 0, 0.6);   /* amber focus ring only */

/* Text hierarchy — 4 opacity levels */
--text-primary:  rgba(255, 255, 255, 0.92);  /* Headlines, active data */
--text-secondary:rgba(255, 255, 255, 0.60);  /* Supporting labels */
--text-tertiary: rgba(255, 255, 255, 0.35);  /* Metadata, timestamps */
--text-muted:    rgba(255, 255, 255, 0.18);  /* Disabled, placeholders */

/* Semantic — used as signals only */
--bull:          #22C55E;   /* Bull case, positive evidence */
--bull-dim:      rgba(34, 197, 94, 0.12);
--bear:          #EF4444;   /* Bear case, risk evidence */
--bear-dim:      rgba(239, 68, 68, 0.12);
--kill:          #F97316;   /* Kill criteria triggered */
--kill-dim:      rgba(249, 115, 22, 0.12);

/* Accent — single amber, for primary CTAs only */
--accent:        #F5B400;
--accent-dim:    rgba(245, 180, 0, 0.08);

/* Spacing — 4px base unit */
--space-1: 4px;     /* icon-to-label gaps */
--space-2: 8px;     /* tight component spacing */
--space-3: 12px;    /* internal card padding */
--space-4: 16px;    /* standard component spacing */
--space-6: 24px;    /* section spacing within a pane */
--space-8: 32px;    /* major section separation */
--space-12: 48px;   /* page-level breathing room */

/* Radius: sharp, technical */
--radius-sm: 2px;   /* tags, badges */
--radius-md: 4px;   /* inputs, buttons */
--radius-lg: 6px;   /* cards, panels */
```

### Typography

**Font pairing:**
- **Display / Data:** `"Geist Mono"` — tabular, monospace, hyper-legible at small sizes. Used for all numeric data, tickers, percentage values, and streaming output.
- **Body / Claims:** `"Lora"` — a contemporary serif with writer's authority. Used for thesis text, evidence claims, analyst arguments, and modal prose. The contrast between cold mono data and warm serif claims is the signature typographic signature of this system.

```css
/* Google Fonts import */
@import url('https://fonts.googleapis.com/css2?family=Geist+Mono:wght@300;400;500;600&family=Lora:ital,wght@0,400;0,600;1,400&display=swap');

/* Typography scale */
--type-micro:  11px / 1.4;  /* Labels, axis ticks */
--type-sm:     12px / 1.5;  /* Metadata, timestamps, badge text */
--type-base:   14px / 1.6;  /* Body copy, evidence claims */
--type-md:     16px / 1.5;  /* Card titles, sub-headers */
--type-lg:     20px / 1.3;  /* Section headers */
--type-xl:     28px / 1.2;  /* Page headers */
--type-2xl:    40px / 1.1;  /* Hero ticker display */

/* Usage rules */
/* Lora:      thesis text, claims, analyst arguments, prose */
/* Geist Mono: all numbers, tickers, percentages, streamed AI output */
```

**Letter spacing:**
- Display headers (--type-xl+): `-0.03em` — condensed and authoritative
- Body (--type-base): `0` — natural reading
- Data labels (--type-micro, --type-sm): `+0.06em` — opens up for legibility at small sizes

---

## Part V: Layout Architecture

### Shell Structure

```
┌────────────────────────────────────────────────────┐
│  [48px Rail]  [Main Content Area]                  │
│               ┌────────────────────────────────┐   │
│  ○ Logo       │  Topbar: ticker input + status  │   │
│               ├────────────────────────────────┤   │
│  ⟳ Analysis  │                                 │   │
│  ⚔ Debate    │         Primary Pane            │   │
│  📄 Theses   │                                 │   │
│  🔔 Alerts   ├────────────────────────────────┤   │
│               │  Detail/Context Drawer (slide)  │   │
│  ─────────── └────────────────────────────────┘   │
│  ◉ User                                            │
└────────────────────────────────────────────────────┘
```

- **Command Rail (48px):** Symbol-only icons, no labels. Tooltip on hover (200ms delay). Active route: `--border-strong` left border + `--accent` icon tint. Same background as canvas — not a separate pane color.
- **Topbar (56px):** Sticky. Contains the ticker input command, run status indicator, and session controls. This is the primary interaction point and must be visually dominant.
- **Primary Pane:** Full height, scrollable, content-specific per route.
- **Context Drawer:** Slides in from the right (not a modal overlay) when users click a specific claim or evidence item to expand it. 340px wide, pushes content rather than covering it.

### Depth Strategy: **Borders Only**

No drop shadows anywhere. Surfaces are distinguished entirely through subtle lightness shifts and border-opacity values. This is a strict rule. It reads as a professional instrument interface, not a consumer app.

---

## Part VI: Page-by-Page Design

---

### 1. Analysis Page (Core Loop)

**Layout:** Topbar → Input area → Streaming output pane → Results tabs

**Topbar Input:**
The ticker entry is the *weapon*. A single, large monospaced input field that fills the topbar. When focused, it grows slightly (height transition 100ms). Placeholder: `"AAPL, NVDA, TSLA..."` in `--text-muted`. To the right: a primary CTA button: `"Analyze"` with `--accent` background and deep `#000` text. To the left: a subtle breadcrumb showing last-run ticker and a status dot (green = cached, amber = running).

**Streaming Reasoning View:**
This is the star feature — watching the agent think. Design requirements:
- Each step appears as a new line with a left gutter showing the step number in `Geist Mono` `--text-tertiary`
- Tool calls appear with a mono label: `[TOOL: fetch_news_headlines]` in `--text-tertiary`
- New lines render with a 10ms fade-in — no animation stagger, the *rate of new content* is the animation
- A pulsing cursor `▊` (CSS keyframe on opacity 0→1) sits at the active line to signal the agent is still working
- When complete, the pulsing cursor disappears and a subtle `✓ Complete` badge appears at the top

**Results Tabs:**
After analysis, results appear in a tab strip: `Summary` | `Debate` | `Evidence` | `Sentiment`. The tabs are text-only, no icons. Active tab: `--text-primary` weight with a 1px `--accent` bottom border. Inactive: `--text-tertiary`.

---

### 2. Debate View (Signature Page)

**This is where the design must be exceptional.**

**Layout:** Split-pane horizontal. Bull pane on the left (55% width) and Bear pane on the right (45% width). Not equal — the asymmetry signals that neutrality is *not* the goal.

**The Verdict Spectrum Bar:**
Pinned at the top of the debate view, full width. A horizontal bar, 8px tall, filled with a shifting gradient:
- Left side: `--bull` green
- Right side: `--bear` red
- The division point moves as evidence streams in
- The bar has a subtle inner shadow to give it physical depth
- A numeric label floats above the division point: e.g., `"Bull 61%"` in `Geist Mono`
- The bar animates smoothly as new claims register (CSS `width` transition 600ms ease)

**Bull Pane:**
- `--bull-dim` very subtle left border accent (2px, `--bull` at 30% opacity)
- Agent label: `"BULL ANALYST"` in ALL CAPS `Geist Mono`, `--text-muted`, `--type-micro` letter-spaced
- Claims rendered in `Lora` serif at `--type-base`
- Evidence grades shown as small mono badges: `[HIGH]` in `--bull` on `--bull-dim`
- When a claim is hovered: the opposite pane dims to 50% opacity — forcing focus

**Bear Pane:**
- Mirror of Bull with `--bear-dim` accent
- Claims that directly rebut a Bull claim show a connector line (thin 1px `--border-base` rule) between the two panes

**Synthesizer Section:**
Below the two-pane split, a full-width `Synthesizer` section appears with the probability-weighted verdict. Three scenario boxes: Bull Case / Base Case / Bear Case — each with a large monospaced probability number and a short serif verdict sentence.

---

### 3. Theses Page

**Layout:** Two-column. Left: thesis list (360px). Right: active thesis detail (flexible).

**Thesis List:**
- Compact rows, each showing: ticker (mono), thesis title (serif short), conviction badge, date
- Active thesis: `--border-strong` left rule + `--surface-2` background
- Kill status: if triggered, a `--kill` amber top border on the row + a small pill badge: `"KILL CRITERIA TRIGGERED"`

**Thesis Detail:**
- Full prose view of the thesis rationale in `Lora` at comfortable `--type-base`
- Kill Criteria listed as a definition list: condition | status | last checked
- History timeline at the bottom: each revision shown as a diff-style view (removed text in `--bear-dim`, added text in `--bull-dim`) — this is the *visual memory* of your thinking evolving

---

### 4. Alerts Page

Compact data table. No cards. Just a clean table with tight rows:
- Ticker | Kill Criteria | Triggered At | Analysis Match | Status | Actions
- Triggered rows get a `--kill-dim` background wash across the entire row
- Resolved rows get `--text-muted` for all text — visually faded

---

## Part VII: Component Standards

### Buttons

Two variants only — tertiary text buttons are the default.

| Variant | Background | Text | Border | Use |
|---|---|---|---|---|
| **Primary** | `--accent` | `#000` | none | One per screen. Run Analysis, Create Thesis. |
| **Ghost** | transparent | `--text-secondary` | `--border-base` | All secondary actions |
| **Destructive** | `--bear-dim` | `--bear` | `--bear` 30% | Irreversible deletions only |

All buttons: `--radius-md` (4px), `--type-sm`, 32px height standard.
Hover transition: 120ms. No scale transforms — opacity shift to full primary only.

### Badges / Tags

```
[BULL] [BEAR] [HIGH] [MEDIUM] [LOW] [KILL]
```
Monospaced all-caps, `--type-micro`, `--radius-sm` (2px), semibold. Background is the semantic dim variant. Text is the semantic full color.

### Inputs

- Background: `--surface-3` (slightly darker than card, inset feel)
- Border: `--border-base` by default, `--border-focus` on focus (amber glow)
- Text: `Geist Mono`, `--text-primary`
- Placeholder: `--text-muted`
- No visible label above — placeholder is the label until content exists

### Streaming Output Lines

```
  01  [REASON] Fetching recent headlines for AAPL...
  02  [TOOL: fetch_news_headlines] → 18 results
  03  [REASON] Headlines reviewed. Sentiment is broadly positive.
  04  [TOOL: analyze_sentiment] → confidence: 0.78
  ...
```
Step numbers in `--text-muted`. Label prefixes `[REASON]` / `[TOOL:...]` in `--text-tertiary`. Main text in `--text-secondary`. Completed lines: `--text-secondary`. Active line: `--text-primary` + pulsing cursor.

---

## Part VIII: Motion & Interactions

**Rules:**
1. **Duration max: 200ms** for micro-interactions. 400ms for panel transitions (drawer slide).
2. **Easing:** `cubic-bezier(0.16, 1, 0.3, 1)` — sharp deceleration. Nothing bounces.
3. **No spinners.** Streaming input replaces all loading states.
4. **Focus dimming:** When hovering a claim in the Debate view, non-hovered content drops to `opacity: 0.4`.
5. **The Verdict Bar** is the only element permitted to animate continuously while analysis runs.

**Page entrance:** On route change, content fades in with `opacity: 0 → 1` over 150ms. No slide. No scale.

**Drawer open/close:** `transform: translateX(100%) → translateX(0)`, 300ms, deceleration easing.

**Tab switch:** Content area fades between `opacity: 0 → 1`, 100ms.

---

## Part IX: Implementation Notes

**Stack:** React 19 + TypeScript + Vite (existing). CSS Modules for component styles.

**Font loading:** Preload Lora and Geist Mono in [index.html](file:///Users/sourabhkapure/Developer/Projects/StockSense-Agent/frontend/index.html) with `<link rel="preload">`.

**Motion library:** Use `motion` (formerly Framer Motion) for the Verdict Spectrum Bar animation and the context drawer. Use CSS transitions for everything else — do not reach for JS animation when CSS works.

**Tailwind:** The existing project uses Tailwind. Keep it for utility classes but define all design tokens as CSS custom properties in a global `tokens.css` file. Tokens take precedence over arbitrary Tailwind values.

**Component scope:**
- `<CommandRail />` — navigation, symbol-only icons
- `<Topbar />` — ticker input + status
- `<StreamingPane />` — SSE reasoning output line renderer
- `<DebateView />` — split pane + VerdictBar
- `<VerdictBar />` — the signature animated spectrum
- `<ThesisDetail />` — prose view + kill criteria + history
- `<AlertsTable />` — compact data table
- `<ContextDrawer />` — sliding evidence expansion panel

**No new routing library needed.** Extend the existing React Router setup.

---

## Part X: Design Validation Checks

Before considering any implementation complete, verify:

- [ ] **Swap test:** If the typeface were swapped to Inter/Roboto, would the design feel meaningfully different? (It should.)
- [ ] **Squint test:** Blur your eyes. Can you identify hierarchy? Does anything jump out harshly?
- [ ] **Signature test:** Can you point to 5 specific elements expressing the "Obsidian Terminal" signature? (VerdictBar, Mono/Serif pairing, 4-step text opacity hierarchy, streaming step rendering, command rail with no labels)
- [ ] **Token test:** Read the CSS variable names aloud. Do `--canvas`, `--bull-dim`, `--kill`, `--text-muted` sound like they belong to this product?
- [ ] **Intent test:** Does the page feel *surgical and authoritative* — or has it drifted toward generic dashboard?

---

*This document is the source of truth for all frontend implementation decisions. No design choice should be made that cannot be traced back to the Intent Declaration in Part I.*
