# NOVA AI — Design System & HUD UI Specification
> Neural Orchestrated Voice Assistant with Autonomous Intelligence  
> Visual Identity + HUD Interface Design Reference

---

## 1. Brand Identity

### 1.1 Project Name & Wordmark
- **Full Name:** NOVA AI — Neural Orchestrated Voice Assistant with Autonomous Intelligence
- **Display Name:** `NOVA`
- **Subtitle / Tagline:** `NEURAL ORCHESTRATED VOICE ASSISTANT`
- **Wordmark Font:** Segoe UI, system-ui, sans-serif
- **Wordmark Weight:** 700 (Bold)
- **Letter Spacing:** 14px (wordmark), 5px (subtitle)
- **Subtitle Opacity:** 0.7

---

## 2. Color Palette (Finalized — Do Not Change)

| Role | Name | Hex | Usage |
|------|------|-----|-------|
| Background (Primary) | Deep Cosmic | `#0D0D0D` | HUD background, window fill |
| Background (Logo) | Midnight Void | `#0E0B1F` | Logo circle bg, app icon bg |
| Primary Brand | Violet Core | `#7B6CF6` | Rings, arcs, borders, orbit dots, subtitle text |
| Light Brand | Lavender | `#A89AF8` | Logo symbol fill (primary), app icon symbol |
| Highlight | Pale Violet | `#C4B8FC` | Logo center node, wordmark mid-stop, light details |
| Accent (Teal) | Neural Teal | `#5DCAA5` | Second orbit dot, wordmark end gradient, teal accents |
| HUD Accent (Cyan) | Cyber Cyan | `#00D4FF` | Status indicators, waveform active, response text, clock |
| Dark Brand | Deep Indigo | `#3D35A8` | Light lockup wordmark text |
| Dark Brand Alt | Medium Indigo | `#5B4FD4` | Light lockup symbol fill |

> **Rule:** `#0D0D0D` is the HUD window background. `#0E0B1F` is the logo circle background. Never swap these.

---

## 3. Logo (Finalized)

### 3.1 Logo Structure
The NOVA logo is a **neural convergence mark** — a frameless circular emblem representing signal, intelligence, and convergence. It consists of:

**Outer Layer (Aura):**
- Radial glow pulse: `#7B6CF6` at 25% → transparent, animates via `pulse-ring` keyframe (opacity 0.18 → 0.32 → 0.18, 3s ease-in-out infinite)
- Two faint concentric guide rings at r=148 and r=118, stroke `#7B6CF6`, width 0.6, opacity 0.2 / 0.15

**Orbit Layer:**
- 3 violet orbit dots on outer ring (r=148): sizes 4px / 2.5px / 3px, opacity 0.9 / 0.5 / 0.7 — rotate clockwise `orbit` 6s linear infinite
- 2 teal orbit dots on inner ring (r=118): sizes 3px / 2px, opacity 0.8 / 0.5 — rotate counter-clockwise `orbit-rev` 9s linear infinite
- All orbit dots use `transform-origin: 200px 200px`

**Inner Disc:**
- Circle r=88 fill `#0E0B1F` (solid, not transparent)
- Border ring r=86 stroke `#7B6CF6`, width 1, opacity 0.4

**Central Symbol (Neural Convergence Mark):**
- Upper wing: upward-pointing chevron/arrow shape — `M 200 138 L 175 160 L 175 195 L 200 162 L 225 195 L 225 160 Z`
- Lower wing: downward-pointing delta shape — `M 178 202 L 162 240 L 200 218 L 238 240 L 222 202 L 200 222 Z`
- Both wings filled with gradient `symbol-fill`: `#A89AF8` (0%) → `#5B4FD4` (100%), diagonal
- Lower wing opacity 0.75
- Core node: circle cx=200 cy=192 r=5 fill `#C4B8FC`
- Entire symbol animates via `breathe` keyframe (opacity 0.85 → 1 → 0.85, 4s ease-in-out infinite)

**Signal Arc:**
- Subtle sine-wave path: `M 120 200 Q 160 155 200 200 Q 240 245 280 200`
- Stroke `#7B6CF6`, width 1.5, opacity 0.3, linecap round, no fill

**Wordmark (below mark):**
- `NOVA` — gradient left-to-right: `#A89AF8` → `#C4B8FC` → `#5DCAA5`
- Font size 48, weight 700, letter-spacing 14, anchor middle
- Subtitle: `NEURAL ORCHESTRATED VOICE ASSISTANT` — fill `#7B6CF6`, opacity 0.7, size 11, letter-spacing 5

