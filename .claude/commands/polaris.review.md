---
description: Perform structured code review and kanban transitions for completed task prompt files
---


## Advanced Command Gate

Load `.claude/commands/references/advanced-gate.md` and apply it before proceeding.

## Model Guidance

This command does planning work. Use **claude-opus-4-6** for this session.

Deep reasoning, synthesis, and decision-making here propagate to all downstream work. Opus-level reasoning is insurance, not indulgence.

If you are currently on Sonnet: switch to Opus before proceeding (`/model claude-opus-4-6`).

---

## Step 1: Claim the WP for review

```bash
polaris agent workflow review $ARGUMENTS --agent <your-name>
```

If no WP ID provided, auto-finds first `lane: "for_review"` WP and moves it to doing.

## Step 2: Separation of Duties Check

**Telemetry**: Run: `polaris telemetry record review --feature <slug> --phase start --agent claude --wp <WP_ID>`

1. `git config user.email` -> your identity
2. Check `.polaris/audit-trail/<feature-slug>.jsonl` for this WP's implementer.
3. If your email matches:
   - `quality.sod_enforcement` enabled in config: STOP with "Reviewer must differ from implementer"
   - Disabled (default): warn but proceed
   - Override: `--self-review "<justification>"` (recorded in audit trail)

## Step 3: Dependency checks

<!-- dependency_check -->
- Confirm each dep WP is merged to main before reviewing this WP.
<!-- dependent_check -->
- Note any WPs depending on this one and their current lanes.
<!-- rebase_warning -->
- If requesting changes with dependents: warn those agents to rebase.
<!-- verify_instruction -->
- Verify dep declarations match actual code coupling.

## Step 4: Read implementation

Switch to WP branch. Read ALL changed files via `git diff`.

## Step 5: Multi-Persona Review Passes

Load `@references/review-passes.md` for full criteria. Perform all 3 passes sequentially with separate headings and verdicts. Check `.polaris/config.yaml` for `review_passes` section (enabled/required per pass); default: all 3 enabled and required.

Do NOT skip or combine passes.

## Step 6: Complete the review

- **APPROVED**: `polaris agent tasks move-task WP## --to done --note "Review passed: <summary>"`
- **REJECTED**: write feedback to temp file, then `polaris agent tasks move-task WP## --to planned --review-feedback-file <temp-file-path>`

**Telemetry**: Run: `polaris telemetry record review --feature <slug> --phase complete --agent claude --wp <WP_ID>`
