---
description: Perform structured code review and kanban transitions for completed task prompt files.
scripts:
  sh: polaris agent check-prerequisites --json --include-tasks
  ps: polaris agent -Json -IncludeTasks
---
## Model Guidance

This command does planning work. Use **claude-opus-4-6** for this session.

Deep reasoning, synthesis, and decision-making here propagate to all downstream work. Opus-level reasoning is insurance, not indulgence.

If you are currently on Sonnet: switch to Opus before proceeding (`/model claude-opus-4-6`).

---


## User Input

```text

**Telemetry**: Run: `polaris telemetry record review --feature <slug> --phase start --agent {{AGENT_NAME}} --wp <WP_ID>`

$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Location Pre-flight
Run `pwd` and `git branch --show-current`. Expected: inside `.worktrees/` on a WP branch (NOT `main`). If on main: navigate to the WP worktree first.

## Steps

1. Run `{SCRIPT}` from repo root; capture `FEATURE_DIR`, `AVAILABLE_DOCS`, and `tasks.md` path.

2. **Determine review target**: If user input specifies a filename, validate it exists under `tasks/` with `lane: "for_review"`. Otherwise, select the oldest WP in `for_review`. Abort if none waiting.

3. **Load context**: Read prompt frontmatter (`task_id`, `phase`, `dependencies`), body sections, supporting docs (constitution, plan, spec, data-model, contracts). Review associated code diffs and tests.
   - **Dependency checks** (v0.11.0+): Verify dependency WPs are merged; identify dependent WPs and warn about rebase if requesting changes.

4. **Conduct adversarial review** -- assume problems exist until proven otherwise:

   **4.1 Completeness**: ALL subtasks implemented (not just commented), ALL acceptance criteria satisfied, ALL files created/modified, ALL error/edge cases handled. Reject if TODOs, FIXMEs, mock/simulated data, or deferred features found.

   **4.2 Implementation Quality**: Actually run the code. Check return values are real (not mocked). Verify DB/file operations persist. Reject simulated results, pass-through functions, empty exception handlers.

   **4.3 Efficiency**: No O(n^2) where O(n) works, no redundant file reads, no unnecessary subprocess calls, no polling when events possible.

   **4.4 Test Quality**: Tests cover failure cases, use real data, verify behavior (not implementation), have meaningful assertions. Reject tests that always pass or don't call the code.

   **4.5 Error Handling**: External calls wrapped with specific exceptions, actionable error messages, resource cleanup on error, input validation.

   **4.6 Cross-Platform**: `pathlib.Path` for paths, no hardcoded separators, no POSIX-only commands, universal newlines.

   **4.7 Security (CRITICAL)**:
   - **Injection**: Parameterized queries (no f-string SQL), list-form subprocess (no shell=True with user input), path traversal checks, no eval/exec on user data, yaml.safe_load
   - **Auth**: Authentication before privileged ops, authorization checked, no hardcoded credentials, modern password hashing
   - **Secrets**: No passwords/tokens in logs/errors/git, env vars for secrets, redacted in debug output
   - **Validation**: All user input validated (format, length, range, type), server-side validation
   - **Files**: Secure temp files, appropriate permissions, symlink protection
   - **Dependencies**: Pinned versions, no known CVEs, minimal set
   - **Mandatory grep checks**: Search changed files for `shell=True`, f-string SQL/eval, passwords/secrets in diffs, unsafe deletes, `random.` instead of `secrets`, broad `except:`, `eval`/`exec`, `yaml.load`. **Any security check failure = AUTOMATIC REJECTION.**

   **4.8 Logic**: No circular deps, race conditions, missing null checks, inconsistent state, mutable default args.

   **4.9 Documentation**: Complex logic commented (why not what), public functions have docstrings, no magic numbers, descriptive names.

   **4.10 Verification (ACTUALLY RUN)**:
   - Search for `TODO`/`FIXME`/`HACK`, `simulated`/`mock_`/`fake_` in production code
   - Run `pytest <test_files> -v --tb=short` -- all pass, coverage >80%
   - Run `ruff check <changed_files>`
   - Test actual behavior (not just unit tests)

   **Default stance: REJECT.** Only approve when you've actively tried to find problems and found none.

5. **Dependency checks** (workspace-per-WP):

   <!-- dependency_check -->
   - Check if this WP declares dependencies in frontmatter. If so, verify those WPs are merged/done before approving.
   <!-- dependent_check -->
   - Check if other WPs depend on this one (downstream dependents). If found, note them.
   <!-- rebase_warning -->
   - If this WP has dependents AND changes are requested, warn: dependents will need rebase after changes are applied.
   <!-- verify_instruction -->
   - Verify the WP's implementation matches its declared dependencies and does not introduce undeclared coupling.

6. **Decide outcome**:

   **Needs changes**: Insert `## Review Feedback` after frontmatter with status, key issues, positives, action items. Set `lane: "planned"`, `review_status: "has_feedback"`, `reviewed_by`. Append Activity Log entry. Run `polaris agent move-task <FEATURE> <TASK_ID> planned --note "..."`.

   **Approved**: Append Activity Log entry. Set `lane: "done"`, `review_status: "approved without changes"`, `reviewed_by`. Run `polaris agent mark-status --task-id <TASK_ID> --status done`.

7. **Report**: Task ID, approval status, key findings, tests executed, follow-up actions.

Context: {ARGS}

All review feedback lives inside the prompt file so future implementers see historical decisions.


**Telemetry**: Run: `polaris telemetry record review --feature <slug> --phase complete --agent {{AGENT_NAME}} --wp <WP_ID>`