### 3.2 Logo Source
- **Implementation:** SVG (inline HTML/Python canvas render)
- **Source file:** `nova_ai_logo.html` (project root reference)
- **Do not rasterize** — always render as SVG for crispness at all sizes

### 3.3 Logo Variants

| Variant | Shape | Background | Use Case |
|---------|-------|------------|----------|
| **Animated Mark** | Full 400×400 SVG | Transparent | HUD center panel, splash screen |
| **App Icon (Circle)** | 80×80 circle | `#0E0B1F` | Taskbar, system tray |
| **App Icon (Rounded Rect)** | 80×80 rx=20 | `#0E0B1F` | Windows app icon |
| **Light Lockup** | Symbol + wordmark horizontal | `#F4F3FF` | Light backgrounds, docs |
| **Dark Lockup** | Symbol + wordmark horizontal | `#0E0B1F` | Dark panels, HUD header |

---

## 4. Typography

| Element | Font | Size | Weight | Color | Letter-Spacing |
|---------|------|------|--------|-------|----------------|
| HUD Clock | Courier New / monospace | 22px | 400 | `#00D4FF` | 3px |
| Status Label | Courier New / monospace | 12px | 400 | `#7B6CF6` | 2px |
| Command Text | Courier New / monospace | 13px | 400 | `#C4B8FC` | 1px |
| Response Text | Courier New / monospace | 12px | 400 | `#00D4FF` | 0.5px |
| Section Labels | Courier New / monospace | 10px | 400 | `#7B6CF6` (70% opacity) | 2px |
| Ticker Text | Courier New / monospace | 11px | 400 | `#5DCAA5` | 1px |
| Wordmark | Segoe UI / system-ui | 48px | 700 | Gradient | 14px |
| Subtitle | Segoe UI / system-ui | 11px | 400 | `#7B6CF6` | 5px |

> **HUD Rule:** All HUD text uses monospace only. No proportional fonts inside the overlay window.

---

## 5. HUD Interface — Full Specification

### 5.1 Window Properties

| Property | Value |
|----------|-------|
| Type | Frameless, borderless (no title bar, no resize handles) |
| Always-on-top | Yes — `Tkinter: root.wm_attributes('-topmost', True)` |
| Transparency | Semi-transparent — `root.wm_attributes('-alpha', 0.92)` |
| Position | Docked right side of screen, full screen height |
| Width | 320px fixed |
| Height | 100% of screen height |
| Background | `#0D0D0D` |
| Resizable | No |
| Draggable | No (fixed dock position) |

### 5.2 HUD Layout (Top to Bottom)

```
┌─────────────────────────────┐
│        NOVA LOGO AREA       │  ← Animated SVG mark (clickable)
│   [Animated Waveform Ring]  │
│        Status Dot + Label   │
├─────────────────────────────┤
│  🕐  22:45:07               │  ← Live clock (cyan, monospace)
├─────────────────────────────┤
│  ── LAST COMMAND ──         │  ← Section label (violet, faded)
│  > play lo-fi music         │  ← User command (lavender)
│  ── RESPONSE ──             │
│  Opening YouTube...         │  ← NOVA response (cyan)
│  (last 5 exchanges)         │
├─────────────────────────────┤
│  ── REMINDERS ──            │  ← Scrolling ticker (teal)
│  10:00 PM — Call Ali  ↔    │
├─────────────────────────────┤
│  [Gesture Cam Feed]         │  ← Optional mini OpenCV window
│  Detected: ✋ Open Palm     │  ← Gesture label (violet)
└─────────────────────────────┘
```

### 5.3 Logo + Waveform Zone (Top Panel)

This is the most visually prominent element of the HUD — the animated NOVA logo acts as the **primary state display and waveform host**.

**Layout:**
- Logo SVG rendered at 200×200px (scaled from 400×400 viewBox), centered in the top panel
- The logo's existing `pulse-ring` and `breathe` animations always run as base idle state
- **Waveform overlays the logo** — rendered as matplotlib `FuncAnimation` on a transparent canvas, positioned concentrically over the logo's outer ring area

**Waveform Design:**
- Shape: Circular waveform ring — audio amplitude bars radiate outward from a circle at r≈90px from center
- Bar count: 64 bars, evenly spaced around 360°
- Bar color: `#00D4FF` (Cyber Cyan) at full opacity during active states
- Bar height: Driven by real audio amplitude data (or sinusoidal mock during idle)
- Minimum bar height (idle): 4px — very subtle, barely visible
- Background of waveform canvas: fully transparent (`alpha=0`)

