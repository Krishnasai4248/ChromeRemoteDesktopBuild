---
description: Create or update the project constitution through interactive phase-based discovery.
---


## Model Guidance

This command does planning work. Use **claude-opus-4-6** for this session.

Constitution discovery requires synthesis of team standards, architectural decisions, and governance rules. Opus-level reasoning here ensures the output is accurate and durable.

If you are currently on Sonnet: switch to Opus before proceeding (`/model claude-opus-4-6`).

Note: `--regenerate` bypasses discovery entirely and runs a Python command directly - no model reasoning required.

---

## User Input

**Telemetry**: Run: `polaris telemetry record constitution --feature <slug> --phase start --agent claude`


```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

**If `$ARGUMENTS` contains `--regenerate`:** run the single Bash command below, print its output, and stop. Do not read further. Do not ask any questions.

```bash
python -c "from specify_cli.core.constitution_regenerate import regenerate; from pathlib import Path; print(regenerate(Path('.')))"
```

If the command exits with an error, print the error message and stop.

---

## What This Command Does

Creates or updates `.polaris/memory/constitution.md` through interactive 5-phase discovery.

**Constitution is OPTIONAL.** All polaris commands work without it. It captures: technical standards, security baseline, code quality expectations, tribal knowledge, and governance rules.

## Discovery Phases

| Phase | Content | Questions | Required? |
|-------|---------|-----------|-----------|
| 1. Technical Standards | Languages, testing, performance, deployment | 4-5 | Recommended |
| 2. Security & Audit Baseline | Data classification, audit logging, AuthN/AuthZ, threat surface | 4 | **Required** |
| 3. Code Quality | PR rules, review checklist, quality gates, docs | 3-4 | Optional |
| 4. Tribal Knowledge | Conventions, lessons learned, historical decisions | 2-4 | Optional |
| 5. Governance | Amendment process, compliance, exceptions | 2-3 | Optional |

**Paths**: Minimal (~1.5 pages, Phases 1 + 2, 7-9 questions) or Comprehensive (~2-3 pages, all phases, 12-16 questions). Phase 2 is **required** in both paths - shipping an app with no documented audit-log policy or threat surface is not a supported configuration. If the answers are genuinely "none" (e.g. internal CLI with no PII), record that explicitly in the constitution rather than skipping the phase.

## Steps

### 1. Initial Choice

Ask: A) Skip (create placeholder), B) Minimal (Phase 1 only), C) Comprehensive (all phases)

If skipped: write placeholder to `.polaris/memory/constitution.md` and exit.

### 2. Phase 1 - Technical Standards

Ask one at a time with examples. When recommending a runtime/framework version, default to the floor in `src/specify_cli/scaffolds/version_pins.yaml` (Node 22+ LTS, Python 3.12+, Java 21+ LTS, PostgreSQL 17+, Next.js 16+, React 19+, Django 5.1+, .NET 8+ LTS, Rust latest stable).

- **Q1 Languages/Frameworks**: e.g., "Python 3.12+ with FastAPI 0.115+", "TypeScript 5.x on Node 22 LTS with Next.js 16 + React 19"
- **Q2 Testing**: e.g., "pytest with 80% coverage", "Jest with 90% coverage"
- **Q3 Performance/Scale**: e.g., "1000 req/s at p95 < 200ms", "N/A"
- **Q4 Deployment**: e.g., "Docker on K8s", "Cross-platform: Linux/macOS/Windows"
- **Q5 Azure DevOps**: Ask if they use ADO for work items. If yes, collect org URL and project name. Enables `/polaris.fix` ADO integration.

### 3. Phase 2 - Security & Audit Baseline (Required)

This phase is REQUIRED for both Minimal and Comprehensive paths. If an answer is genuinely "none" or "not applicable", record that explicitly so future reviewers can see the conscious decision rather than guess.

- **Q6 Data Classification**: What is the most sensitive data tier the application stores or processes? Use the standard four-tier model: Public, Internal, Confidential, Restricted (PII/PHI/payment/secrets). Pick the highest tier that applies; the constitution records this and downstream specs reference it.
- **Q7 Audit Logging**: Which events MUST be captured to an append-only audit log, and how long are they retained? At minimum: authentication outcomes (success/failure), authorization denials, all writes/deletes against Confidential or Restricted data, configuration changes, and admin actions. Default retention: 1 year. Audit logs land in `audit-trail/` (project root) or a managed sink (Splunk, Sentinel, S3 + Object Lock); never in the same database table as the data they describe.
- **Q8 AuthN / AuthZ Model**: How do callers authenticate (none, API key, OIDC/OAuth2, mTLS, SSO) and how is authorization decided (role-based, attribute-based, ownership-based)? Default-deny is required: if a request does not match a permit rule, it is denied. Record the principal source (JWT, header, session) and the policy enforcement point.
- **Q9 Threat Surface**: Where does untrusted input enter the system? List every boundary: public HTTP, webhook, file upload, message queue, scheduled job consuming external data, third-party API. For each, note PII/PHI/payment exposure and whether the app is multi-tenant. The answer becomes the seed of the threat model under `security/threat-model.md`.

### 4. Phase 3 - Code Quality (comprehensive only)

Ask to skip or continue. If yes:
- **PR Requirements**: approval count, CI checks
- **Review Checklist**: what reviewers should check
- **Quality Gates**: what must pass before merge
- **Documentation Standards**: docstrings, README, ADRs

### 5. Phase 4 - Tribal Knowledge (comprehensive only)

Ask to skip or continue. If yes:
- **Team Conventions**: coding styles, patterns to follow
- **Lessons Learned**: past mistakes to avoid
- **Historical Decisions** (optional): architectural choices and rationale

### 6. Phase 5 - Governance (comprehensive only)

Ask to skip or continue. If skipped, use defaults: PR-based amendments, reviewer compliance, case-by-case exceptions.

If yes: amendment process, compliance validation, exception handling (optional).

### 7. Summary and Confirmation

Present summary of all phases/answers. Ask: A) Write it, B) Start over, C) Cancel.

### 8. Write Constitution File


Generate markdown to `.polaris/memory/constitution.md` with sections for each completed phase. Include:
- Header with project name, date, version
- Technical Standards (Q1-Q4)
- Azure DevOps section (if Q5 answered yes)
- **Security & Audit Baseline (Q6-Q9, always included)** - data classification tier, audit log policy and retention, AuthN/AuthZ model, threat surface
- Code Quality (if Phase 3)
- Tribal Knowledge (if Phase 4)
- Governance (Phase 5 or defaults)
- **Model Selection section (always included)**
- License Compliance section (always included):
  - Allowed: Apache-2.0, BSD-2/3-Clause, MIT, ISC, PSF-2.0, Unlicense, 0BSD, CC0-1.0
  - Prohibited: LGPL, AGPL, GPL, SSPL, BSL, CPAL, EUPL, MPL-2.0
- Deployment Compliance & Topology section: do NOT generate this manually.
  This section is auto-managed by `polaris ship`. The first time a developer
  runs `polaris ship` (or `/polaris.ship`), they are asked whether the app
  needs ITAR or GDPR compliance, and the answer is written into both
  `.polaris/metadata.yaml` (under a `deployment:` block) and this constitution
  file (as a "## Deployment Compliance & Topology" section). Subsequent ships
  read the stored value and do not re-prompt. To change it later, run
  `/polaris.constitution --amend` and update the deployment section in place,
  then sync `.polaris/metadata.yaml` to match (or use the helper
  `specify_cli.core.deployment_decisions.write_decisions(...)` which updates
  both files together).

The Model Selection section must appear verbatim in every generated constitution:

```markdown
## Model Selection

