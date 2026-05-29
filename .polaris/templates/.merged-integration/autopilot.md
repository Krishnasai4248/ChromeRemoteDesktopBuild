---
description: Run the full Aptean application pipeline autonomously with retry logic.
---

## Model Guidance

- **Planning steps** (specify, plan, tasks): use **claude-opus-4-6**
- **Implementation steps** (code writing, tool calls, tests): use **claude-sonnet-4-6**

If a WP surfaces unexpected complexity: stop, emit `REPLAN NEEDED`, re-enter planning with Opus before resuming.

## Tool Preferences

1. `Read` / `Grep` / `Glob` - local files (always prefer)
2. `WebFetch` - public URLs, text only
3. Headless browser - dynamic/auth-gated pages (~82% fewer tokens than screenshot tools)
4. Screenshot browser - last resort only; ~10x more tokens than WebFetch, deprioritised in all skills
5. PDFs - extract as text (not images); ~90% token reduction vs. image path. Applies to all implementation skills automatically.

## Output Style

- After writing a file: `Written: <path>`
- After a command: one line with result
- After a WP: `WP## done`
- NO preamble, NO narration, NO code explanation
- Do NOT use extended thinking for implementation, test, or commit steps

---

## User Input

**Telemetry**: Run: `polaris telemetry record autopilot --feature <slug> --phase start --agent {{AGENT_NAME}}`


```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Quick Mode

If `--quick`: use quick mode for specify stage (2 questions max, combined spec+plan). All downstream stages run with full quality gates.

## Discovery

1. **Context**: New application, existing feature, or `--resume` from saved state.
2. **Feature slug**: Detect from directory, arguments, or ask.
3. **Retry limit**: Default 3 per stage.
4. **On failure**: Default skip-and-continue.
5. **Mode**: `--quick` activates quick mode (record in state).

End with `WAITING_FOR_AUTOPILOT_INPUT`.

## Pipeline Stages

### Stage 1: Setup (new apps only)

Run `/polaris.setup` with Aptean defaults. Skip if `.polaris/` exists.

### Stage 2: Build

**2a. Specify + Plan** (`/polaris.specify`): Create spec + plan. Skip if both exist.

**2b. Tasks** (`/polaris.tasks`): Generate WPs. Run `polaris agent feature finalize-tasks --json`. Skip if `tasks.md` exists.

**2c. Test Plan**: Create `polaris-specs/<slug>/test-plan.md` (Unit/Integration/Acceptance/Edge Cases, all `test_` prefixed). Skip if exists.

**2d. Implement**: For each WP in dependency order:
1. `polaris implement <WP_ID>` (add `--base <dep>` if needed). Verify `doing`.
2. **Worktree handoff**: parse and execute `cd` command, verify `pwd` contains `.worktrees/` and branch is NOT `main`.
3. Implement fully per tasks file, run tests, commit
4. **Return to main repo root** before next WP
5. On failure: retry (max 3), then skip dependents

### Stage 3: Ship

**3a. Test Execution** (per WP):
1. `polaris agent tasks move-task <WP_ID> --to testing`
2. `python .polaris/scripts/tasks/run_tests.py --project-root . --wp <WP_ID> --json` - gate: `success: true`
3. E2E if `.spec.js` exists: `polaris runtests --wp <WP_ID>`
4. On failure: move to doing, fix, retry (max 3)
5. Test plan coverage gate: `>= 80%`
6. On success: move to `for_review`

**Kanban flow**: planned -> doing -> testing -> (doing if fail) -> for_review -> done

**3b. Review** (`/polaris.review`): Approve -> done. Reject -> doing, fix, restart 3a.

**3c. Accept** (`/polaris.accept`): Once all WPs pass review.

**3d. Merge** (`/polaris.merge`): Preflight, merge all WPs, clean up worktrees.

## State Persistence

State saved to `.polaris/autopilot-state.json` after every transition. Resume: `--resume`. Abort: `--abort`.

## Final Summary

Pipeline stages, WP counts (succeeded/failed/skipped), per-WP test results, failed WP details, next steps.

## Error Handling

Never halt silently. Never lose work. State updated atomically. All commands cross-platform.


**Telemetry**: Run: `polaris telemetry record autopilot --feature <slug> --phase complete --agent {{AGENT_NAME}}`
