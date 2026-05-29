# Report PPTX Design System

If the user requested PPTX output, follow this section. Steps 1 (Report Type) and 2 (Gather Data) from the HTML path still apply -- determine the report type and collect all evidence before building slides.

## PPTX Dependency Check

The generated Python script must begin with:

```python
try:
    from pptx import Presentation
    from pptx.util import Inches, Pt, Emu
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-pptx"])
    from pptx import Presentation
    from pptx.util import Inches, Pt, Emu
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
```

## PPTX Color Palette

Use these `RGBColor` constants throughout the script. Do NOT use ad-hoc hex values.

```python
# ---- Brand ----
CHARCOAL       = RGBColor(0x3A, 0x3A, 0x3A)  # Body text on white
APTEAN_NAVY    = RGBColor(0x05, 0x08, 0x52)  # Headers, strong emphasis
APTEAN_BLUE    = RGBColor(0x24, 0x59, 0xA9)  # Subheadings, links
APTEAN_ORANGE  = RGBColor(0xE6, 0x61, 0x2E)  # Accent, call-to-action
DARK_TEAL      = RGBColor(0x2B, 0x65, 0x83)  # Supporting color
APTEAN_TEAL    = RGBColor(0x54, 0xB3, 0xBE)  # Icons, lighter accents
LIGHT_GRAY     = RGBColor(0xEA, 0xEA, 0xEA)  # Backgrounds, dividers
FOOTER_LINE    = RGBColor(0xE5, 0xE7, 0xEB)  # Footer separator line
TEXT_SECONDARY = RGBColor(0x4B, 0x55, 0x63)  # Footer text, captions
BLACK          = RGBColor(0x00, 0x00, 0x00)
WHITE          = RGBColor(0xFF, 0xFF, 0xFF)

# ---- Severity ----
SEV_CRITICAL   = RGBColor(0xD3, 0x2F, 0x2F)
SEV_HIGH       = RGBColor(0xE6, 0x51, 0x00)
SEV_MEDIUM     = RGBColor(0xF5, 0x7F, 0x17)
SEV_LOW        = RGBColor(0x5C, 0x6B, 0xC0)
SEV_GOOD       = RGBColor(0x2E, 0x7D, 0x32)

# ---- Severity backgrounds (light fills for table cells) ----
SEV_CRITICAL_BG = RGBColor(0xFE, 0xF2, 0xF2)
SEV_HIGH_BG     = RGBColor(0xFF, 0xF7, 0xED)
SEV_MEDIUM_BG   = RGBColor(0xFF, 0xFD, 0xE7)
SEV_LOW_BG      = RGBColor(0xEE, 0xF0, 0xFB)
SEV_GOOD_BG     = RGBColor(0xF0, 0xFD, 0xF4)

# ---- Chart sequence ----
CHART_COLORS = [APTEAN_NAVY, APTEAN_BLUE, DARK_TEAL, APTEAN_TEAL, APTEAN_ORANGE]
```

## PPTX Typography

Titles: "Suisse Intl Condensed" (fallback: "Barlow Condensed"), Bold, 36-44pt, `APTEAN_NAVY`/`BLACK` (content) or `WHITE` (on dark/gradient). Body: "Suisse Intl" (fallback: "Arial"), Regular, 16-20pt, `CHARCOAL`. Code: "Consolas". Footer: 9-10pt, `TEXT_SECONDARY` on white background. Set `run.font.name` to primary font. Never use Calibri.

## PPTX Slide Dimensions

```python
prs = Presentation()
prs.slide_width  = Inches(13.333)  # Widescreen 16:9
prs.slide_height = Inches(7.5)
```

## PPTX Footer Helper

Every slide (except section dividers) must include a clean footer with the Aptean logo image, a thin separator line, and confidentiality text. **No dark background bar.** Define this reusable helper:

```python
from pptx.util import Inches, Pt, Emu, Mm
from pathlib import Path

# Logo paths - resolve from project media/ or .polaris/
LOGO_BLACK = Path("media/aptean-logo-black.png")  # For content slides (white bg)
LOGO_YELLOW_WHITE = Path("media/aptean-logo-yellow-white.png")  # For divider slides (dark bg)

def add_footer(slide, slide_number, prs):
    """Add the standard Aptean footer to a slide (clean, no dark bar)."""
    sw = prs.slide_width
    sh = prs.slide_height
    margin_x = Inches(0.5)
    line_y = sh - Inches(0.5)

    # Thin separator line
    connector = slide.shapes.add_connector(
        1, margin_x, line_y, sw - margin_x, line_y
    )
    connector.line.color.rgb = FOOTER_LINE
    connector.line.width = Pt(0.5)

    # Aptean logo (black, bottom-left)
    if LOGO_BLACK.exists():
        slide.shapes.add_picture(
            str(LOGO_BLACK),
            left=margin_x,
            top=sh - Inches(0.38),
            width=Inches(0.8),
            height=Inches(0.25),
        )

    # Confidentiality text (right side)
    conf_tf = slide.shapes.add_textbox(
        Inches(6), sh - Inches(0.42), sw - Inches(6) - Inches(0.3), Inches(0.35)
    ).text_frame
    conf_tf.word_wrap = False
    conf_run = conf_tf.paragraphs[0].add_run()
    conf_run.text = f"Company Confidential - Internal Distribution Only   |   {slide_number}"
    conf_run.font.name = "Suisse Intl"
    conf_run.font.size = Pt(9)
    conf_run.font.color.rgb = TEXT_SECONDARY
    conf_tf.paragraphs[0].alignment = PP_ALIGN.RIGHT
    conf_tf.paragraphs[0].space_before = Pt(2)
```

