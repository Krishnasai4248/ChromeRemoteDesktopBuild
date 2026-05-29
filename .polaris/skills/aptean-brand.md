# Aptean Brand Design System - Unified Guardrail

You are building software for Aptean. Apply these design rules by default in ALL UI,
frontend, and presentation work. No explicit instruction is needed.

This guardrail covers three contexts:
1. **Light Theme (AppCentral)** - Web applications with white/light backgrounds
2. **Dark Theme (Enterprise)** - Web applications with dark backgrounds
3. **PPTX Presentation Style** - PowerPoint slide decks

Choose the appropriate theme based on context. When in doubt, use the Light Theme
for web applications and the PPTX style for presentations.

---

## Bundled Resources

This skill includes official Aptean font and screenshot files:

```
fonts/
  SuisseIntl-Book.otf              # Body text (regular weight 400)
  SuisseIntl-BookItalic.otf        # Body text italic
  SuisseIntl-Bold.otf              # Bold body text, card titles (weight 700)
  SuisseIntl-BoldItalic.otf        # Bold italic
  SuisseIntlCond-Regular.otf       # Condensed headings regular (weight 400)
  SuisseIntlCond-RegularItalic.otf # Condensed headings italic
  SuisseIntlCond-Bold.otf          # Condensed headings bold (weight 700)
  SuisseIntlCond-BoldItalic.otf    # Condensed headings bold italic

assets/
  resolve360-task-list.png          # Reference: task list UI pattern
  resolve360-case-detail.png        # Reference: case detail layout
  sales-smart-workspace.png         # Reference: action hub pattern
  time-dashboard.png                # Reference: time entry dashboard
```

---

## Shared Typography (All Themes)

### Font Families

| Role | Font Family | Fallback Stack | Usage |
|------|------------|----------------|-------|
| Headings / Display | Suisse Intl Condensed | Barlow Condensed, Arial Narrow, sans-serif | Page titles, section headers, slide titles |
| Body / UI | Suisse Intl | -apple-system, BlinkMacSystemFont, Segoe UI, Arial, sans-serif | Body text, buttons, labels, inputs, table cells |
| Monospace | SF Mono, Fira Code | Consolas, monospace | Code blocks, data values |

### Rules

- Suisse Intl Condensed = headings ONLY -- never use for body, labels, or buttons
- Suisse Intl = all other text (body, buttons, labels, inputs, table cells, badges)
- Never substitute Inter, Roboto, or other generic fonts as primary
- Use the bundled OTF files; never use Google Fonts or CDN alternatives when bundled fonts are available

### @font-face Declarations

Copy font files from `.polaris/skills/aptean-brand/fonts/` to your project's font directory and declare:

```css
@font-face {
  font-family: 'Suisse Intl';
  src: url('/fonts/SuisseIntl-Book.otf') format('opentype');
  font-weight: 400;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: 'Suisse Intl';
  src: url('/fonts/SuisseIntl-BookItalic.otf') format('opentype');
  font-weight: 400;
  font-style: italic;
  font-display: swap;
}
@font-face {
  font-family: 'Suisse Intl';
  src: url('/fonts/SuisseIntl-Bold.otf') format('opentype');
  font-weight: 700;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: 'Suisse Intl';
  src: url('/fonts/SuisseIntl-BoldItalic.otf') format('opentype');
  font-weight: 700;
  font-style: italic;
  font-display: swap;
}
@font-face {
  font-family: 'Suisse Intl Condensed';
  src: url('/fonts/SuisseIntlCond-Regular.otf') format('opentype');
  font-weight: 400;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: 'Suisse Intl Condensed';
  src: url('/fonts/SuisseIntlCond-RegularItalic.otf') format('opentype');
  font-weight: 400;
  font-style: italic;
  font-display: swap;
}
@font-face {
  font-family: 'Suisse Intl Condensed';
  src: url('/fonts/SuisseIntlCond-Bold.otf') format('opentype');
  font-weight: 700;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: 'Suisse Intl Condensed';
  src: url('/fonts/SuisseIntlCond-BoldItalic.otf') format('opentype');
  font-weight: 700;
  font-style: italic;
  font-display: swap;
}

h1, h2, h3 {
  font-family: 'Suisse Intl Condensed', 'Barlow Condensed', 'Arial Narrow', sans-serif;
}
body, p, span, button, input, select, textarea, label, td, th {
  font-family: 'Suisse Intl', -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
}
```

