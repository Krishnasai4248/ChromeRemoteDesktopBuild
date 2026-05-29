---
description: Audit project compliance against organization best practices and standards.
---

## User Input

**Telemetry**: Run: `polaris telemetry record standards --feature <slug> --phase start --agent {{AGENT_NAME}}`


```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Audit the project against organization standards (folder structure, versioning, branching, health endpoints, CI/CD, containerization, docs, security). Generate compliance report with scores, findings, and remediation.

## Steps

### 1. Run Compliance Audit

Check each area and record pass/fail/warn:

**Folder Structure**: Has `src/`, `tests/`, `docs/`, CI/CD directory. Clean separation of concerns.

**Versioning**: VERSION file with CalVer (YYYY.MM.PATCH), CHANGELOG.md, version consistency across files/tags.

**Branching**: Protected main/master, feature branch naming convention, no stale branches >30 days.

**Health Endpoints**: `/health`, `/liveness`, `/readiness` endpoints. Health checks cover DB and cache dependencies.

**CI/CD**: Lint+test+build workflow, release/deploy workflow, runs on PR and merge, tests gate merges.

**Containerization**: Dockerfile with multi-stage build, non-root user, HEALTHCHECK instruction, .dockerignore.

**Documentation**: README.md with setup, API docs (if applicable), architecture docs, meaningful code comments.

**Security**: No secrets in source (.env gitignored), pinned dependencies (lock file), vulnerability scanning configured, no known vulnerable deps.

**DAST**: Detect tooling via `detect_dast_tools()` from `specify_cli.assess.tooling_detection`. Supported: OWASP ZAP (.zap/, zap.yaml), Nuclei (nuclei-templates/, .nuclei-config.yaml), Burp Suite (.burp/, burp-project.json). When not detected, include setup guidance (install, config, run, docs).

### 2. Generate Report

Display category-by-category scores (pass/fail/warn per area), overall percentage, and findings sorted by severity (HIGH/MEDIUM/LOW) with specific remediation steps.

### 3. Offer Auto-Fix

For straightforward fixes (VERSION file, CHANGELOG template, .dockerignore), offer to create. Never modify existing files without showing diff first.

### 4. Save Report

Save to `compliance-report.md` in project root.

## Regulatory Compliance (--compliance flag)

Supported: `soc2`, `iso27001`, `hipaa`, `pci-dss`. Unsupported values get an error message.

**C1. Ensure assess results**: Check `.polaris/cache/assess-results.json`. If missing or >24h old, auto-run `/polaris.assess`.

**C2. Load controls**: `python -c "from specify_cli.compliance import get_framework_controls; controls = get_framework_controls('<framework>')"`.

**C3. Map findings to controls**: PASS (no findings), PARTIAL (medium/low only), FAIL (critical/high), EXTERNAL (requires infra/org tooling Polaris cannot evidence).

**C4. Render compliance matrix**: Control-by-control table with status, grouped by category. Include finding details for FAIL/PARTIAL.

**C5. SoD evidence**: If `.polaris/audit-trail/` exists, include per-WP implementer/reviewer/accepter, timestamps, overrides, overall SoD status.

**C6. Summary**: Controls assessed, PASS/PARTIAL/FAIL/EXTERNAL counts with percentages.

## Evidence Packaging (--evidence-package flag)

Bundle artifacts into dated directory via `create_evidence_package()` from `specify_cli.compliance.evidence`. Includes: assess results, audit trail, compliance matrix, evidence log, test results, SHA-256 manifest, metadata.json.

## GRC Export (--export flag)

Requires `--compliance`. Formats: `json` or `csv`. Uses `export_json()`/`export_csv()` from `specify_cli.compliance.export`. Report output path and control counts.

## Principles

Audit first then fix. Severity-driven (HIGH first). Non-destructive. Every failure has remediation. Smart caching (<24h). EXTERNAL controls clearly marked. Evidence bundled with checksums.

Context: {ARGS}


**Telemetry**: Run: `polaris telemetry record standards --feature <slug> --phase complete --agent {{AGENT_NAME}}`
