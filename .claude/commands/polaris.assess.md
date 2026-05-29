---
description: Perform a thorough codebase assessment covering architecture, code quality, security, tech debt, tests, and dependencies. Scales from small projects to 500K+ file monorepos.
---


## User Input

**Telemetry**: Run: `polaris telemetry record assess --feature <slug> --phase start --agent claude`


```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Conduct a systematic, comprehensive assessment of the codebase at any scale. Use automated tooling to gather quantitative metrics first, then deep-dive into flagged hotspots. The output is a structured, severity-rated analysis saved to `.polaris/reports/`.

**This assessment MUST work on repos of any size** - from 10 files to 500,000+ files. Never attempt to read every file. Gather metrics programmatically, then sample strategically.

## Execution Steps

### 0. Context Discovery (MUST run before assessment)

Before starting any analysis, gather existing project knowledge to produce a **contextualized** assessment rather than a generic one.

**a) Check for constitution file:**

Look for `.polaris/memory/constitution.md`. If it exists, read it. Extract:
- Project purpose and domain
- Architecture decisions and constraints
- Tech stack choices and rationale
- Known limitations or technical debt decisions
- Team conventions and standards
- Integration points (databases, APIs, external services)

If the constitution does NOT exist, tell the user:

> "No project constitution found at `.polaris/memory/constitution.md`. A constitution captures tribal knowledge (architecture decisions, tech stack rationale, known constraints) that makes this assessment far more accurate.
>
> Would you like to:
> 1. **Run `/polaris.constitution` first** (recommended - 5 min interactive setup)
> 2. **Provide a brief context now** - Tell me about this codebase: what it does, key technologies, known pain points
> 3. **Proceed without context** - I will do a generic industry-based assessment
>
> Option 1 or 2 will significantly improve the assessment quality."

Wait for the user's response. If they choose option 2, record their input and use it throughout the assessment. If option 3, proceed but note in the report that no project context was available.

**b) Check for agent context file:**

Check for the active agent's context file (e.g., `CLAUDE.md`, `GEMINI.md`, `AGENTS.md`). If it exists, read the `## Active Technologies` and `## Recent Changes` sections to understand what tech is in use and what changed recently.

**c) Check for existing memory files:**

If `.polaris/memory/` exists, scan for any `.md` files (besides constitution). These may contain project-specific knowledge from previous sessions.

**Use all discovered context** to tailor the assessment: weight dimensions based on the project's actual tech stack, apply the team's own standards as a benchmark, and flag findings that contradict stated architecture decisions.

### 1. Purpose Interview

Ask the user:

> What is the primary purpose of this assessment?
> - **Upgrade readiness** - Evaluating before a major framework/language upgrade
> - **Modernization** - Identifying areas to modernize legacy code
> - **Security audit** - Focus on OWASP Top 10 and security best practices
> - **Tech debt inventory** - Cataloguing all technical debt for prioritization
> - **New team onboarding** - Creating a codebase overview for new developers
> - **General health check** - Broad assessment across all dimensions

Wait for the answer. This determines emphasis weighting.

### 2. Repo Census

Use your built-in search and file tools to gather these metrics. If shell commands are needed, use **git commands** (cross-platform) or **Python one-liners** (guaranteed available since Polaris is Python). Never use `find`, `sed`, `awk`, or other Unix-only commands.

**IMPORTANT: Run each sub-section (a, b, c, d) one at a time, not in parallel.** Some commands return non-zero exit codes when no matches are found, which is normal. Running them as parallel sibling tool calls risks cascading cancellation if any one fails.

Load @references/assess-metric-scripts.md for all metric collection scripts (scale/structure, LOC, dependency manifests, config files, tech debt markers, security scans, largest files, CI/CD detection). Run each sub-section ONE AT A TIME sequentially.

Record the total file count - this determines scan depth:
- **Small** (<1,000 files): Read most files directly
- **Medium** (1,000-50,000): Grep patterns + 5-10% sampling
- **Large** (50,000+): Grep patterns only + 1-2% sampling

### 4. Deep Dive Sampling

Based on automated metrics, **read the top hotspot files**:

1. **Architecture**: Main entry points, largest modules, dependency manifests
2. **Security**: Every file flagged by security grep patterns
3. **Complexity**: Top 5 largest source files
4. **Tech debt**: Top 5 files with most TODO/FIXME markers
5. **Tests**: 2-3 test files to assess quality and patterns

For each sampled file, note specific line numbers and extrapolate patterns.

### 5. Severity Assignment

- **CRITICAL**: Security vulnerability, data loss risk, production-breaking
- **HIGH**: Significant tech debt, missing tests for critical paths, architectural concern
- **MEDIUM**: Code quality issue, moderate tech debt, missing documentation
- **LOW**: Style inconsistency, minor improvement

### 6. Produce Assessment Report

Save to `.polaris/reports/assessment-YYYY-MM-DD.md`:

```markdown
# Codebase Assessment Report

**Date**: YYYY-MM-DD | **Repo**: <name> | **Purpose**: <from interview> | **Context**: <constitution/user-provided/none>

## Executive Summary

| Metric | Value |
|--------|-------|
| Health score | A/B/C/D/F |
| Total files | <count> |
| Lines of code | <count> |
| Languages | <list> |
| Critical findings | <count> |
| Total findings | <count> |

## Scale Profile

| Metric | Value |
|--------|-------|
| Source files | <count> |
| Test files | <count> |
| Test ratio | <ratio> |
| Dependencies | <count> |
| Tech debt markers | <count> |

## Findings by Dimension

### Architecture (<score>/10)
| # | Severity | Finding | Location | Recommendation |
|---|----------|---------|----------|----------------|

### Code Quality (<score>/10)
### Security (<score>/10)
### Technical Debt (<score>/10)
### Test Coverage (<score>/10)
### Dependencies (<score>/10)
### CI/CD (<score>/10)

## Top 10 Priority Actions
| # | Severity | Action | Impact | Effort |
|---|----------|--------|--------|--------|

## Methodology
- Scan strategy: <small/medium/large>
- Files sampled: <count>
- Patterns matched: <count>
```

### 7. Report Output

The CLI saves a **markdown report by default** to `.polaris/reports/assessment.md`. Users can also request HTML via `--format html`, or skip the file with `--no-report`. After writing the detailed report above, inform the user:

- Default: `polaris assess` (saves `.polaris/reports/assessment.md`)
- HTML: `polaris assess --format html` (saves `.polaris/reports/assessment.html`)
- Custom path: `polaris assess --output ./my-report.md`
- Skip file: `polaris assess --no-report`

## Operating Principles

- **Tool-first**: Gather metrics via git commands or agent search tools before reading files. Never read more than 50 files manually.
- **Cross-platform**: Use `git grep`, `git ls-files`, and Python - never Unix-only tools like `find`, `sed`, or `awk`.
- **Scale-aware**: A 500K-file repo gets the same quality as a 50-file repo with smarter sampling.
- **Evidence-based**: Every finding cites specific files and lines.
- **Actionable**: Every finding includes a recommendation with effort estimate.
- **Non-destructive**: Read-only analysis - never modify files.

## Context

$ARGUMENTS


**Telemetry**: Run: `polaris telemetry record assess --feature <slug> --phase complete --agent claude`