**Waveform States:**

| NOVA State | Waveform Behavior | Bar Color | Opacity |
|------------|------------------|-----------|---------|
| 🔴 Sleeping | Near-flat, very slow pulse, bars ~4px | `#7B6CF6` | 30% |
| 🟡 Listening | Medium amplitude, irregular bars, rapid refresh | `#00D4FF` | 85% |
| 🟢 Processing | Slow rotating sweep pattern, bars mid-height | `#5DCAA5` | 70% |
| 🔵 Speaking | High amplitude bars, driven by TTS audio levels | `#00D4FF` | 100% |

**Click Interaction:**
- Clicking anywhere on the logo/waveform zone triggers manual NOVA activation (alternative to "Hey NOVA")
- Visual feedback: brief flash of all bars to max height for 200ms on click
- Cursor: pointer hand on hover

### 5.4 Status Indicator

- Position: Below logo, centered
- Format: `● SLEEPING` / `● LISTENING` / `● PROCESSING` / `● SPEAKING`
- Dot colors: 🔴 `#FF4444` / 🟡 `#FFD700` / 🟢 `#00FF88` / 🔵 `#00D4FF`
- Font: Courier New, 12px, letter-spacing 3px
- Dot blinks at 1Hz during LISTENING state

### 5.5 Clock Display

- Position: Below status indicator
- Format: `HH:MM:SS` — updates every second via `after(1000, update_clock)`
- Font: Courier New, 22px, `#00D4FF`
- Letter-spacing: 3px
- No date shown in clock row (date available on voice query only)

### 5.6 Command / Response Panel

- Shows last 5 command-response pairs, newest at top
- Each pair:
  - `>` prefix + command text — color `#C4B8FC`, size 13px
  - Response text — color `#00D4FF`, size 12px, slight indent
  - Thin 1px separator line `#7B6CF6` at 20% opacity between pairs
- Panel scrolls if overflow (scrollbar hidden, mouse-wheel enabled)
- Max visible: 5 pairs without scrolling
- Text wraps at panel width with padding 12px each side

### 5.7 Reminders Ticker

- Position: Bottom of command panel, above gesture cam
- Horizontal scrolling ticker (marquee effect via Tkinter `after` loop)
- Format: `⏰ HH:MM — Reminder text` per item
- Color: `#5DCAA5` (Neural Teal)
- Font: Courier New, 11px
- Scroll speed: 2px per 30ms frame
- If no reminders: shows `── NO PENDING REMINDERS ──` in `#7B6CF6` at 40% opacity

### 5.8 Gesture Camera Feed (Optional)

- Position: Bottom of HUD panel
- Size: 280×160px (16:9 crop of camera feed)
- Border: 1px solid `#7B6CF6` at 40% opacity
- Overlay text: detected gesture name in `#5DCAA5`, bottom-left, 10px monospace
- Toggle: Enabled/disabled via `config.json` → `"gesture_cam_hud": true/false`
- If disabled: panel collapses, space filled by reminders ticker expansion

### 5.9 HUD Separator Lines

- Between each section: 1px horizontal rule
- Color: `#7B6CF6`, opacity 20%
- Margin: 0 (edge to edge within HUD width)

### 5.10 HUD Padding & Spacing

| Element | Padding |
|---------|---------|
| Logo zone | 16px top, 8px bottom |
| Clock | 4px top, 4px bottom |
| Section labels | 8px top, 4px bottom |
| Command/response pairs | 6px vertical between pairs |
| Ticker bar | 6px vertical |
| Horizontal padding (all text) | 12px left, 12px right |

---

## 6. Waveform — Technical Implementation Notes

### 6.1 Matplotlib FuncAnimation Config

```python
# Waveform canvas setup
fig = Figure(figsize=(2.0, 2.0), dpi=100, facecolor='none')
fig.patch.set_alpha(0.0)
ax = fig.add_subplot(111, polar=True)
ax.set_facecolor('none')
ax.set_ylim(0, 100)
ax.axis('off')

# 64 bars around 360 degrees
theta = np.linspace(0, 2 * np.pi, 64, endpoint=False)
bars = ax.bar(theta, heights, width=(2*np.pi/64)*0.8,
              color='#00D4FF', alpha=0.85, bottom=30)
```

### 6.2 State-Driven Amplitude

