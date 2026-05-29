---
description: Create an isolated workspace (worktree) for implementing a specific work package.
---

## Advanced Command Gate

Load `.claude/commands/references/advanced-gate.md` and apply it before proceeding.

## Model Guidance

Use **claude-sonnet-4-6**. Unexpected complexity: stop and emit `REPLAN NEEDED: [what was unexpected]` - re-enter Opus before continuing.

## Output Style

One line per action: `Written: <path>`, command result. No preamble, no narration, no code explanation. Two lines max on failure. No extended thinking for code/test/commit steps.

---

## Domain Expert and Subagent Check

Read WP frontmatter before starting. Load `@references/implement-domain-subagent.md` for the full domain expert and subagent protocols.

---

## Working Directory

**Telemetry**: Run: `polaris telemetry record implement --feature <slug> --phase start --agent {{AGENT_NAME}} --wp <WP_ID>`

Two modes:

- **Default (worktree)**: `polaris implement WP##` creates `.worktrees/###-feature-WP##/`. After running it, `cd` into that directory for all file operations.
- **In-place**: `polaris implement WP## --in-place` skips the worktree. Use when worktrees cause issues or only one WP is in flight.

---

Run the workflow command to get the WP prompt:

```bash
polaris agent workflow implement $ARGUMENTS --agent <your-name>
```

The output ends with the completion command for moving to `for_review` - read to the end.

---

## Decision Memory and Failure Awareness (only if memory files exist)

Skip if neither `.polaris/memory/decisions-summary.md` nor `.polaris/memory/failures-summary.md` exists.

- **decisions-summary.md**: consult before non-trivial architectural choices; follow prior decisions; record new ones via `polaris memory record-decision`
- **failures-summary.md**: apply recorded fixes for matching error signatures; resolve new ones via `polaris memory resolve-failure`

---

## Pre-Implementation Context

If NOT WP01 and `control-map.md` exists: read it and the relevant shared dependency files for consistency. Otherwise skip.

## Commit Workflow

**BEFORE moving to for_review**, commit your implementation. Then:

```bash
polaris runtests --feature <slug>
```

On pass: moves to `for_review` automatically. On fail: fix regressions first.

**Fallback** (only if `test_status: "skipped"`):
```bash
polaris agent tasks move-task WP## --to for_review --note "No tests: docs-only WP"
```

---

**Telemetry**: Run: `polaris telemetry record implement --feature <slug> --phase complete --agent {{AGENT_NAME}} --wp <WP_ID>`
