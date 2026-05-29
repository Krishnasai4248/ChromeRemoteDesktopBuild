---
description: Validate feature readiness and guide final acceptance steps.
---

## Advanced Command Gate

Load `.claude/commands/references/advanced-gate.md` and apply it before proceeding.

## Model Guidance

This command does planning work. Use **claude-opus-4-6** for this session.

Deep reasoning, synthesis, and decision-making here propagate to all downstream work. Opus-level reasoning is insurance, not indulgence.

If you are currently on Sonnet: switch to Opus before proceeding (`/model claude-opus-4-6`).

---

# /polaris.accept - Validate Feature Readiness

**Version**: 0.11.0+
**Purpose**: Validate all work packages are complete and feature is ready to merge.

## 📍 WORKING DIRECTORY: Run from MAIN repository

**Telemetry**: Run: `polaris telemetry record accept --feature <slug> --phase start --agent {{AGENT_NAME}}`


**IMPORTANT**: Accept runs from the main repository root, NOT from a WP worktree.

```bash
# If you're in a worktree, return to main first:
cd $(git rev-parse --show-toplevel)

# Then run accept:
polaris accept
```

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Separation of Duties Check

Before proceeding with acceptance, verify SoD compliance:
1. Resolve your identity: run `git config user.email` to determine who you are.
2. Check the audit trail at `.polaris/audit-trail/<feature-slug>.jsonl` for this feature's implementer and reviewer.
3. The acceptor must be different from BOTH the implementer (actor who moved WP to "doing") and the reviewer (actor who moved WP to "for_review" or "done" during review).
4. If your email matches either the implementer or reviewer:
   - If `quality.sod_enforcement` is enabled in `.polaris/config.yaml`: STOP and reject with "Acceptor must be different from implementer/reviewer".
   - If disabled (default): warn "SoD: acceptor overlaps with implementer/reviewer" but allow acceptance to proceed.
   - Override: use `--self-review` flag with a justification string. The override and justification will be recorded in the audit trail with `override: true`.
5. The acceptance action is automatically recorded in the audit trail.

## Discovery (mandatory)

Before running the acceptance workflow, gather the following:

1. **Feature slug** (e.g., `005-awesome-thing`). If omitted, detect automatically.
2. **Acceptance mode**:
   - `pr` when the feature will merge via hosted pull request.
   - `local` when the feature will merge locally without a PR.
   - `checklist` to run the readiness checklist without committing or producing merge instructions.
3. **Validation commands executed** (tests/builds). Collect each command verbatim; omit if none.
4. **Acceptance actor** (optional, defaults to the current agent name).

Ask one focused question per item and confirm the summary before continuing. End the discovery turn with `WAITING_FOR_ACCEPTANCE_INPUT` until all answers are provided.

## Execution Plan

1. Compile the acceptance options into an argument list:
   - Always include `--actor "__AGENT__"`.
   - Append `--feature "<slug>"` when the user supplied a slug.
   - Append `--mode <mode>` (`pr`, `local`, or `checklist`).
   - Append `--test "<command>"` for each validation command provided.
2. Run `{SCRIPT}` (the CLI wrapper) with the assembled arguments **and** `--json`.
3. Parse the JSON response. It contains:
   - `summary.ok` (boolean) and other readiness details.
   - `summary.outstanding` categories when issues remain.
   - `instructions` (merge steps) and `cleanup_instructions`.
   - `notes` (e.g., acceptance commit hash).
4. Present the outcome:
   - If `summary.ok` is `false`, list each outstanding category with bullet points and advise the user to resolve them before retrying acceptance.
   - If `summary.ok` is `true`, display:
     - Acceptance timestamp, actor, and (if present) acceptance commit hash.
     - Merge instructions and cleanup instructions as ordered steps.
     - Validation commands executed (if any).
5. When the mode is `checklist`, make it clear no commits or merge instructions were produced.

## Output Requirements

- Summaries must be in plain text (no tables). Use short bullet lists for instructions.
- Surface outstanding issues before any congratulations or success messages.
- If the JSON payload includes warnings, surface them under an explicit **Warnings** section.
- Never fabricate results; only report what the JSON contains.

## Error Handling

- If the command fails or returns invalid JSON, report the failure and request user guidance (do not retry automatically).
- When outstanding issues exist, do **not** attempt to force acceptance-return the checklist and prompt the user to fix the blockers.

**Telemetry**: Run: `polaris telemetry record accept --feature <slug> --phase complete --agent {{AGENT_NAME}}`