For **divider slides** (gradient background), use `LOGO_YELLOW_WHITE` instead of `LOGO_BLACK`, and skip the separator line and confidentiality text.

## PPTX Gradient Helper

Section divider slides use the Aptean signature gradient (steel blue to dusty lavender to soft mauve-pink). Generate it with Pillow if available, otherwise fall back to solid navy.

```python
def make_gradient_bg(width_px=1920, height_px=1080):
    """Return gradient PNG bytes, or None if Pillow is unavailable."""
    try:
        from PIL import Image
    except ImportError:
        return None

    img = Image.new("RGB", (width_px, height_px))
    pixels = img.load()
    # Gradient stops: 0% #477599, 40% #8276AE, 100% #C878BE
    stops = [
        (0.0,  (0x47, 0x75, 0x99)),
        (0.4,  (0x82, 0x76, 0xAE)),
        (1.0,  (0xC8, 0x78, 0xBE)),
    ]
    for x in range(width_px):
        t = x / (width_px - 1)
        for i in range(len(stops) - 1):
            if stops[i][0] <= t <= stops[i + 1][0]:
                seg_t = (t - stops[i][0]) / (stops[i + 1][0] - stops[i][0])
                c0, c1 = stops[i][1], stops[i + 1][1]
                r = int(c0[0] + (c1[0] - c0[0]) * seg_t)
                g = int(c0[1] + (c1[1] - c0[1]) * seg_t)
                b = int(c0[2] + (c1[2] - c0[2]) * seg_t)
                break
        for y in range(height_px):
            pixels[x, y] = (r, g, b)

    import io
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
```

## PPTX Slide Type Patterns

Use these patterns to build slides. Each pattern shows the python-pptx code structure. Substitute `{{PLACEHOLDER}}` values with actual content.

### 1. Title Slide

White background, large bold title, project name subtitle, footer.

```python
from pptx.enum.text import MSO_ANCHOR

slide_layout = prs.slide_layouts[6]  # Blank layout
slide = prs.slides.add_slide(slide_layout)

# Title
title_tf = slide.shapes.add_textbox(
    Inches(0.8), Inches(1.0), Inches(11), Inches(2)
).text_frame
title_tf.word_wrap = True
title_run = title_tf.paragraphs[0].add_run()
title_run.text = "{{REPORT_TITLE}}"
title_run.font.name = "Suisse Intl Condensed"
title_run.font.size = Pt(44)
title_run.font.bold = True
title_run.font.color.rgb = BLACK

# Subtitle / tag line
sub_tf = slide.shapes.add_textbox(
    Inches(0.8), Inches(3.2), Inches(11), Inches(1)
).text_frame
sub_run = sub_tf.paragraphs[0].add_run()
sub_run.text = "{{TAG_LINE}}"
sub_run.font.name = "Suisse Intl"
sub_run.font.size = Pt(20)
sub_run.font.color.rgb = CHARCOAL

# Metadata line (date, project, scope)
meta_tf = slide.shapes.add_textbox(
    Inches(0.8), Inches(4.2), Inches(11), Inches(0.6)
).text_frame
meta_run = meta_tf.paragraphs[0].add_run()
meta_run.text = "{{FULL_DATE}}  |  {{PROJECT_NAME}}  |  {{SCOPE_SUMMARY}}"
meta_run.font.name = "Suisse Intl"
meta_run.font.size = Pt(14)
meta_run.font.color.rgb = APTEAN_BLUE

add_footer(slide, 1, prs)
```

### 2. Section Divider Slide

Gradient background (or solid navy fallback), large white title, NO footer.

