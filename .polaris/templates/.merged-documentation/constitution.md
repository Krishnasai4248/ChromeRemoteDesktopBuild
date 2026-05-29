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

**Telemetry**: Run: `polaris telemetry record constitution --feature <slug> --phase start --agent {{AGENT_NAME}}`


```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## What This Command Does

Creates or updates `.polaris/memory/constitution.md` through interactive 4-phase discovery.

**Constitution is OPTIONAL.** All polaris commands work without it. It captures: technical standards, code quality expectations, tribal knowledge, and governance rules.

## Discovery Phases

| Phase | Content | Questions | Required? |
|-------|---------|-----------|-----------|
| 1. Technical Standards | Languages, testing, performance, deployment | 3-4 | Recommended |
| 2. Code Quality | PR rules, review checklist, quality gates, docs | 3-4 | Optional |
| 3. Tribal Knowledge | Conventions, lessons learned, historical decisions | 2-4 | Optional |
| 4. Governance | Amendment process, compliance, exceptions | 2-3 | Optional |

**Paths**: Minimal (~1 page, Phase 1 only, 3-5 questions) or Comprehensive (~2-3 pages, all phases, 8-12 questions).

## Steps

### 1. Initial Choice

Ask: A) Skip (create placeholder), B) Minimal (Phase 1 only), C) Comprehensive (all phases)

If skipped: write placeholder to `.polaris/memory/constitution.md` and exit.

### 2. Phase 1 - Technical Standards

Ask one at a time with examples:
- **Q1 Languages/Frameworks**: e.g., "Python 3.11+ with FastAPI", "TypeScript 4.9+ with React 18"
- **Q2 Testing**: e.g., "pytest with 80% coverage", "Jest with 90% coverage"
- **Q3 Performance/Scale**: e.g., "1000 req/s at p95 < 200ms", "N/A"
- **Q4 Deployment**: e.g., "Docker on K8s", "Cross-platform: Linux/macOS/Windows"

### 3. Phase 2 - Code Quality (comprehensive only)

Ask to skip or continue. If yes:
- **PR Requirements**: approval count, CI checks
- **Review Checklist**: what reviewers should check
- **Quality Gates**: what must pass before merge
- **Documentation Standards**: docstrings, README, ADRs

### 4. Phase 3 - Tribal Knowledge (comprehensive only)

Ask to skip or continue. If yes:
- **Team Conventions**: coding styles, patterns to follow
- **Lessons Learned**: past mistakes to avoid
- **Historical Decisions** (optional): architectural choices and rationale

### 5. Phase 4 - Governance (comprehensive only)

Ask to skip or continue. If skipped, use defaults: PR-based amendments, reviewer compliance, case-by-case exceptions.

If yes: amendment process, compliance validation, exception handling (optional).

### 6. Summary and Confirmation

Present summary of all phases/answers. Ask: A) Write it, B) Start over, C) Cancel.

### 7. Write Constitution File

Generate markdown to `.polaris/memory/constitution.md` with sections for each completed phase. Include:
- Header with project name, date, version
- Technical Standards (Q1-Q4)
- Code Quality (if Phase 2)
- Tribal Knowledge (if Phase 3)
- Governance (Phase 4 or defaults)
- **Model Selection section (always included)**
- License Compliance section (always included):
  - Allowed: Apache-2.0, BSD-2/3-Clause, MIT, ISC, PSF-2.0, Unlicense, 0BSD, CC0-1.0
  - Prohibited: LGPL, AGPL, GPL, SSPL, BSL, CPAL, EUPL, MPL-2.0

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

### 8. Success Message

Report: file location, phases completed, next steps (review, share, run /polaris.specify).

## Behaviors

- Ask one question at a time with skip options
- Keep constitution lean (1-3 pages)
- If skipped entirely, still create placeholder file


**Telemetry**: Run: `polaris telemetry record constitution --feature <slug> --phase complete --agent {{AGENT_NAME}}`
