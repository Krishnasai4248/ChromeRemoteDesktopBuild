#!/usr/bin/env python3
"""Generate branded release notes PDF for Aptean Polaris.

Parses CHANGELOG.md dynamically. RCs fold into their parent release.
Full releases are grouped by minor version series for compact history.

Standalone script - does NOT import from specify_cli.
Requires: reportlab (pip install reportlab)
"""

import argparse
import re
import sys
import tomllib
from collections import OrderedDict
from pathlib import Path

try:
    from reportlab.lib.colors import HexColor
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        PageBreak,
        HRFlowable,
        KeepTogether,
    )
except ImportError:
    print(
        "ERROR: reportlab is required. Install it with: pip install reportlab",
        file=sys.stderr,
    )
    sys.exit(1)

# ---------------------------------------------------------------------------
# Aptean brand colors
# ---------------------------------------------------------------------------
APTEAN_TEAL = HexColor("#54B3BE")
APTEAN_TEAL_DARK = HexColor("#3D8A93")
APTEAN_NAVY = HexColor("#050852")
APTEAN_BLUE = HexColor("#2459A9")
APTEAN_ORANGE = HexColor("#E6612E")
APTEAN_SUCCESS = HexColor("#2E7D32")
APTEAN_TEXT = HexColor("#1A2332")
APTEAN_TEXT_SEC = HexColor("#546E7A")
APTEAN_BANNER_BG = HexColor("#3D8A93")  # Teal dark for confidential banner
WHITE = HexColor("#FFFFFF")
LIGHT_GRAY = HexColor("#F5F5F5")
BORDER_GRAY = HexColor("#E0E0E0")
HIGHLIGHT_BG = HexColor("#E8F5F7")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# This script should be run from the repo root:
#   python src/specify_cli/scripts/generate_release_notes_pdf.py --version 2026.3.4
# It resolves paths relative to cwd (repo root), not the script location.
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path.cwd()
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"
CHANGELOG_PATH = REPO_ROOT / "CHANGELOG.md"

# ---------------------------------------------------------------------------
# Register Suisse Intl TTF fonts (converted from OTF via otf2ttf)
# ---------------------------------------------------------------------------
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont as _TTFont

_FONT_DIR = REPO_ROOT / ".polaris" / "reports" / "fonts"
_FONT_MAP = {
    "SuisseIntl": "SuisseIntl-Book.ttf",
    "SuisseIntl-Bold": "SuisseIntl-Bold.ttf",
    "SuisseIntl-Italic": "SuisseIntl-BookItalic.ttf",
    "SuisseIntlCond": "SuisseIntlCond-Regular.ttf",
    "SuisseIntlCond-Bold": "SuisseIntlCond-Bold.ttf",
}
_suisse_ok = True
for _name, _file in _FONT_MAP.items():
    _path = _FONT_DIR / _file
    if _path.exists():
        try:
            pdfmetrics.registerFont(_TTFont(_name, str(_path)))
        except Exception:
            _suisse_ok = False
    else:
        _suisse_ok = False

if _suisse_ok:
    _F_TITLE = "SuisseIntlCond-Bold"
    _F_HEAD = "SuisseIntlCond-Bold"
    _F_BODY = "SuisseIntl"
    _F_BOLD = "SuisseIntl-Bold"
    _F_ITALIC = "SuisseIntl-Italic"
else:
    _F_TITLE = "Helvetica-Bold"
    _F_HEAD = "Helvetica-Bold"
    _F_BODY = "Helvetica"
    _F_BOLD = "Helvetica-Bold"
    _F_ITALIC = "Helvetica-Oblique"

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 20 * mm
CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN

# Alternating colors for version series headers
SERIES_COLORS = [APTEAN_TEAL_DARK, APTEAN_BLUE, APTEAN_NAVY, APTEAN_TEAL, APTEAN_ORANGE]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def get_version() -> str:
    with open(PYPROJECT_PATH, "rb") as f:
        return tomllib.load(f)["project"]["version"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate branded Aptean Polaris release notes PDF."
    )
    parser.add_argument("--output", "-o", type=Path, default=None)
    parser.add_argument(
        "--version", "-v", type=str, default=None,
        help="Version to generate notes for (default: read from pyproject.toml)",
    )
    return parser.parse_args()