```python
slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank

# Gradient background
gradient_bytes = make_gradient_bg()
if gradient_bytes:
    import io
    slide.shapes.add_picture(
        io.BytesIO(gradient_bytes),
        Emu(0), Emu(0),
        prs.slide_width, prs.slide_height,
    )
else:
    # Solid navy fallback
    bg = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Emu(0), Emu(0),
        prs.slide_width, prs.slide_height,
    )
    bg.fill.solid()
    bg.fill.fore_color.rgb = APTEAN_NAVY
    bg.line.fill.background()

# Section title (lower-left quadrant)
sec_tf = slide.shapes.add_textbox(
    Inches(0.8), Inches(4.0), Inches(10), Inches(2.5)
).text_frame
sec_tf.word_wrap = True
sec_run = sec_tf.paragraphs[0].add_run()
sec_run.text = "{{SECTION_TITLE}}"
sec_run.font.name = "Suisse Intl Condensed"
sec_run.font.size = Pt(60)
sec_run.font.bold = True
sec_run.font.color.rgb = WHITE
# NO footer on section dividers
```

### 3. Content Slide

White background with title, body text, and footer.

```python
slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank

# Title
title_tf = slide.shapes.add_textbox(
    Inches(0.8), Inches(0.4), Inches(11.5), Inches(0.9)
).text_frame
title_run = title_tf.paragraphs[0].add_run()
title_run.text = "{{SLIDE_TITLE}}"
title_run.font.name = "Suisse Intl Condensed"
title_run.font.size = Pt(36)
title_run.font.bold = True
title_run.font.color.rgb = APTEAN_NAVY

# Body (add multiple paragraphs for bullet points)
body_tf = slide.shapes.add_textbox(
    Inches(0.8), Inches(1.5), Inches(11.5), Inches(5.0)
).text_frame
body_tf.word_wrap = True

for bullet_text in ["{{BULLET_1}}", "{{BULLET_2}}", "{{BULLET_3}}"]:
    p = body_tf.add_paragraph() if body_tf.paragraphs[0].text else body_tf.paragraphs[0]
    run = p.add_run()
    run.text = bullet_text
    run.font.name = "Suisse Intl"
    run.font.size = Pt(18)
    run.font.color.rgb = CHARCOAL
    p.space_after = Pt(8)

add_footer(slide, slide_number, prs)
```

### 4. Findings Table Slide

Table with severity-colored cells for findings.

```python
slide = prs.slides.add_slide(prs.slide_layouts[6])

# Title
title_tf = slide.shapes.add_textbox(
    Inches(0.8), Inches(0.4), Inches(11.5), Inches(0.9)
).text_frame
title_run = title_tf.paragraphs[0].add_run()
title_run.text = "{{TABLE_TITLE}}"
title_run.font.name = "Suisse Intl Condensed"
title_run.font.size = Pt(36)
title_run.font.bold = True
title_run.font.color.rgb = APTEAN_NAVY

# Table
rows = len(findings) + 1  # +1 for header
cols = 3  # Severity, Finding, Location
table_shape = slide.shapes.add_table(
    rows, cols,
    Inches(0.8), Inches(1.5), Inches(11.5), Inches(0.4 * rows)
)
table = table_shape.table

# Header row
for idx, header in enumerate(["Severity", "Finding", "Location"]):
    cell = table.cell(0, idx)
    cell.text = header
    cell.fill.solid()
    cell.fill.fore_color.rgb = LIGHT_GRAY
    for p in cell.text_frame.paragraphs:
        for r in p.runs:
            r.font.name = "Suisse Intl"
            r.font.size = Pt(11)
            r.font.bold = True
            r.font.color.rgb = APTEAN_NAVY

# Column widths
table.columns[0].width = Inches(1.5)
table.columns[1].width = Inches(7.5)
table.columns[2].width = Inches(2.5)

# Data rows -- severity cell fill uses the severity background colors
SEV_MAP = {
    "CRITICAL": (SEV_CRITICAL, SEV_CRITICAL_BG),
    "HIGH":     (SEV_HIGH, SEV_HIGH_BG),
    "MEDIUM":   (SEV_MEDIUM, SEV_MEDIUM_BG),
    "LOW":      (SEV_LOW, SEV_LOW_BG),
    "GOOD":     (SEV_GOOD, SEV_GOOD_BG),
}

for row_idx, finding in enumerate(findings, start=1):
    sev = finding["severity"].upper()
    fg, bg = SEV_MAP.get(sev, (CHARCOAL, WHITE))

    sev_cell = table.cell(row_idx, 0)
    sev_cell.text = sev
    sev_cell.fill.solid()
    sev_cell.fill.fore_color.rgb = bg
    for r in sev_cell.text_frame.paragraphs[0].runs:
        r.font.color.rgb = fg
        r.font.bold = True
        r.font.size = Pt(10)
        r.font.name = "Suisse Intl"

    table.cell(row_idx, 1).text = finding["title"]
    table.cell(row_idx, 2).text = finding["location"]

    for col in range(1, 3):
        for r in table.cell(row_idx, col).text_frame.paragraphs[0].runs:
            r.font.name = "Suisse Intl"
            r.font.size = Pt(11)
            r.font.color.rgb = CHARCOAL

add_footer(slide, slide_number, prs)
```

