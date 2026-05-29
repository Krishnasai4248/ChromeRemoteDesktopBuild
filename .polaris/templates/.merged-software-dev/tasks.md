---
description: Generate grouped work packages with actionable subtasks and matching prompt files for the feature in one pass.
---

## Model Guidance

This command does planning work. Use **claude-opus-4-6** for this session.

Work package decomposition made here defines the implementation structure for the entire feature. Errors in WP scope, dependencies, or sizing compound in every downstream implementation session. If you are on Sonnet: switch to Opus (`/model claude-opus-4-6`).

---

## User Input

**Telemetry**: Run: `polaris telemetry record tasks --feature <slug> --phase start --agent {{AGENT_NAME}}`


```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Working Directory

Run from planning repository root. NO worktrees created. Output goes to `polaris-specs/###-feature/tasks/`.

Verify you're on the target branch:
```bash
git branch --show-current
```

## WP Sizing Rules (CRITICAL)

| Metric | Target | Max | Action if exceeded |
|--------|--------|-----|--------------------|
| Subtasks/WP | 3-7 | 10 | SPLIT the WP |
| Prompt lines/WP | 200-500 | 700 | SPLIT the WP |

- Let complexity dictate WP count (20+ WPs is fine)
- Each WP: independently implementable, single focused goal

## Steps

### 1. Setup

```bash
polaris agent feature check-prerequisites --json --paths-only --include-tasks
```

Capture `FEATURE_DIR` (ABSOLUTE path). Use it for ALL file operations.

### 2. Load Design Documents

From `FEATURE_DIR`: spec.md and plan.md (required), data-model.md, contracts/, research.md (optional).

### 3. Derive Subtasks

Create complete list (T001, T002, ...). Include implementation steps, tests, migrations, operational work. Mark parallel-safe items `[P]`.

### 4. Group into Work Packages

Group into WPs following sizing rules. Sequence: setup -> foundational -> story phases -> polish. Every subtask in exactly one WP.

### 5. Write tasks.md

Write to `FEATURE_DIR/tasks.md` with WP sections: summary, subtask checklist, implementation sketch, parallel opportunities, dependencies.

### 6. Generate WP Prompt Files

Create `FEATURE_DIR/tasks/WPxx-slug.md` for each WP (FLAT directory - NO subdirectories under `tasks/`).

Frontmatter: `work_package_id`, `subtasks`, `lane: "planned"`, `dependencies`. Include objective, detailed per-subtask guidance, test strategy, DoD, risks.

Lane status is in `lane:` frontmatter only - never in directory structure.

**Validate each prompt**: if >700 lines, go back and split.

### 7. Finalize

```bash
polaris agent feature finalize-tasks --json
```

Parses dependencies, updates frontmatter, validates (no cycles), COMMITS automatically. **DO NOT run git commit after this.**

### 8. Report

WP count, subtask tallies, size distribution, parallelization opportunities, MVP scope, next command.

## Dependencies (0.11.0+)

```yaml
dependencies: ["WP01"]
```

Include correct command in each WP prompt:
- No deps: `polaris implement WP01`
- With deps: `polaris implement WP02 --base WP01`

## Task Rules

- E2E tests required for every feature. Only pure docs/infra WPs may skip (`test_status: "skipped"`).
- Subtask granularity: one clear action
- Prompt detail: purpose, steps, files to create/modify, validation checklist, edge cases

## Domain Assignment

Assign `domain` frontmatter to every WP:

| Domain | When to use |
|--------|-------------|
| `database` | Migrations, schema, queries |
| `api-design` | REST/GraphQL endpoints, auth |
| `frontend-craft` | UI, CSS, accessibility |
| `backend-logic` | Business logic, services (default if mixed) |
| `testing-specialist` | Test strategy, fixtures |
| `devops-infra` | CI/CD, Docker, Helm |
| `documentation` | Docs, changelogs |

## Subagent Eligibility

After grouping, evaluate each WP for parallel subagent eligibility. Load `@references/tasks-subagent-eligibility.md` for full criteria and safety rules.

Context: {ARGS}

The combination of tasks.md and prompt files must enable any engineer to deliver a WP end-to-end.


**Telemetry**: Run: `polaris telemetry record tasks --feature <slug> --phase complete --agent {{AGENT_NAME}}`