### Type Scale

| Element | Font | Weight | Size | Line Height | Letter Spacing |
|---------|------|--------|------|-------------|----------------|
| Page title | Suisse Intl Condensed | 700 | 28-32px | 1.2 | -0.02em |
| Section header | Suisse Intl Condensed | 700 | 22-26px | 1.25 | -0.01em |
| Card title | Suisse Intl | 700 | 16-18px | 1.3 | 0 |
| Body text | Suisse Intl | 400 | 14px | 1.5 | 0 |
| Secondary/meta | Suisse Intl | 400 | 12-13px | 1.4 | 0 |
| Column header | Suisse Intl | 700 | 11-12px | 1.2 | 0.05em (uppercase) |
| Badge/chip | Suisse Intl | 500 | 12px | 1.3 | 0 |
| Link text | Suisse Intl | 400 | inherit | inherit | 0 |

---

## Light Theme (AppCentral)

Use this theme for Aptean AppCentral web applications. Backgrounds are white or light
gray. Teal (#1A7B7E) is the primary interactive color.

### Core Principle: My Tasks First

Every application screen prioritizes ACTIONABLE WORK over dashboards or analytics.
- Task lists are the primary landing view (not graphs or KPI tiles)
- Severity and urgency are always visible (color-coded chips and left-border indicators)
- Users see what needs their attention immediately on login
- Progressive disclosure: summary first, detail on demand

### Color Tokens (CSS Custom Properties)

#### Backgrounds

| Token | Hex | Usage |
|-------|-----|-------|
| `--bg-page` | `#FAFAFA` | Page / app background |
| `--bg-card` | `#FFFFFF` | Card and content area background |
| `--bg-sidebar` | `#FFFFFF` | Navigation sidebar background |
| `--bg-sidebar-active` | `#1A7B7E` | Active nav item background |
| `--bg-filter-bar` | `#F5F5F5` | Filter bar band |
| `--bg-today` | `#FEF9E7` | Today highlight (time dashboard) |
| `--bg-teal-subtle` | `#E6F4F4` | Teal-tinted hover / selected state |

#### Text

| Token | Hex | Usage |
|-------|-----|-------|
| `--color-gray-900` | `#111827` | Primary headings and body text |
| `--color-gray-700` | `#374151` | Strong secondary text |
| `--color-gray-600` | `#4B5563` | Secondary labels, meta text |
| `--color-gray-500` | `#6B7280` | Placeholder, disabled, tertiary |
| `--color-gray-400` | `#9CA3AF` | Icon default state |

#### Brand / Teal Palette

| Token | Hex | Usage |
|-------|-----|-------|
| `--color-teal-50` | `#E6F4F4` | Teal tint bg, active pill bg |
| `--color-teal-100` | `#C0E5E5` | Light teal backgrounds |
| `--color-teal-200` | `#8FD0D1` | Subtle teal highlights |
| `--color-teal-300` | `#5CBCBE` | Focus rings, active tab outline |
| `--color-teal-400` | `#2EA3A5` | Mid teal |
| `--color-teal-500` | `#1A7B7E` | Primary buttons, links, active nav |
| `--color-teal-600` | `#156668` | Dark teal |
| `--color-teal-700` | `#0F5F61` | Button hover state |
| `--color-teal-800` | `#0A4345` | Button active/pressed state |
| `--color-teal-900` | `#062D2E` | Deepest teal |

#### Borders and Shadows

| Token | Value | Usage |
|-------|-------|-------|
| `--border-default` | `#E5E7EB` | Card, input, separator borders |
| `--border-focus` | `#1A7B7E` | Focused input or selected element |
| `--shadow-card` | `0 1px 3px rgba(0,0,0,0.08)` | Card elevation |
| `--shadow-dropdown` | `0 4px 12px rgba(0,0,0,0.12)` | Dropdown menus |
| `--shadow-modal` | `0 8px 24px rgba(0,0,0,0.16)` | Modal dialogs |

#### Severity (left-border and icon use only)

| Token | Hex | Usage |
|-------|-----|-------|
| `--color-severity-critical` | `#DC2626` | 4px left border, red icon |
| `--color-severity-high` | `#F59E0B` | 4px left border, amber icon |
| `--color-severity-medium` | `#F3D573` | 4px left border, yellow-gold icon |
| `--color-severity-low` | `#6B7280` | 4px left border, gray icon |

#### Status

| Token | Hex | Usage |
|-------|-----|-------|
| `--color-status-new` | `#3B82F6` | Blue badge |
| `--color-status-active` | `#1A7B7E` | Teal badge |
| `--color-status-overdue` | `#DC2626` | Red text / icon |
| `--color-status-resolved` | `#16A34A` | Green badge |
| `--color-status-closed` | `#6B7280` | Gray badge |

#### Category

| Token | Hex | Usage |
|-------|-----|-------|
| `--color-category-internal` | `#7C3AED` | Solid purple badge |
| `--color-category-external` | `#F97316` | Solid orange badge |

#### Semantic Actions (inline icon buttons)

| Token | Hex | Usage |
|-------|-----|-------|
| `--color-action-confirm` | `#16A34A` | Green checkmark |
| `--color-action-snooze` | `#F59E0B` | Amber clock |
| `--color-action-dismiss` | `#6B7280` | Gray x |
| `--color-action-danger` | `#DC2626` | Red destructive |

### Layout Shell

- **Global header**: 56-64px height, white background, bottom border `--border-default`
  - Left: Aptean logo + "Aptean AppCentral" wordmark (bold, dark text)
  - Right: icon buttons + language pill + user avatar (teal-500 circle with initials)
- **Left sidebar**: 220px (expanded) / 56px (icon-only collapsed), white background
  - Right border: 1px solid `--border-default`
  - Active nav item: background `--bg-sidebar-active`, white text and icon
  - Inactive nav item: gray-700 text, hover background gray-100
- **Content area**: flex-1, overflow-y auto, padding 24px, background `--bg-page`
- **Page max-width**: 1440px centered for wide screens

### Component Conventions

#### Buttons

| Variant | Style |
|---------|-------|
| Primary | bg `--color-teal-500`, text white, border-radius 8px, padding 10px 20px. Hover: `--color-teal-700`. Focus: ring 2px `--color-teal-300`. Disabled: opacity 0.5. |
| Secondary | White bg, 1px solid `--border-default`, text `--color-teal-500`. Hover: bg gray-50, border `--color-teal-300`. |
| Icon button | 32x32px or 40x40px, transparent bg. Hover: bg gray-100. Icon: gray-500, hover gray-700. |
| Danger | bg `--color-action-danger`, text white. |
| Text button | teal-500 color, no border, underline on hover. |

#### Data Tables

- Table header: height 44px, transparent or gray-50 bg, uppercase 11px gray-500, border-bottom 1px solid `--border-default`
- Body rows: white bg, border-bottom 1px solid `--border-default`, height 56-64px
  - Hover: bg gray-50
  - Severity left border: 4px colored strip (do NOT color the whole row)
- ID/link column: teal-500, font-weight 500, underline on hover

#### Task Tab Bar (My Tasks First navigation)

- Inactive tab: gray-600 text, transparent background
- Active tab: background teal-500 pill, white text, white count badge
- Count badge: rounded pill, gray-200 background (inactive) or white (active)
- Right-aligned CTA: primary button with "+" icon

#### Filter Bar

- Container: gray-50 background, border-top and border-bottom 1px solid `--border-default`
- Search input: 40px height, 1px solid `--border-default`, border-radius 8px
- Filter dropdowns: bordered, rounded, chevron-down icon

#### Cards / Content Sections

- Background: white
- Border: 1px solid `--border-default`, border-radius 12px
- Shadow: `--shadow-card`
- Padding: 16px

#### Modals / Dialogs

- Overlay: rgba(0, 0, 0, 0.4)
- Content: white bg, border-radius 12px, max-width 560px, `--shadow-modal`
- Header: padding 20px 24px, border-bottom `--border-default`, title 18px 600
- Footer: padding 16px 24px, border-top `--border-default`, action buttons right-aligned

#### Form Inputs

- Background: white
- Border: 1px solid `--border-default`, border-radius 8px, height 40px, padding 0 12px
- Placeholder: gray-400
- Focus: border-color `--border-focus`, box-shadow 0 0 0 2px rgba(26,123,126,0.15)

#### Severity Left Borders (severity-only -- do not repurpose)

- Critical: 4px solid #DC2626
- High: 4px solid #F59E0B
- Medium: 4px solid #F3D573
- Low: 4px solid #6B7280

#### Badges / Pills

- Solid: filled background, white or dark text
- Outlined: transparent background, border 1px solid, matching text color
- Soft: light-colored background, darker matching text
- Size default: height 24px, padding 2px 12px, font-size 12px, border-radius 12px

### Shadcn/ui CSS Variable Mapping

When using Shadcn/ui, override these variables in your globals.css:

```css
@layer base {
  :root {
    --background:            0   0% 100%;   /* white page background */
    --foreground:          222  47%  11%;   /* dark gray text (#111827) */
    --card:                  0   0% 100%;   /* white card background */
    --card-foreground:     222  47%  11%;
    --popover:               0   0% 100%;
    --popover-foreground:  222  47%  11%;
    --primary:             182  66%  30%;   /* teal-500 (#1A7B7E) */
    --primary-foreground:    0   0% 100%;   /* white text on teal */
    --secondary:           220  14%  96%;   /* light gray */
    --secondary-foreground: 215 28%  17%;
    --muted:               220  14%  96%;
    --muted-foreground:    215  16%  47%;   /* gray-500 */
    --accent:              183  67%  94%;   /* teal-50 (#E6F4F4) */
    --accent-foreground:   182  66%  30%;   /* teal-500 */
    --destructive:           0  84%  60%;   /* red (#DC2626) */
    --destructive-foreground: 0  0% 100%;
    --border:              220  13%  91%;   /* gray-200 (#E5E7EB) */
    --input:               220  13%  91%;
    --ring:                182  66%  30%;   /* teal-500 focus ring */
    --radius: 0.5rem;
  }
}
```

### Tailwind Config Extension

```js
theme: {
  extend: {
    colors: {
      aptean: {
        'teal-50':  '#E6F4F4',
        'teal-300': '#5CBCBE',
        'teal-500': '#1A7B7E',
        'teal-700': '#0F5F61',
        'teal-800': '#0A4345',
        'gray-50':  '#FAFAFA',
        'gray-100': '#F5F5F5',
        'gray-200': '#E5E7EB',
        'gray-500': '#6B7280',
        'gray-600': '#4B5563',
        'gray-900': '#111827',
        'sev-critical': '#DC2626',
        'sev-high':     '#F59E0B',
        'sev-medium':   '#F3D573',
        'sev-low':      '#6B7280',
        'status-new':      '#3B82F6',
        'status-resolved': '#16A34A',
        'status-closed':   '#6B7280',
        'cat-internal':    '#7C3AED',
        'cat-external':    '#F97316',
      }
    }
  }
}
```

### Light Theme Anti-Patterns (NEVER do these)

- DO NOT use dark backgrounds (#0C1013 or similar) -- this is a LIGHT theme
- DO NOT use pure black (#000000) for backgrounds -- use white or gray-50
- DO NOT use #54B3BE as the primary button color -- use teal-500 (#1A7B7E) for light theme
- DO NOT use severity colors (red, amber, yellow) outside severity indicators
- DO NOT repurpose category colors (purple, orange) for non-category use
- DO NOT make dashboards or analytics the default landing view -- task lists come first
- DO NOT hide severity or urgency information -- always visible in task lists
- DO NOT use rounded corners > 12px (too consumer-app-like)
- DO NOT use bright gradients or decorative illustrations

---

## Dark Theme (Enterprise)

Use this theme for Aptean enterprise applications that require a dark UI. The dark theme
uses desaturated blue-gray tones with `#54B3BE` teal as the primary accent.

### Color Tokens (CSS Custom Properties)

#### Backgrounds

| Token | Hex | Usage |
|-------|-----|-------|
| `--aptean-bg-darkest` | `#0C1013` | Deepest background (sidebars, navbars) |
| `--aptean-bg-dark` | `#151618` | Primary dark background |
| `--aptean-bg-panel` | `#1D262D` | Panel/card backgrounds |
| `--aptean-bg-elevated` | `#252E37` | Elevated surfaces, hover states |
| `--aptean-bg-surface` | `#39434D` | Table headers, toolbars |
| `--aptean-bg-muted` | `#646D76` | Muted/disabled backgrounds |

#### Text

| Token | Hex | Usage |
|-------|-----|-------|
| `--aptean-text-primary` | `#FFFFFF` | Primary text on dark |
| `--aptean-text-secondary` | `#A9B2B9` | Secondary/muted text on dark |
| `--aptean-text-tertiary` | `#646D76` | Tertiary/disabled text on dark |
| `--aptean-text-dark` | `#161616` | Primary text on light surfaces |
| `--aptean-text-dark-secondary` | `#666666` | Secondary text on light surfaces |

#### Brand / Accent

| Token | Hex | Usage |
|-------|-----|-------|
| `--aptean-teal` | `#54B3BE` | Primary accent -- links, active states, focus rings, primary buttons |
| `--aptean-teal-dark` | `#2B6583` | Darker teal -- selected states |
| `--aptean-blue` | `#2459A9` | Secondary accent, informational |
| `--aptean-navy` | `#050852` | Deep navy, strong emphasis |
| `--aptean-orange` | `#E6612E` | Warnings, CTAs |
| `--aptean-yellow` | `#FFFC3B` | Logo accent ONLY (Aptean triangle -- never use elsewhere) |

#### Status

| Token | Hex | Usage |
|-------|-----|-------|
| `--aptean-success` | `#4CAF50` | Success, positive |
| `--aptean-warning` | `#FF9800` | Warning, caution |
| `--aptean-error` | `#F44336` | Error, destructive |
| `--aptean-info` | `#2196F3` | Informational |

#### Borders and Shadows

| Token | Value | Usage |
|-------|-------|-------|
| `--aptean-border-dark` | `#2E3842` | Borders on dark backgrounds |
| `--aptean-border-light` | `#E0E0E0` | Borders on light surfaces |
| `--aptean-border-focus` | `#54B3BE` | Focus rings |
| `--aptean-shadow-sm` | `0 1px 3px rgba(0,0,0,0.3)` | Subtle elevation |
| `--aptean-shadow-md` | `0 4px 12px rgba(0,0,0,0.4)` | Medium elevation |
| `--aptean-shadow-lg` | `0 8px 24px rgba(0,0,0,0.5)` | Strong elevation |

### Spacing Grid (8px base)

| Token | Value |
|-------|-------|
| `--aptean-space-xs` | 4px |
| `--aptean-space-sm` | 8px |
| `--aptean-space-md` | 16px |
| `--aptean-space-lg` | 24px |
| `--aptean-space-xl` | 32px |
| `--aptean-space-2xl` | 48px |

### Border Radius Scale

| Token | Value |
|-------|-------|
| `--aptean-radius-sm` | 4px |
| `--aptean-radius-md` | 6px |
| `--aptean-radius-lg` | 8px |
| `--aptean-radius-xl` | 12px |

### Responsive Breakpoints

| Breakpoint | Behavior |
|------------|----------|
| >= 1440px | Full sidebar (240px), spacious content |
| 1024-1439px | Compact sidebar, reduced padding |
| 768-1023px | Collapsed sidebar (56px icons-only), overlay on click |
| < 768px | No sidebar -- bottom nav or hamburger, full-width content |

### Component Conventions

#### Buttons

| Variant | Background | Text | Border |
|---------|-----------|------|--------|
| Primary | `#54B3BE` | `#FFFFFF` | none |
| Primary hover | `#49A0AA` | `#FFFFFF` | none + box-shadow 0 2px 8px rgba(84,179,190,0.3) |
| Secondary | transparent | `#A9B2B9` | 1px solid #39434D |
| Secondary hover | `#252E37` | `#FFFFFF` | 1px solid #39434D |
| Ghost | transparent | `#54B3BE` | none |
| Danger | `#F44336` | `#FFFFFF` | none |
| Disabled | `#252E37` | `#646D76` | none |

Button sizing: padding 8px 16px, border-radius 4px, font-size 13px, font-weight 700, min-height 34px.
Small: padding 4px 12px, font-size 12px, min-height 28px.
Large: padding 10px 24px, font-size 14px, min-height 40px.

#### Form Inputs

- Background: `--aptean-bg-panel` (#1D262D)
- Border: 1px solid `--aptean-border-dark` (#2E3842), border-radius 4px
- Text: `--aptean-text-primary` (#FFFFFF), font-size 14px
- Placeholder: `--aptean-text-tertiary` (#646D76)
- Focus: border-color `--aptean-border-focus` (#54B3BE), box-shadow 0 0 0 2px rgba(84,179,190,0.2)
- Disabled: bg `--aptean-bg-elevated`, text tertiary, cursor not-allowed

#### Data Tables

- Header: bg `--aptean-bg-surface` (#39434D), text secondary, 12px bold uppercase, letter-spacing 0.04em
- Rows: bg `--aptean-bg-panel` (#1D262D), border-bottom 1px solid `--aptean-border-dark`
- Row hover: bg `--aptean-bg-elevated` (#252E37)
- Selected row: bg rgba(84,179,190,0.08), left box-shadow inset 3px 0 0 `--aptean-teal`
- Sortable columns: active sort uses `--aptean-teal` color

#### Sidebar

- Width: 240px (expanded), 56px (collapsed)
- Background: `--aptean-bg-darkest` (#0C1013)
- Border-right: 1px solid `--aptean-border-dark`
- Active item: bg `--aptean-bg-panel`, text `--aptean-teal`, left border 3px solid `--aptean-teal`, font-weight 700
- Inactive: text secondary, hover bg `--aptean-bg-panel`

#### Cards

- Background: `--aptean-bg-panel` (#1D262D)
- Border: 1px solid `--aptean-border-dark`, border-radius `--aptean-radius-md` (6px)
- Padding: 20px
- Shadow: `--aptean-shadow-sm`

#### Side Panels

- Slide-in from right edge
- Narrow: 360px, Wide: 560px
- Background: `--aptean-bg-panel`
- Border-left: 1px solid `--aptean-border-dark`
- Overlay: rgba(0,0,0,0.4)

#### Modals

- Overlay: rgba(0,0,0,0.6)
- Background: `--aptean-bg-panel`
- Border: 1px solid `--aptean-border-dark`, border-radius `--aptean-radius-lg` (8px)
- Min-width: 400px, max-width: 600px
- Animation: fade-in scale from 0.95 to 1, 0.2s ease

#### Toast Notifications

- Background: `--aptean-bg-elevated` (#252E37)
- Border-radius: `--aptean-radius-md` (6px)
- Left border: 4px solid (success=#4CAF50, error=#F44336, warning=#FF9800, info=#2196F3)
- Shadow: `--aptean-shadow-md`

### Dark Theme Anti-Patterns (NEVER do these)

- DO NOT use light/white backgrounds as default -- this is a DARK theme
- DO NOT use #1A7B7E as primary accent -- use #54B3BE for dark theme
- DO NOT use #FFFC3B yellow anywhere except the Aptean logo triangle
- DO NOT use bright, saturated neon colors -- keep tones desaturated and professional
- DO NOT use gratuitous animations -- transitions should be fast (0.15s) and subtle
- DO NOT substitute Arial, Inter, or Roboto when Suisse Intl fonts are available

---

## PPTX Presentation Style

Use this when creating PowerPoint presentations for Aptean. All decks must follow
these guidelines for brand consistency.

### Color Palette

| Role | Hex | Name | Usage |
|------|-----|------|-------|
| Primary Dark | `#3A3A3A` | Charcoal | Body text on white backgrounds |
| Deep Navy | `#050852` | Aptean Navy | Headers on light slides, strong emphasis |
| Blue | `#2459A9` | Aptean Blue | Subheadings, links, secondary emphasis |
| Orange | `#E6612E` | Aptean Orange | Accent highlights, call-to-action elements |
| Dark Teal | `#2B6583` | Dark Teal | Supporting color, chart accents |
| Light Teal | `#54B3BE` | Aptean Teal | Icons, lighter accents, chart series |
| Yellow | `#FFFC3B` | Aptean Yellow | Logo triangle ONLY -- never as general accent |
| Light Gray | `#EAEAEA` | Light Gray | Backgrounds, subtle dividers |
| Footer Line | `#E5E7EB` | Footer Separator | Thin separator line above footer area |
| Footer Text | `#4B5563` | Secondary Text | Footer confidentiality text, captions |

### Signature Gradient

For section divider slides. A soft, muted gradient -- not neon or vivid:

- Start: `#477599` (muted steel blue)
- Mid (40%): `#8276AE` (dusty lavender)
- End: `#C878BE` (soft mauve-pink)

DO NOT use bright/saturated colors like #42A2DA, #9E28D2, or #EA338E -- those are too vivid.

### PPTX Typography

| Element | Font | Weight | Size (pt) | Color |
|---------|------|--------|-----------|-------|
| Slide title (content) | Suisse Intl Condensed | Bold | 36-44 | #000000 or #050852 |
| Large impact title | Suisse Intl Condensed | Bold | 60-80 | #FFFFFF (on dark/gradient) |
| Section header | Suisse Intl Condensed | Bold | 28-36 | #FFFFFF (on gradient) |
| Subheading | Suisse Intl | Bold | 20-24 | #3A3A3A or #050852 |
| Body text | Suisse Intl | Regular | 16-20 | #3A3A3A |
| Captions / footnotes | Suisse Intl | Regular | 10-12 | #3A3A3A at 60% opacity |
| Footer text | Suisse Intl | Regular | 9-10 | #FFFFFF (on footer bar) |

Fallbacks: Suisse Intl Condensed -> Barlow Condensed. Suisse Intl -> Arial.

### Slide Types

1. **Title Slide** -- White bg, bold title top-left, photo strip middle, Aptean logo bottom-left, dark footer
2. **Section Divider** -- Full gradient bg, large white text lower-left, optional photo upper-right, NO footer bar
3. **Content Slide** -- White bg, title top-left, body left-aligned, standard footer
4. **Impact/Quote Slide** -- Solid black bg, centered large white text, standard footer
5. **People/Team Slide** -- White bg, row of headshots, names below, standard footer
6. **Two-Column Slide** -- White bg, title top-left, two equal columns, standard footer

### Document Classification

Ask the user the distribution intent before generating any document:

| Intent | Footer Text | Banner |
|--------|------------|--------|
| **Internal Only** (default) | Company Confidential - Internal Distribution Only | COMPANY CONFIDENTIAL - INTERNAL DISTRIBUTION ONLY |
| **Do Not Distribute** | Company Confidential - Do Not Distribute | COMPANY CONFIDENTIAL - DO NOT DISTRIBUTE |
| **Customer Facing** | Aptean Confidential | *(no banner)* |

### Footer Specification

Every slide (except section dividers) includes a clean footer (no dark background bar):
- Thin separator line (`#E5E7EB`, 0.5pt) above the footer area
- Left side: Aptean logo image (`aptean-logo-black.png` on white bg, `aptean-logo-yellow-white.png` on dark bg)
- Right side: Classification text + " | [page number]" in `#4B5563`
- Never render "aptean" as text - always use the logo image file
- Logo appears exactly once per slide - never in both header and footer

### Chart Colors (in order)

`#050852`, `#2459A9`, `#2B6583`, `#54B3BE`, `#E6612E`

- Clean white chart backgrounds
- Muted axis labels in #3A3A3A
- Subtle grid lines in #EAEAEA
- No gratuitous 3D effects

### Spacing and Layout

- Slide margins: 0.5" minimum on all sides
- Title top margin: 0.3-0.5" from top edge
- Content gap below title: 0.3-0.5"
- Between content blocks: 0.3" minimum
- Footer bar height: 0.4", anchored to bottom
- Content must not overlap the footer bar -- keep above y: 5.1"

### PPTX Anti-Patterns (NEVER do these)

- DO NOT use #FFFC3B yellow anywhere except the Aptean logo triangle
- DO NOT use bright neon gradients -- the Aptean gradient is muted and professional
- DO NOT use fonts other than Suisse Intl / Suisse Intl Condensed (with fallbacks)
- DO NOT omit the footer bar from content and impact slides
- DO NOT use gratuitous 3D effects on charts
- DO NOT center body text -- left-align unless it is a single-line callout or title