### 5. Score Card Slide

Grid of metric shapes for executive summary KPIs.

```python
slide = prs.slides.add_slide(prs.slide_layouts[6])

title_tf = slide.shapes.add_textbox(
    Inches(0.8), Inches(0.4), Inches(11.5), Inches(0.9)
).text_frame
title_run = title_tf.paragraphs[0].add_run()
title_run.text = "Executive Summary"
title_run.font.name = "Suisse Intl Condensed"
title_run.font.size = Pt(36)
title_run.font.bold = True
title_run.font.color.rgb = APTEAN_NAVY

metrics = [
    {"label": "{{LABEL}}", "value": "{{VALUE}}", "color": APTEAN_NAVY},
]

cards_per_row = 4
card_w = Inches(2.7)
card_h = Inches(1.6)
start_x = Inches(0.8)
start_y = Inches(1.8)
gap = Inches(0.25)

for i, m in enumerate(metrics):
    col = i % cards_per_row
    row = i // cards_per_row
    x = start_x + col * (card_w + gap)
    y = start_y + row * (card_h + gap)

    card = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, x, y, card_w, card_h
    )
    card.fill.solid()
    card.fill.fore_color.rgb = RGBColor(0xF8, 0xF9, 0xFB)
    card.line.color.rgb = RGBColor(0xE2, 0xE7, 0xEF)
    card.line.width = Pt(1)

    lbl_tf = slide.shapes.add_textbox(x, y + Inches(0.15), card_w, Inches(0.35)).text_frame
    lbl_run = lbl_tf.paragraphs[0].add_run()
    lbl_run.text = m["label"].upper()
    lbl_run.font.name = "Suisse Intl"
    lbl_run.font.size = Pt(9)
    lbl_run.font.bold = True
    lbl_run.font.color.rgb = RGBColor(0x86, 0x94, 0xA1)
    lbl_tf.paragraphs[0].alignment = PP_ALIGN.CENTER

    val_tf = slide.shapes.add_textbox(x, y + Inches(0.5), card_w, Inches(0.8)).text_frame
    val_run = val_tf.paragraphs[0].add_run()
    val_run.text = m["value"]
    val_run.font.name = "Suisse Intl"
    val_run.font.size = Pt(28)
    val_run.font.bold = True
    val_run.font.color.rgb = m["color"]
    val_tf.paragraphs[0].alignment = PP_ALIGN.CENTER

add_footer(slide, slide_number, prs)
```

### 6. Impact / Quote Slide

Black background, large centered white text.

```python
slide = prs.slides.add_slide(prs.slide_layouts[6])

bg = slide.shapes.add_shape(
    MSO_SHAPE.RECTANGLE, Emu(0), Emu(0),
    prs.slide_width, prs.slide_height,
)
bg.fill.solid()
bg.fill.fore_color.rgb = BLACK
bg.line.fill.background()

quote_tf = slide.shapes.add_textbox(
    Inches(1.5), Inches(2.0), Inches(10), Inches(3.5)
).text_frame
quote_tf.word_wrap = True
quote_run = quote_tf.paragraphs[0].add_run()
quote_run.text = "{{QUOTE_TEXT}}"
quote_run.font.name = "Suisse Intl Condensed"
quote_run.font.size = Pt(48)
quote_run.font.bold = True
quote_run.font.color.rgb = WHITE
quote_tf.paragraphs[0].alignment = PP_ALIGN.CENTER

add_footer(slide, slide_number, prs)
```

## Report-to-Slide Mapping

Header->Title(#1), Methodology->Content(#3), Exec Summary->ScoreCard(#5), Dimension heading->Divider(#2), Findings table->Table(#4, max 8 rows/slide), Narrative->Content(#3), Recommendations->Content(#3), Takeaway->Impact(#6), Disclaimer->Content(#3).

**Order**: Title -> Methodology -> Executive Summary -> (Divider -> Findings -> Narrative) per dimension -> Recommendations -> Takeaway -> Disclaimer.

## EXECUTION STEPS (PPTX)

Steps 1-2 same as HTML. **Step 3**: Write self-contained `.py` script to `.polaris/reports/_generate_{report-slug}.py` with auto-install fallback, color constants, helpers, 16:9 Presentation, slides per mapping order. **Step 4**: Run script, verify `.pptx` created, report both paths.

**PPTX Checklist**: Only RGBColor constants (no ad-hoc hex), title slide complete, dividers use gradient (no footer), all other slides have footer, severity fills in tables, correct fonts, 16:9 dimensions, tables split at 8 rows, no Unicode issues.

**Principles**: Design system is law, evidence-based, actionable, self-contained, non-destructive (`.polaris/reports/` only), cross-platform.