def _strip_emoji(text: str) -> str:
    """Remove all emoji and special Unicode that reportlab can't render."""
    # Remove non-BMP (surrogate pairs)
    text = re.sub(r'[^\x00-\uFFFF]', '', text)
    # Remove common emoji/symbols in BMP range (dingbats, arrows, symbols, misc)
    text = re.sub(r'[\u2190-\u21FF\u2600-\u27BF\u2B50-\u2B55\u2796\uFE00-\uFE0F\u200D]', '', text)
    return text.strip()


def _is_rc(version: str) -> bool:
    return bool(re.search(r"(rc|a|b)\d*$", version))


def _base_version(version: str) -> str:
    """Strip rc/a/b suffix: 2026.3.1rc3 -> 2026.3.1"""
    return re.sub(r"(rc|a|b)\d*$", "", version)


def _series_key(version: str) -> str:
    """Group key: 2026.2.9 -> 2026.2.x, 0.13.28 -> 0.13.x"""
    base = _base_version(version)
    parts = base.split(".")
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}.x"
    return base


# ---------------------------------------------------------------------------
# CHANGELOG parser
# ---------------------------------------------------------------------------
def parse_changelog() -> list[dict]:
    """Parse CHANGELOG.md into list of {version, date, sections: {heading: [items]}}."""
    with open(CHANGELOG_PATH, encoding="utf-8") as f:
        content = f.read()

    releases = []
    # Split on ## [version] - date
    chunks = re.split(r"^## \[", content, flags=re.MULTILINE)

    for chunk in chunks[1:]:  # skip preamble
        header_match = re.match(r"([^\]]+)\]\s*-\s*(\d{4}-\d{2}-\d{2})", chunk)
        if not header_match:
            continue
        version = header_match.group(1)
        date = header_match.group(2)
        body = chunk[header_match.end():]

        sections: dict[str, list[str]] = {}
        current_section = "Changes"

        for line in body.split("\n"):
            section_match = re.match(r"^### (.+)", line)
            if section_match:
                current_section = _strip_emoji(section_match.group(1).strip())
                if current_section not in sections:
                    sections[current_section] = []
                continue
            # Bullet items
            item_match = re.match(r"^- \*\*(.+?)\*\*:?\s*(.*)", line)
            if item_match:
                title = _strip_emoji(item_match.group(1))
                desc = _strip_emoji(item_match.group(2).strip())
                if current_section not in sections:
                    sections[current_section] = []
                sections[current_section].append({"title": title, "desc": desc})
            elif re.match(r"^- (.+)", line):
                plain = _strip_emoji(re.match(r"^- (.+)", line).group(1).strip())
                if current_section not in sections:
                    sections[current_section] = []
                sections[current_section].append({"title": plain, "desc": ""})

        releases.append({
            "version": version,
            "date": date,
            "sections": sections,
            "is_rc": _is_rc(version),
            "base_version": _base_version(version),
        })

    return releases


def merge_rc_releases(releases: list[dict]) -> list[dict]:
    """Merge RC releases into their parent version. Returns full releases only."""
    merged: OrderedDict[str, dict] = OrderedDict()

    for rel in releases:
        base = rel["base_version"]
        if base not in merged:
            merged[base] = {
                "version": base,
                "date": rel["date"],  # latest date wins (RCs come first)
                "sections": {},
                "is_rc": rel["is_rc"],
                "rc_versions": [],
            }
        entry = merged[base]
        if rel["is_rc"]:
            entry["rc_versions"].append(rel["version"])
            # Keep the latest RC date as the release date
            entry["date"] = rel["date"]
            entry["is_rc"] = True  # mark as upcoming if any RC

        # Merge sections
        for section, items in rel["sections"].items():
            if section not in entry["sections"]:
                entry["sections"][section] = []
            # Deduplicate by title
            existing_titles = {i["title"] for i in entry["sections"][section]}
            for item in items:
                if item["title"] not in existing_titles:
                    entry["sections"][section].append(item)
                    existing_titles.add(item["title"])

    return list(merged.values())


def group_by_series(releases: list[dict]) -> OrderedDict[str, list[dict]]:
    """Group releases by minor version series."""
    groups: OrderedDict[str, list[dict]] = OrderedDict()
    for rel in releases:
        key = _series_key(rel["version"])
        if key not in groups:
            groups[key] = []
        groups[key].append(rel)
    return groups