Claude Code operates in two phases within any Polaris workflow. Use the right model for each.

### Plan Phase -> Opus

When reading specs, synthesizing the architecture, deciding what to build and how it connects:
use claude-opus-4-6. Planning mistakes compound through every line of code that follows.
Opus-level reasoning here is insurance, not indulgence.

Polaris planning commands: /polaris.specify, /polaris.plan, /polaris.tasks

### Implementation Phase -> Sonnet

When writing code, calling tools, executing against a defined plan:
use claude-sonnet-4-6. Implementation is where call volume lives - this is where savings compound.

Polaris implementation commands: /polaris.implement, /polaris.autopilot, /polaris.runtests

### When Implementation Hits Unexpected Complexity

Do not reason through ambiguity or contradiction at Sonnet level. Stop the step, describe what
is unexpected, and surface it:

REPLAN NEEDED: [one sentence - what was unexpected]
SPEC REFERENCE: [which spec/section the assumption came from]
OPTIONS: [2-3 ways to resolve, with tradeoffs]

Re-enter the plan phase (Opus) with the updated context before continuing.
Never self-escalate the model mid-implementation.
```

### 9. Success Message

Report: file location, phases completed, next steps (review, share, run /polaris.specify).

## Behaviors

- Ask one question at a time with skip options
- Keep constitution lean (1-3 pages)
- If skipped entirely, still create placeholder file


**Telemetry**: Run: `polaris telemetry record constitution --feature <slug> --phase complete --agent claude`
