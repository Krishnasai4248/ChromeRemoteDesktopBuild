---
description: Generate a standardized, branded report (HTML or PPTX) using the Polaris design system. Use for any analysis, audit, assessment, or investigation output.
---

## User Input

**Telemetry**: Run: `polaris telemetry record report --feature <slug> --phase start --agent {{AGENT_NAME}}`


```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Generate a professional, enterprise-branded report using the **Polaris report design system** defined below. Reports can be produced in **HTML** (default) or **PPTX** (PowerPoint) format. This template ensures visual consistency across ALL reports produced by any agent, skill, or workflow. The output is saved to `.polaris/reports/`.

**This is the canonical reference for report generation.** Any agent or skill that produces a report MUST use this design system. Do NOT invent custom colors, fonts, or component styles.

## Report Naming Convention

Save to: `.polaris/reports/{project-slug}-{report-slug}-{YYYY-MM-DD}.{ext}`

- `{project-slug}`: kebab-case project identifier (e.g., `m2m`, `acme-api`, `platform`)
- `{report-slug}`: kebab-case report type (e.g., `codebase-assessment`, `security-audit`, `nfr-readiness`, `bug-root-cause-analysis`, `repo-cleanup`, `migration-readiness`, `dependency-audit`)
- `{YYYY-MM-DD}`: date of generation
- `{ext}`: `html` or `pptx` depending on the chosen format
- Examples:
  - `.polaris/reports/m2m-security-audit-2026-02-19.html`
  - `.polaris/reports/acme-api-codebase-assessment-2026-03-01.pptx`

---

## Document Classification

Before generating, ask the user:

> What is the distribution intent for this document?
> 1. **Internal Only** - Shared within Aptean teams (default)
> 2. **Do Not Distribute** - Restricted, not to be shared beyond named recipients
> 3. **Customer Facing** - Will be shared with external customers or partners

Use the selected classification in the confidential banner and footer:

| Intent | Banner Text | Footer Text |
|--------|------------|-------------|
| Internal Only | `COMPANY CONFIDENTIAL - INTERNAL DISTRIBUTION ONLY` | `Company Confidential - Internal Distribution Only` |
| Do Not Distribute | `COMPANY CONFIDENTIAL - DO NOT DISTRIBUTE` | `Company Confidential - Do Not Distribute` |
| Customer Facing | *(no banner)* | `Aptean Confidential` |

If the user does not respond or skips, default to **Internal Only**.

## Format Selection

Determine the output format from the user's input:

| User input contains... | Format |
|------------------------|--------|
| `pptx`, `powerpoint`, `slides`, `deck`, `presentation` | **PPTX** |
| Anything else (or nothing specified) | **HTML** (default) |

- If **HTML**: Load @references/report-html-design-system.md for the HTML skeleton, component catalog, CSS stylesheet, content guidelines, and HTML execution steps.
- If **PPTX**: Load @references/report-pptx-design-system.md for the PPTX color palette, typography, slide dimensions, helper functions, slide type patterns, report-to-slide mapping, and PPTX execution steps.

Both formats share the same **Report Naming Convention**, **Report Type** determination (Step 1), **Data Gathering** (Step 2), **Content Guidelines**, and **Operating Principles**.

---

## Operating Principles

- **Design system is law**: Use only the design system from the reference files. Do NOT invent custom colors, fonts, or layouts.
- **Evidence-based**: Every finding cites specific files and lines.
- **Actionable**: Every finding includes a recommendation with effort estimate.
- **Self-contained**: The generated HTML/PPTX must be complete and standalone.
- **Non-destructive**: Output only to `.polaris/reports/`. Never modify source files.
- **Cross-platform**: Python-generated PPTX script must run on Windows, macOS, and Linux.

## Context

$ARGUMENTS


**Telemetry**: Run: `polaris telemetry record report --feature <slug> --phase complete --agent {{AGENT_NAME}}`