# ---------------------------------------------------------------------------
# PDF building blocks
# ---------------------------------------------------------------------------
def _confidential_banner() -> Table:
    style = ParagraphStyle(
        "Banner", fontName=_F_BOLD, fontSize=9,
        textColor=WHITE, alignment=1, leading=12,
    )
    t = Table(
        [[Paragraph("COMPANY CONFIDENTIAL - INTERNAL DISTRIBUTION ONLY", style)]],
        colWidths=[CONTENT_WIDTH], rowHeights=[8 * mm],
    )
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), APTEAN_BANNER_BG),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def _make_table(headers, rows, col_widths):
    th = ParagraphStyle("TH", fontName=_F_BOLD, fontSize=8, textColor=WHITE, leading=10)
    td = ParagraphStyle("TD", fontName=_F_BODY, fontSize=8, textColor=APTEAN_TEXT, leading=11)
    data = [[Paragraph(h, th) for h in headers]]
    for row in rows:
        data.append([Paragraph(c, td) for c in row])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), APTEAN_TEAL_DARK),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_GRAY),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            cmds.append(("BACKGROUND", (0, i), (-1, i), LIGHT_GRAY))
    t.setStyle(TableStyle(cmds))
    return t


def _highlight_box(text: str) -> Table:
    style = ParagraphStyle(
        "Highlight", fontName=_F_BODY, fontSize=9,
        textColor=APTEAN_TEXT, leading=13, alignment=0,
    )
    t = Table(
        [[Paragraph(text, style)]],
        colWidths=[CONTENT_WIDTH - 6 * mm],
    )
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HIGHLIGHT_BG),
        ("BOX", (0, 0), (-1, -1), 1, APTEAN_TEAL),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    return t


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
TITLE_STYLE = ParagraphStyle(
    "RNTitle", fontName=_F_BOLD, fontSize=32,
    textColor=APTEAN_NAVY, alignment=1, leading=38, spaceAfter=2 * mm,
)
SUBTITLE_STYLE = ParagraphStyle(
    "RNSubtitle", fontName=_F_BODY, fontSize=16,
    textColor=APTEAN_TEXT_SEC, alignment=1, leading=22, spaceAfter=4 * mm,
)
VERSION_STYLE = ParagraphStyle(
    "RNVersion", fontName=_F_BOLD, fontSize=12,
    textColor=WHITE, alignment=1, leading=16,
)
SECTION_STYLE = ParagraphStyle(
    "RNSection", fontName=_F_BOLD, fontSize=16,
    textColor=APTEAN_NAVY, spaceBefore=6 * mm, spaceAfter=3 * mm,
)
BODY_STYLE = ParagraphStyle(
    "RNBody", fontName=_F_BODY, fontSize=9.5,
    textColor=APTEAN_TEXT, alignment=4, leading=13, spaceAfter=3 * mm,
)

# Compact styles for history
HIST_VERSION = ParagraphStyle(
    "HistVer", fontName=_F_BOLD, fontSize=10,
    textColor=APTEAN_NAVY, leading=13, spaceBefore=3 * mm, spaceAfter=1 * mm,
)
HIST_ITEM = ParagraphStyle(
    "HistItem", fontName=_F_BODY, fontSize=8,
    textColor=APTEAN_TEXT, leading=10, leftIndent=4, spaceAfter=0.5 * mm,
)
HIST_ITEM_BOLD = ParagraphStyle(
    "HistItemBold", fontName=_F_BOLD, fontSize=8,
    textColor=APTEAN_TEXT, leading=10,
)


# Section display names for PDF (no emoji - reportlab can't render them)
SECTION_LABELS = {
    "Added": "New Features",
    "Fixed": "Improvements and Fixes",
    "Changed": "Changes",
    "Removed": "Removed",
    "Security": "Security",
    "Deprecated": "Deprecated",
    "Changes": "Changes",
}

# Strip emoji prefix from changelog section names (e.g., "✨ Added" -> "Added")
def _clean_section_name(name: str) -> str:
    """Remove emoji prefixes and map to display label."""
    cleaned = _strip_emoji(name)
    # Also strip leading non-ASCII chars and whitespace
    cleaned = re.sub(r'^[^\x20-\x7E]+\s*', '', cleaned).strip()
    # Try exact match first, then partial
    if cleaned in SECTION_LABELS:
        return SECTION_LABELS[cleaned]
    for key, label in SECTION_LABELS.items():
        if key.lower() in cleaned.lower():
            return label
    return cleaned


