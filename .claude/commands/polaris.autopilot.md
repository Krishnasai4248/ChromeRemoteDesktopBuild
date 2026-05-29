---
description: Run the full Aptean application pipeline autonomously with retry logic.
---


## Model Guidance

Autopilot spans both planning and implementation phases. Route accordingly:

- **Planning steps** (specify, plan, tasks generation): use **claude-opus-4-6**
- **Implementation steps** (per-WP code writing, tool calls, test runs): use **claude-sonnet-4-6**

If a WP surfaces unexpected complexity, do not self-escalate. Stop, emit a `REPLAN NEEDED` signal, and re-enter the planning phase with Opus before resuming implementation.

## Output Style

One line per action: `Written: <path>`, `Run: <cmd> -> <result>`, `WP## done`, `Stage <N> done`. On failure: two lines max. No preamble, no narration, no mid-pipeline summaries. No extended thinking for implementation steps.

---

## User Input

**Telemetry**: Run: `polaris telemetry record autopilot --feature <slug> --phase start --agent claude`

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Quick Mode

If `--quick` is passed: use quick mode for the specify stage (2 questions max, combined spec+plan). All downstream stages run normally with full quality gates.

## Discovery

1. **Context**: New application (full pipeline), existing feature (resume from current phase), or `--resume` (from saved state).
2. **Feature slug**: Detect from directory, arguments, or ask.
3. **Retry limit**: Default 3 attempts per stage.
4. **On failure**: Default skip-and-continue (skip failed WP, continue with independents).
5. **Mode**: `--quick` activates quick mode (record in state).

End with `WAITING_FOR_AUTOPILOT_INPUT`.

## Pipeline Stages

### Stage 1: Setup (new apps only)

Run `/polaris.setup` with Aptean defaults. Skip if `.polaris/` exists.

### Stage 2: Build

**2a. Specify + Plan** (`/polaris.specify`): Create spec with auto-review, generate plan. Skip if both exist.

**2b. Tasks** (`/polaris.tasks`): Generate WPs. Run `polaris agent feature finalize-tasks --json`. Skip if `tasks.md` exists.

**2c. Test Plan**: Create `polaris-specs/<slug>/test-plan.md` with Unit Tests (min 2/WP), Integration Tests, Acceptance Tests, Edge Cases. All names start `test_`, all unique. Skip if exists.

**2d. Implement**: For each WP in dependency order:
1. `polaris implement <WP_ID> --feature <slug>` (add `--base <dep>` if deps). Verify `doing`.
2. **Worktree handoff**: parse `cd` from output, execute, verify `pwd` contains `.worktrees/` and branch is NOT `main`. If verification fails, STOP.
3. Follow implementation prompt from tasks file
4. Implement fully, run tests, commit
5. **Return to main repo root** before next WP
6. On failure: retry up to limit, then mark failed and skip dependents

### Stage 3: Quality Assurance and Ship

**3a. Test Execution** (per WP):
1. `polaris agent tasks move-task <WP_ID> --to testing`
2. `python .polaris/scripts/tasks/run_tests.py --project-root . --wp <WP_ID> --json` - gate: `success: true, failed: 0`
3. Run E2E if `.spec.js` files exist: `polaris runtests --wp <WP_ID> --feature <slug>`
4. On failure: move back to doing, fix, retry (max 3)
5. Validate test plan coverage: gate `coverage_percent >= 80`

**3b. Mutation Testing** (per WP after tests pass):
1. Identify changed files via `git diff`
2. Introduce 3-5 mutations per file (negate conditions, remove returns, swap operators)
3. Re-run relevant tests for each mutation
4. Gate: survival rate > 30% requires additional tests
5. Log results in WP activity log

**3c. Self-Review** (after mutation testing):
Check: every acceptance criterion implemented, no unintended changes, no hardcoded values/secrets, follows constitution standards. Fix issues, re-run tests if needed. Move to `for_review` with self-review note.

**Kanban flow**: planned -> doing -> testing -> (doing if fail) -> for_review -> done

**3d. Review** (`/polaris.review`): For each WP in for_review. Approve -> done. Reject -> doing, fix, restart 3a.

**3e. Accept** (`/polaris.accept`): Once all WPs pass review.

**3f. Merge** (`/polaris.merge`): Preflight, merge all WPs, clean up worktrees.

## State Persistence

Load `@references/autopilot-state.md` for the full state schema. Resume: `--resume`. Abort: `--abort`.

## Final Summary

Display: pipeline stages, succeeded/failed/skipped WP counts, per-WP test results (run/passed/failed/coverage), failed WP details with error and impact, next steps.

## Error Handling

Never halt silently. Never lose work. State updated atomically. All commands cross-platform.

**Telemetry**: Run: `polaris telemetry record autopilot --feature <slug> --phase complete --agent claude`