```python
# nova_state: 'sleeping' | 'listening' | 'processing' | 'speaking'
def get_amplitudes(nova_state, tick):
    if nova_state == 'sleeping':
        return np.abs(np.sin(theta + tick * 0.02)) * 6 + 2
    elif nova_state == 'listening':
        return np.random.uniform(10, 60, 64)
    elif nova_state == 'processing':
        return np.roll(np.abs(np.sin(np.linspace(0, 4*np.pi, 64))) * 40, tick % 64)
    elif nova_state == 'speaking':
        return np.random.uniform(30, 95, 64)  # or real audio level data
```

### 6.3 FuncAnimation

```python
ani = FuncAnimation(fig, update_waveform, interval=50,  # 20 FPS
                    blit=True, cache_frame_data=False)
```

### 6.4 Canvas Placement Over Logo

- Logo SVG rendered first as background label (Tkinter Label with PhotoImage or HTML render)
- Matplotlib canvas placed over it with `place()` geometry manager, centered
- Canvas background: `None` / transparent
- Z-order: logo behind, waveform canvas on top

---

## 7. Animation Summary

| Animation | Element | Duration | Easing | Trigger |
|-----------|---------|----------|--------|---------|
| `pulse-ring` | Logo outer glow | 3s | ease-in-out | Always |
| `orbit` | 3 violet orbit dots | 6s | linear | Always |
| `orbit-rev` | 2 teal orbit dots | 9s | linear | Always |
| `breathe` | Central symbol | 4s | ease-in-out | Always |
| Waveform bars | Circular bar chart | 50ms (20fps) | — | State-driven |
| Status dot blink | Listening indicator | 500ms | step | Listening only |
| Click flash | All waveform bars | 200ms | instant | Logo click |
| Ticker scroll | Reminders text | 30ms | linear | Always if reminders |

---

## 8. HUD Window Initialization Sequence

1. Window created frameless, always-on-top, alpha 0.92, right-docked
2. Background filled `#0D0D0D`
3. Logo SVG rendered (idle animation begins immediately)
4. Matplotlib waveform canvas placed over logo (sleeping state)
5. Status label set to `● SLEEPING`
6. Clock starts ticking
7. Memory queried → startup greeting spoken via TTS
8. Status transitions: SLEEPING → SPEAKING (greeting) → SLEEPING
9. Reminders ticker populated from SQLite reminders table
10. Gesture cam feed initialized if `gesture_cam_hud: true` in config

---

## 9. Folder Structure Reference (Design Assets)

```
nova-ai/
│
├── assets/
│   ├── logo/
│   │   ├── nova_logo_animated.svg      ← Full animated mark (400×400)
│   │   ├── nova_icon_circle.svg        ← App icon circle (80×80)
│   │   ├── nova_icon_rounded.svg       ← App icon rounded rect (80×80)
│   │   ├── nova_lockup_dark.svg        ← Dark lockup (horizontal)
│   │   └── nova_lockup_light.svg       ← Light lockup (horizontal)
│   │
│   └── fonts/
│       └── (system fonts used — no custom font files required)
│
├── ui/
│   ├── hud.py                          ← Main HUD Tkinter window (Module 23)
│   ├── waveform.py                     ← Matplotlib waveform component
│   ├── ticker.py                       ← Scrolling reminders ticker
│   └── logo_renderer.py               ← SVG logo render helper
│
└── design.md                           ← This file
```

---

## 10. Design Rules — Do Not Violate

1. **Never use white backgrounds** inside the HUD — only `#0D0D0D` or `#0E0B1F`
2. **Never use proportional fonts** (Arial, Times, etc.) in HUD text — monospace only
3. **Never change the color palette** — all 9 colors are finalized and locked
4. **Never rasterize the logo** — always SVG render
5. **Never show a title bar** — HUD is frameless at all times
6. **Always maintain alpha 0.92** — HUD must be slightly transparent
7. **Waveform must always be active** — even in sleeping state (very subtle pulse, not flat-zero)
8. **Logo is always visible and centered** at top of HUD — it is the primary brand anchor
9. **Status indicator must update within 100ms** of state change
10. **Clicking the logo/waveform area always triggers NOVA activation**

---

## 11. Context.md Entry — design.md

```
FILE: design.md
ACTION: Created (new file)
LOCATION: Project root
CHANGE: Full design system specification created covering color palette, logo anatomy,
        HUD layout, waveform states + implementation, typography, animation table,
        folder structure, and design rules.
BEFORE: File did not exist
AFTER: Complete UI/UX reference document for all HUD and brand implementation
REASON: Single source of truth for all visual decisions — ensures HUD (Module 23),
        logo rendering, and waveform are implemented consistently across all modules
```