# ---------------------------------------------------------------------------
# Page 1: Cover
# ---------------------------------------------------------------------------
def build_cover(version: str, current_release: dict) -> list:
    """Build the What's New pages (after the gradient cover)."""
    elements: list = []

    # Page title
    elements.append(Paragraph("What's New", ParagraphStyle(
        "WNTitle", fontName=_F_TITLE, fontSize=22,
        textColor=APTEAN_NAVY, leading=28, spaceAfter=6 * mm,
    )))

    # Version badge
    display_ver = version if not _is_rc(version) else f"{_base_version(version)} (Pre-release)"
    v_table = Table(
        [[Paragraph(f"v{display_ver}", ParagraphStyle(
            "VBadge", fontName=_F_BOLD, fontSize=11, textColor=WHITE, alignment=1, leading=14,
        ))]],
        colWidths=[60 * mm], rowHeights=[8 * mm],
    )
    v_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), APTEAN_TEAL_DARK),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(v_table)
    elements.append(Spacer(1, 2 * mm))

    elements.append(Paragraph(
        current_release["date"],
        ParagraphStyle("WNDate", fontName=_F_BODY, fontSize=10,
                       textColor=APTEAN_TEXT_SEC, leading=14, spaceAfter=6 * mm),
    ))
    elements.append(
        HRFlowable(width="80%", thickness=1, color=BORDER_GRAY, spaceAfter=5 * mm)
    )

    # Summary box - find sections by partial match (handles emoji-stripped keys)
    def _count_section(sections, *keys):
        for k, v in sections.items():
            for key in keys:
                if key.lower() in k.lower():
                    return len(v)
        return 0

    total_added = _count_section(current_release["sections"], "Added")
    total_changed = _count_section(current_release["sections"], "Changed")
    total_fixed = _count_section(current_release["sections"], "Fixed")
    parts = []
    if total_added:
        parts.append(f"<b>{total_added}</b> new feature{'s' if total_added != 1 else ''}")
    if total_changed:
        parts.append(f"<b>{total_changed}</b> change{'s' if total_changed != 1 else ''}")
    if total_fixed:
        parts.append(f"<b>{total_fixed}</b> fix{'es' if total_fixed != 1 else ''}")
    if parts:
        elements.append(_highlight_box(
            f"Version {current_release['version']} includes {', '.join(parts)}."
        ))
        elements.append(Spacer(1, 4 * mm))

    # Section styles
    sec_style = ParagraphStyle(
        "WNSec", fontName=_F_HEAD, fontSize=12,
        textColor=APTEAN_TEAL_DARK, spaceBefore=5 * mm, spaceAfter=2 * mm,
    )
    item_style = ParagraphStyle(
        "WNItem", fontName=_F_BODY, fontSize=9,
        textColor=APTEAN_TEXT, leading=13, leftIndent=6 * mm,
        spaceAfter=2.5 * mm,
    )

    # Render each section
    for section, items in current_release["sections"].items():
        label = _clean_section_name(section)
        elements.append(Paragraph(label, sec_style))
        elements.append(
            HRFlowable(width="100%", thickness=1.5, color=APTEAN_TEAL, spaceAfter=3 * mm)
        )

        for item in items:
            title, desc = _simplify_item(item["title"], item["desc"])
            title = _escape_xml(title)
            desc = _escape_xml(desc)

            # Truncate long descriptions to first sentence
            if desc and len(desc) > 180:
                first_sentence = re.split(r'(?<=[.!])\s', desc)[0]
                if len(first_sentence) < 180:
                    desc = first_sentence
                else:
                    desc = desc[:177] + "..."
            if desc:
                elements.append(Paragraph(
                    f"-  <b>{title}</b> - {desc}", item_style,
                ))
            else:
                elements.append(Paragraph(
                    f"-  <b>{title}</b>", item_style,
                ))

    return elements


