---
description: Create an isolated workspace (worktree) for implementing a specific work package.
---

# /polaris.implement - Create Workspace for Work Package

## Model Guidance

Use **claude-sonnet-4-6** for this session. Implementation is high-volume execution against a defined plan - this is where savings compound.

If unexpected complexity surfaces (spec contradiction, constraint not in the plan): stop and surface it as:
```
REPLAN NEEDED: [what was unexpected]
SPEC REFERENCE: [which spec section]
OPTIONS: [2-3 resolution options with tradeoffs]
```
Re-enter planning (Opus) before continuing. Never reason through ambiguity at Sonnet level.

## Tool Preferences

1. `Read` / `Grep` / `Glob` - local files (always prefer)
2. `WebFetch` - public URLs, text only
3. Headless browser - dynamic/auth-gated pages (~82% fewer tokens than screenshot tools)
4. Screenshot browser - last resort only; ~10x more tokens than WebFetch, deprioritised in all skills
5. PDFs - extract as text (not images); ~90% token reduction vs. image path. Applies to all implementation skills automatically.

## Output Style

- After writing a file: `Written: <path>` - nothing else
- After a command: one line with result
- NO preamble, NO narration, NO code explanation
- Do NOT use extended thinking for code, tests, or commits

---

## Working Directory

**Telemetry**: Run: `polaris telemetry record implement --feature <slug> --phase start --agent {{AGENT_NAME}} --wp <WP_ID>`

Run `polaris implement WP##`, then `cd` into the printed worktree path (`.worktrees/###-feature-WP##/`). Do all file operations there.

---

## Decision Memory and Failure Awareness (only if memory files exist)

Skip if neither `.polaris/memory/decisions-summary.md` nor `.polaris/memory/failures-summary.md` exists.

- **decisions-summary.md**: consult before architectural choices; follow prior decisions; record new ones via `polaris memory record-decision`
- **failures-summary.md**: apply recorded fixes for matching errors; resolve new ones via `polaris memory resolve-failure`

---

## Pre-Implementation Context

If NOT WP01 and `control-map.md` exists: read it and relevant shared dependency files for consistency.

---

## Two-step command

```bash
# 1. Get the WP prompt
polaris agent workflow implement WP## --agent __AGENT__

# 2. Create workspace and implement
polaris implement WP##              # No dependencies
polaris implement WP## --base WPXX  # With dependencies
```

## Completion Requirements

Work is NOT complete until:
1. All subtasks in WP prompt finished
2. Changes committed to the WP workspace
3. **Run feature-scoped regression**: `polaris runtests --feature <slug>`

**Default flow**: implement -> `polaris runtests` -> auto-moves to `for_review` on pass

**Fallback** (only for `test_status: "skipped"` WPs):
```bash
polaris agent tasks move-task WP## --to for_review --note "No tests: docs/infra WP"
```

## Lane Status

`planned` -> `doing` -> `testing` -> `for_review` -> `done`

Testing transitions (via `polaris runtests`):
- `doing` -> `testing` -> `for_review` (pass)
- `doing` -> `testing` -> `doing` (fail, with details)

## Complete Workflow

```bash
# 1. Get WP prompt
polaris agent workflow implement WP## --agent __AGENT__

# 2. Create workspace
polaris implement WP##  # or --base WPXX if dependencies

# 3. cd into worktree and implement

# 4. Regression tests (REQUIRED)
polaris runtests --feature <slug>

# 5. Self-review: verify all acceptance criteria met, no unintended changes, no hardcoded values

# 6. Move to for_review (runtests handles this automatically on pass)
```

## Troubleshooting

- **"Base workspace WP01 does not exist"**: run `polaris implement WP01` first
- **"WP02 has dependencies"**: add `--base WP01`
- **Status shows 'doing' after for_review**: reviewer may have moved it back, or sync delay - check the WP file


**Telemetry**: Run: `polaris telemetry record implement --feature <slug> --phase complete --agent {{AGENT_NAME}} --wp <WP_ID>`
