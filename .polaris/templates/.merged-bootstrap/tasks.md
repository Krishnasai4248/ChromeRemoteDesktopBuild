---
description: Generate grouped work packages with actionable subtasks and matching prompt files for the feature in one pass.
---

## Model Guidance

This command does planning work. Use **claude-opus-4-6** for this session.

WP decomposition here defines the implementation structure for the entire feature. If you are on Sonnet: switch to Opus (`/model claude-opus-4-6`).

---

## User Input

**Telemetry**: Run: `polaris telemetry record tasks --feature <slug> --phase start --agent {{AGENT_NAME}}`


```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Working Directory

Run from planning repository root. NO worktrees created. Output goes to `polaris-specs/###-feature/tasks/`.

If `pwd` contains `.worktrees/`: STOP. Navigate back to repo root.

```bash
git branch --show-current
```

## WP Sizing Rules (CRITICAL)

| Metric | Target | Max | Action if exceeded |
|--------|--------|-----|-------------------|
| Subtasks/WP | 3-7 | 10 | SPLIT the WP |
| Prompt lines/WP | 200-500 | 700 | SPLIT the WP |

## Steps

### 1. Setup

```bash
polaris agent feature check-prerequisites --json --paths-only --include-tasks
```

Capture `FEATURE_DIR` (ABSOLUTE path).

### 2. Load Design Documents

From `FEATURE_DIR`: spec.md and plan.md (required), data-model.md, contracts/, research.md (optional).

### 3. Derive Subtasks

Create list (T001, T002, ...). Include implementation, tests, migrations. Mark parallel-safe `[P]`.

### 4. Group into Work Packages

Follow sizing rules. Sequence: setup -> foundational -> story phases -> polish. Every subtask in exactly one WP.

### 5. Write tasks.md

Write `FEATURE_DIR/tasks.md` with: summary, subtask checklist, implementation sketch, parallel opportunities, dependencies per WP.

### 6. Generate WP Prompt Files

Create `FEATURE_DIR/tasks/WPxx-slug.md` for each WP (FLAT). Frontmatter: `work_package_id`, `subtasks`, `lane: "planned"`, `dependencies`. Lane in frontmatter only.

**Validate each prompt**: if >700 lines, split.

### 7. Finalize

```bash
polaris agent feature finalize-tasks --json
```

COMMITS automatically. **DO NOT run git commit after this.**

### 8. Report

WP count, subtask tallies, size distribution, parallelization opportunities, next command.

## Dependencies (0.11.0+)

```yaml
dependencies: ["WP01"]
```

- No deps: `polaris implement WP01`
- With deps: `polaris implement WP02 --base WP01`

## Task Rules

- E2E tests required. Only pure docs/infra WPs may skip (`test_status: "skipped"`).
- One clear action per subtask. Include purpose, steps, files, validation, edge cases.

Context: {ARGS}


**Telemetry**: Run: `polaris telemetry record tasks --feature <slug> --phase complete --agent {{AGENT_NAME}}`