def _escape_xml(text: str) -> str:
    """Escape XML special chars for reportlab Paragraph."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _simplify_item(title: str, desc: str) -> tuple[str, str]:
    """Rewrite a changelog item into plain English for the PDF.

    Strips code references, function names, file paths, and internal
    jargon. Returns (clean_title, clean_desc).
    """
    # Remove (NNN) spec references from title
    title = re.sub(r"\s*\(\d{3}\)\s*", " ", title).strip()

    # Replace backtick-wrapped code with plain text (keep the content, strip backticks)
    desc = re.sub(r"`([^`]+)`", r"\1", desc)
    # Remove migration references
    desc = re.sub(r"(?:Added |New )?[Mm]igration\s+`?\w+`?\.?\s*", "", desc)
    # Remove file/module paths (src/foo/bar.py, .polaris/foo)
    desc = re.sub(r"\bsrc/\S+", "", desc)
    desc = re.sub(r"\.polaris/\S+", "", desc)
    # Remove function-like references: word_word()
    desc = re.sub(r"\b\w+_\w+\(\)\s*", "", desc)
    # Clean up punctuation artifacts
    desc = re.sub(r"[,;]\s*[,;]", ",", desc)
    desc = re.sub(r"^\s*[,;.]+\s*", "", desc)
    desc = re.sub(r"\s*[,;]+\s*$", "", desc)
    desc = re.sub(r"\s*,\s*\.", ".", desc)
    # Collapse whitespace
    desc = re.sub(r"\s{2,}", " ", desc).strip()
    # If desc is now too short or empty after cleanup, drop it
    if len(desc) < 10:
        desc = ""
    return title.strip(), desc


# ---------------------------------------------------------------------------
# History pages: compact grouped releases
# ---------------------------------------------------------------------------
def build_history(series_groups: OrderedDict[str, list[dict]], skip_version: str) -> list:
    elements: list = []

    elements.append(Paragraph("Full Release History", SECTION_STYLE))
    elements.append(Paragraph(
        "All production releases grouped by version series. "
        "Each entry lists key changes for traceability.",
        BODY_STYLE,
    ))

    color_idx = 0
    for series_key, releases in series_groups.items():
        # Only include 2026.x series
        if not series_key.startswith("2026"):
            continue

        # Skip the current release (already shown in detail)
        releases_to_show = [r for r in releases if r["version"] != skip_version]
        if not releases_to_show:
            continue

        # Series header bar
        color = SERIES_COLORS[color_idx % len(SERIES_COLORS)]
        color_idx += 1

        date_range = f"{releases_to_show[-1]['date']} to {releases_to_show[0]['date']}"
        total_changes = sum(
            sum(len(items) for items in r["sections"].values())
            for r in releases_to_show
        )

        series_header_style = ParagraphStyle(
            f"SH{color_idx}", fontName=_F_BOLD, fontSize=10,
            textColor=WHITE, leading=13,
        )
        series_meta_style = ParagraphStyle(
            f"SM{color_idx}", fontName=_F_BODY, fontSize=8,
            textColor=WHITE, leading=10,
        )
        header_t = Table(
            [
                [Paragraph(f"Version Series {series_key}", series_header_style)],
                [Paragraph(
                    f"{len(releases_to_show)} release(s)  |  {date_range}  |  "
                    f"{total_changes} total changes",
                    series_meta_style,
                )],
            ],
            colWidths=[CONTENT_WIDTH],
        )
        header_t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), color),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (0, 0), 6),
            ("BOTTOMPADDING", (0, -1), (0, -1), 6),
        ]))
        elements.append(Spacer(1, 3 * mm))
        elements.append(header_t)
        elements.append(Spacer(1, 2 * mm))

        # Detailed bullets for recent series (2026.x), compact for older
        is_recent = series_key.startswith("2026.")

        # Each release in series
        ver_header_style = ParagraphStyle(
            f"VH{color_idx}", fontName=_F_BOLD, fontSize=9,
            textColor=APTEAN_NAVY, leading=12, spaceBefore=3 * mm,
            spaceAfter=1.5 * mm,
        )
        sec_label_style = ParagraphStyle(
            f"SL{color_idx}", fontName=_F_BOLD, fontSize=8,
            textColor=APTEAN_TEAL_DARK, leading=11, leftIndent=4 * mm,
            spaceBefore=1.5 * mm, spaceAfter=1 * mm,
        )
        item_style = ParagraphStyle(
            f"HI{color_idx}", fontName=_F_BODY, fontSize=8,
            textColor=APTEAN_TEXT, leading=11, leftIndent=10 * mm,
            spaceAfter=1 * mm,
        )

        for rel in releases_to_show:
            version_label = f"v{rel['version']}  ({rel['date']})"
            item_count = sum(len(items) for items in rel["sections"].values())

            ver_elements: list = []
            ver_elements.append(Paragraph(
                f"<b>{version_label}</b> - {item_count} change(s)",
                ver_header_style,
            ))

            if is_recent:
                # Full bulleted detail for recent releases
                for section, items in rel["sections"].items():
                    label = _clean_section_name(section)
                    ver_elements.append(Paragraph(label, sec_label_style))

                    for item in items[:6]:
                        title = _escape_xml(_strip_emoji(item["title"]))
                        ver_elements.append(Paragraph(
                            f"- {title}", item_style,
                        ))
                    if len(items) > 6:
                        ver_elements.append(Paragraph(
                            f"<i>+ {len(items) - 6} more</i>", item_style,
                        ))
            else:
                # Compact one-liner for older releases
                section_summary = []
                for section, items in rel["sections"].items():
                    label = _clean_section_name(section)
                    section_summary.append(f"{label} ({len(items)})")
                ver_elements.append(Paragraph(
                    "  ".join(section_summary),
                    ParagraphStyle(
                        f"HC{color_idx}", fontName=_F_BODY, fontSize=7.5,
                        textColor=APTEAN_TEXT_SEC, leading=10, leftIndent=4 * mm,
                        spaceAfter=0.5 * mm,
                    ),
                ))

            elements.append(KeepTogether(ver_elements))

    return elements


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
# Module-level variable set by main() so footer callback can access it
_footer_version: str = ""
_release_date_display: str = ""


LOGO_BLACK = REPO_ROOT / "media" / "aptean-logo-black.png"
LOGO_WHITE = REPO_ROOT / "media" / "aptean-logo-white.png"
_MARGIN = 20 * mm
_TEXT_SEC = HexColor("#4B5563")


def _add_header(canvas, doc):
    """Clean header: title left, page right, thin separator."""
    canvas.setFillColor(_TEXT_SEC)
    canvas.setFont(_F_BODY, 7.5)
    canvas.drawString(_MARGIN, PAGE_HEIGHT - 8 * mm,
                       f"Polaris CLI  |  Release Notes v{_footer_version}")
    canvas.drawRightString(PAGE_WIDTH - _MARGIN, PAGE_HEIGHT - 8 * mm,
                            f"Page {doc.page}")
    canvas.setStrokeColor(BORDER_GRAY)
    canvas.setLineWidth(0.5)
    canvas.line(_MARGIN, PAGE_HEIGHT - 10.5 * mm, PAGE_WIDTH - _MARGIN, PAGE_HEIGHT - 10.5 * mm)


def _add_footer(canvas, doc):
    """Clean footer: thin line, logo left, classification right."""
    canvas.setStrokeColor(BORDER_GRAY)
    canvas.setLineWidth(0.5)
    canvas.line(_MARGIN, 12 * mm, PAGE_WIDTH - _MARGIN, 12 * mm)
    if LOGO_BLACK.exists():
        canvas.drawImage(str(LOGO_BLACK), _MARGIN, 4 * mm,
                         width=18 * mm, height=5.5 * mm,
                         preserveAspectRatio=True, mask="auto")
    canvas.setFillColor(_TEXT_SEC)
    canvas.setFont(_F_BODY, 7)
    canvas.drawRightString(PAGE_WIDTH - _MARGIN, 5.5 * mm,
                            "Company Confidential - Internal Distribution Only")


def _cover_page(canvas, doc):
    """Gradient cover page matching other Polaris documents."""
    canvas.saveState()
    try:
        from PIL import Image as PILImage
        from reportlab.lib.utils import ImageReader
        from io import BytesIO
        w, h = 1200, 800
        img = PILImage.new("RGB", (w, h))
        px = img.load()
        r1, g1, b1 = 0x47, 0x75, 0x99
        r2, g2, b2 = 0x82, 0x76, 0xAE
        r3, g3, b3 = 0xC8, 0x78, 0xBE
        for x in range(w):
            t = x / (w - 1)
            if t < 0.4:
                s = t / 0.4
                r = int(r1 + (r2 - r1) * s)
                g = int(g1 + (g2 - g1) * s)
                b = int(b1 + (b2 - b1) * s)
            else:
                s = (t - 0.4) / 0.6
                r = int(r2 + (r3 - r2) * s)
                g = int(g2 + (g3 - g2) * s)
                b = int(b2 + (b3 - b2) * s)
            for y in range(h):
                px[x, y] = (r, g, b)
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        canvas.drawImage(ImageReader(buf), 0, 0, PAGE_WIDTH, PAGE_HEIGHT,
                         preserveAspectRatio=False)
    except ImportError:
        canvas.setFillColor(APTEAN_NAVY)
        canvas.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)

    from reportlab.lib.colors import Color
    canvas.setFillColor(Color(0, 0, 0, alpha=0.15))
    canvas.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)

    if LOGO_WHITE.exists():
        canvas.drawImage(str(LOGO_WHITE), _MARGIN, PAGE_HEIGHT - 22 * mm,
                         width=30 * mm, height=9 * mm,
                         preserveAspectRatio=True, mask="auto")

    mid_y = PAGE_HEIGHT * 0.52
    canvas.setFillColor(WHITE)
    canvas.setFont(_F_TITLE, 40)
    canvas.drawString(_MARGIN, mid_y + 16 * mm, "Polaris CLI")
    canvas.setFont(_F_TITLE, 24)
    canvas.drawString(_MARGIN, mid_y - 4 * mm, "Release Notes")

    from reportlab.lib.colors import Color as C2
    canvas.setStrokeColor(C2(1, 1, 1, alpha=0.4))
    canvas.setLineWidth(1)
    canvas.line(_MARGIN, mid_y - 14 * mm, _MARGIN + 80 * mm, mid_y - 14 * mm)

    canvas.setFont(_F_BODY, 12)
    canvas.setFillColor(C2(1, 1, 1, alpha=0.85))
    canvas.drawString(_MARGIN, mid_y - 24 * mm, f"Version {_footer_version}")

    canvas.setFont(_F_BODY, 10)
    canvas.setFillColor(C2(1, 1, 1, alpha=0.7))
    canvas.drawString(_MARGIN, 22 * mm, _release_date_display)
    canvas.setFont(_F_BODY, 8)
    canvas.drawRightString(PAGE_WIDTH - _MARGIN, 22 * mm,
                            "Company Confidential - Internal Distribution Only")
    canvas.restoreState()


def add_footer(canvas, doc):
    """Combined header + footer for content pages."""
    canvas.saveState()
    _add_header(canvas, doc)
    _add_footer(canvas, doc)
    canvas.restoreState()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def _find_release(merged: list[dict], target_version: str) -> dict | None:
    """Find a release by version string in the merged list."""
    base_target = _base_version(target_version)
    for rel in merged:
        if rel["version"] == base_target or rel["version"] == target_version:
            return rel
    return None


def main(output_path: Path, target_version: str | None = None) -> None:
    global _footer_version, _release_date_display
    version = target_version or get_version()
    _footer_version = version

    # Parse and process changelog
    raw_releases = parse_changelog()

    # For pre-release versions, show the RC-specific changes on cover
    is_prerelease = _is_rc(version)

    if is_prerelease:
        # Find the specific RC entry in raw releases (before merging)
        current = None
        for rel in raw_releases:
            if rel["version"] == version:
                current = rel
                break
        if not current:
            # Fallback: use merged view
            merged = merge_rc_releases(raw_releases)
            current = merged[0]
        else:
            # Show RC-specific content but note it will fold into parent
            current["rc_note"] = f"Pre-release for v{_base_version(version)}"
        past_releases = [
            r for r in merge_rc_releases(raw_releases)[1:]
            if not r.get("is_rc")
        ]
    else:
        # Full release: fold RCs into parent
        merged = merge_rc_releases(raw_releases)
        current = _find_release(merged, version) or merged[0]
        past_releases = [
            r for r in merged
            if r["version"] != current["version"] and not r.get("is_rc")
        ]

    series_groups = group_by_series(past_releases)

    # Derive display date from release date (e.g., "2026-03-25" -> "March 2026")
    try:
        from datetime import datetime
        dt = datetime.strptime(current["date"], "%Y-%m-%d")
        _release_date_display = dt.strftime("%B %Y")
    except Exception:
        _release_date_display = current.get("date", "")

    # Build PDF
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        topMargin=14 * mm,
        bottomMargin=16 * mm,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        title=f"Aptean Polaris Release Notes v{version}",
        author="Aptean",
    )

    elements: list = []

    # Cover page spacer (visuals drawn by _cover_page canvas handler)
    elements.append(Spacer(1, PAGE_HEIGHT - 40 * mm))
    elements.append(PageBreak())

    # Current release detail (page 2+)
    elements.extend(build_cover(version, current))
    elements.append(PageBreak())
    elements.extend(build_history(series_groups, current["version"]))

    # ---- Closing page ----
    elements.append(PageBreak())

    elements.append(Paragraph("Getting Started", ParagraphStyle(
        "ClosingH1", fontName=_F_TITLE, fontSize=20,
        textColor=APTEAN_NAVY, leading=26, spaceAfter=5 * mm,
    )))
    elements.append(
        HRFlowable(width="100%", thickness=1.5, color=APTEAN_TEAL, spaceAfter=5 * mm)
    )

    closing_body = ParagraphStyle(
        "ClosingBody", fontName=_F_BODY, fontSize=10,
        textColor=APTEAN_TEXT, leading=15, spaceAfter=3 * mm,
    )
    closing_cmd = ParagraphStyle(
        "ClosingCmd", fontName="Courier", fontSize=9,
        textColor=APTEAN_TEXT, backColor=LIGHT_GRAY, borderColor=BORDER_GRAY,
        borderWidth=0.5, borderPadding=4, leading=12,
        spaceBefore=1 * mm, spaceAfter=3 * mm, leftIndent=4 * mm, rightIndent=4 * mm,
    )
    closing_bullet = ParagraphStyle(
        "ClosingBullet", fontName=_F_BODY, fontSize=9.5,
        textColor=APTEAN_TEXT, leading=13, leftIndent=6 * mm, spaceAfter=2 * mm,
    )

    elements.append(Paragraph(
        "To upgrade to this release, download the latest wheel from SharePoint and run:",
        closing_body,
    ))
    elements.append(Paragraph(
        f"pip install --force-reinstall polaris_cli-{version}-py3-none-any.whl<br/>"
        "polaris upgrade",
        closing_cmd,
    ))

    elements.append(Spacer(1, 4 * mm))
    elements.append(Paragraph("Useful Commands", ParagraphStyle(
        "ClosingH2", fontName=_F_HEAD, fontSize=13,
        textColor=APTEAN_TEAL_DARK, spaceAfter=3 * mm,
    )))
    commands = [
        ("/polaris.setup", "Set up a new application or onboard an existing project"),
        ("/polaris.specify", "Describe a feature and run the discovery interview"),
        ("/polaris.autopilot", "Full pipeline - tasks, implement, test, review, merge"),
        ("/polaris.qa", "Generate E2E tests from a work item for QA engineers"),
        ("/polaris.fix", "Fix a bug from Azure DevOps, GitHub Issues, or Jira"),
        ("/polaris.assess", "Codebase assessment - architecture, quality, security"),
        ("/polaris.ship", "Review, accept, and merge a completed feature"),
    ]
    for cmd, desc in commands:
        elements.append(Paragraph(
            f"-  <b>{cmd}</b> - {desc}", closing_bullet,
        ))

    elements.append(Spacer(1, 6 * mm))
    elements.append(Paragraph("Support", ParagraphStyle(
        "ClosingH2b", fontName=_F_HEAD, fontSize=13,
        textColor=APTEAN_TEAL_DARK, spaceAfter=3 * mm,
    )))
    elements.append(Paragraph(
        "Email: <b>polaris@aptean.com</b>", closing_body,
    ))
    elements.append(Paragraph(
        "Teams: <b>Ask Anything</b> channel", closing_body,
    ))

    elements.append(Spacer(1, 10 * mm))
    elements.append(
        HRFlowable(width="60%", thickness=1, color=BORDER_GRAY, spaceAfter=4 * mm)
    )
    elements.append(Paragraph(
        "Aptean Polaris - Plan. Orchestrate. Lead. Align. Realize. Integrate. Ship.",
        ParagraphStyle(
            "Signoff", fontName=_F_ITALIC, fontSize=9,
            textColor=APTEAN_TEXT_SEC, alignment=1, leading=13,
        ),
    ))

    doc.build(elements, onFirstPage=_cover_page, onLaterPages=add_footer)
    print(f"Release notes PDF generated: {output_path.resolve()}")
    print(f"  Version: v{version} ({'pre-release' if is_prerelease else 'full release'})")
    print(f"  Current release: v{current['version']} ({current['date']})")
    print(f"  Historical releases: {len(past_releases)}")
    print(f"  Version series: {len(series_groups)}")


if __name__ == "__main__":
    args = parse_args()
    version = args.version or get_version()
    output = args.output or Path(f"polaris-release-notes-v{version}.pdf")
    main(output, target_version=version)
