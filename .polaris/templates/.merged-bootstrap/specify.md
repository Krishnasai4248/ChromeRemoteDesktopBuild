---
description: Create or update the feature specification from a natural language feature description.
---

## Model Guidance

This command does planning work. Use **claude-opus-4-6** for this session.

Spec decisions made here propagate through the entire project. If you are on Sonnet: switch to Opus before proceeding (`/model claude-opus-4-6`).

---

## User Input

**Telemetry**: Run: `polaris telemetry record specify --feature <slug> --phase start --agent {{AGENT_NAME}}`


```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Amend Mode

If `$ARGUMENTS` contains `--amend`, skip the Discovery Gate. Load `@references/specify-amend-mode.md` for the full amend procedure.

## Quick Mode

If user passes `--quick`: Skip discovery gate. Ask only (1) feature description and (2) key acceptance criteria. Produce spec.md and plan.md together, commit, report.

## Working Directory

Run from the **main repository** root (planning repo). NO worktrees are created during specify. Output and committed artifacts go to `polaris-specs/###-feature/` on the main branch. Worktrees are created later via `polaris implement WP##`.

If `pwd` contains `.worktrees/`: STOP. Navigate back to the main repo root first.

## Discovery Gate

Conduct a structured discovery interview scaled to complexity:

- **Trivial**: 1-2 questions max
- **Simple**: 2-3 questions
- **Complex**: 3-5 questions
- **Critical**: 5+ questions

Rules:
- Present ALL questions as a **numbered list** in one message
- End with `WAITING_FOR_DISCOVERY_INPUT`
- If user says "skip questions": minimize and use defaults
- Present **Intent Summary** when sufficient context gathered; confirm before proceeding

**Work Item Question**: Always include: "Is this linked to a tracker item? (ADO: AB#12345, GitHub: #42, Jira: PROJ-123, or 'skip')" Auto-detect provider; fetch details when possible.

**Estimation Question**: Always include: "Team estimate without AI assistance? (e.g., '3 days', '5 SP')" Normalize to hours. Store in meta.json under `estimation`. If skipped: proceed.

**Partial answers**: Use informed defaults; document in Assumptions. Do not re-ask.

## Mission Selection

- **software-dev**: Building features, APIs, tools, apps
- **research**: Investigations, analysis, evaluations

Confirm unless explicit. If `--mission <key>` provided, use directly.

## Workflow

**Write early, write often.** Every file write is a context-loss checkpoint.

1. Stay in discovery loop until Intent Summary confirmed.

2. Create feature:
   ```bash
   polaris agent feature create-feature "<slug>" --json
   ```
   Parse for `feature`, `feature_dir`, `target_branch`. Run ONCE.

3. Create meta.json (required fields only):
   ```json
   {"feature_number": "<n>", "slug": "<slug>", "friendly_name": "<Title>",
    "mission": "<mission>", "source_description": "$ARGUMENTS",
    "created_at": "<ISO>", "target_branch": "<branch>", "vcs": "git"}
   ```
   Add only the detected tracker field. Write `discovery-notes.md` now; delete after spec finalized.

4. Generate spec from discovery answers. Fill: User Scenarios, Functional Requirements, Success Criteria, Key Entities. **Write to `<feature_dir>/spec.md` immediately.**

5. Control map if 2+ interrelated flows: `<feature_dir>/control-map.md` with Flows and Shared Dependencies tables (under 100 lines). Skip if single-flow.

6. Validate spec: requirements testable, success criteria measurable and tech-agnostic. Fix and re-validate (max 3 iterations). Save checklist to `checklists/requirements.md`.

7. Auto-review: re-read end-to-end, fix gaps, delete `discovery-notes.md`.

## Phase 2: Implementation Planning

Run directly after spec (eliminates separate `/polaris.plan`).

1. `polaris agent feature setup-plan --feature <feature-slug> --json`
2. Read spec and `.polaris/memory/constitution.md` if exists
3. Generate: Technical Context, research.md (if unknowns), data-model.md, contracts/, quickstart.md
4. Commit planning artifacts

## Spec Guidelines

- Focus on WHAT and WHY, never HOW. Written for business stakeholders.
- Mandatory sections completed; success criteria measurable, tech-agnostic, verifiable.

## On Completion

- `--no-continue`: STOP and report spec path
- Default: ask "Proceed with autopilot? (y/n)" - y launches `/polaris.autopilot`


**Telemetry**: Run: `polaris telemetry record specify --feature <slug> --phase complete --agent {{AGENT_NAME}}`
