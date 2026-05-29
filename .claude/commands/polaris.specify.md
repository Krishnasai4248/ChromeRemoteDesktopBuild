---
description: Create or update the feature specification from a natural language feature description.
---


## Model Guidance

This command does planning work. Use **claude-opus-4-6** for this session.

Spec synthesis and architecture decisions made here propagate through the entire project. A misread requirement or wrong architectural assumption compounds through every line of code that follows. Opus-level reasoning here is insurance, not indulgence.

If you are currently on Sonnet: switch to Opus before proceeding (`/model claude-opus-4-6`).

---

## User Input

**Telemetry**: Run: `polaris telemetry record specify --feature <slug> --phase start --agent claude`


```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Amend Mode

If `$ARGUMENTS` contains `--amend`, skip the Discovery Gate entirely and follow the Amend Workflow. Load `@references/specify-amend-mode.md` for the full step-by-step procedure. `--amend` is mutually exclusive with `--quick`.

---

## Quick Mode

If user passes `--quick` or arguments contain "quick": Skip discovery gate. Assume simple complexity. Ask only: (1) What is the feature? (2) Key acceptance criteria. Generate spec directly with no clarification rounds, no separate plan phase - produce spec.md and plan.md together. Commit and report.

## Working Directory

Run from the **main repository** root (planning repo). NO worktrees created during specify. Artifacts are committed to `polaris-specs/###-feature/` on the main branch. Worktrees are created later during `/polaris.implement`.

## Discovery Gate

Conduct a structured discovery interview scaled to complexity:

- **Trivial** (hello world, simple page): 1-2 questions max
- **Simple** (small UI, minor enhancement): 2-3 questions
- **Complex** (new subsystem, integration): 3-5 questions
- **Critical** (auth, payments, infra): 5+ questions

Rules:
- Determine the full question set then present ALL questions as a **numbered list** in one message
- End with `WAITING_FOR_DISCOVERY_INPUT`
- Developer responds with numbered answers (any order)
- If user says "just testing" or "skip questions" - minimize and use defaults
- When sufficient context gathered, present **Intent Summary** and confirm
- Empty invocation: stay in interview mode until description agreed

**Work Item Question**: Always include: "Is this linked to a tracker item? (ADO: AB#12345, GitHub: #42, Jira: PROJ-123, or 'skip')" Auto-detect provider from format; fetch from API when possible. If skipped: proceed without link.

**Estimation Question**: Always include: "What is the team's estimate without AI assistance? (e.g., '3 days', '16 hours', '5 SP')" Normalize to hours. Store in meta.json: `{"estimation": {"baseline_raw": "3 days", "baseline_hours": 24, "source": "developer|ado", "captured_at": "<ISO>"}}`. If skipped: proceed.

**Partial answers**: Use informed defaults for unanswered questions; document in Assumptions. Do not re-ask unless user requests.

## Mission Selection

After discovery, determine mission:
- **software-dev**: Building features, APIs, tools, apps
- **research**: Investigations, analysis, evaluations

Confirm with user unless explicit. If `--mission <key>` provided, use it directly.

## Workflow

**IMPORTANT - Write early, write often.** Context windows can drop mid-conversation. Every file write is a checkpoint.

1. **Check discovery status** - stay in question loop until Intent Summary confirmed

2. **Create feature** (once discovery complete):
   ```bash
   polaris agent feature create-feature "<slug>" --json
   ```
   Parse JSON for `feature`, `feature_dir`, `target_branch`. Run ONCE only.

3. **Create meta.json** in feature dir (required fields):
   ```json
   {
     "feature_number": "<number>", "slug": "<full-slug>",
     "friendly_name": "<Title>", "mission": "<mission>",
     "source_description": "$ARGUMENTS",
     "created_at": "<ISO>", "target_branch": "<current-branch>", "vcs": "git"
   }
   ```
   Add only the detected tracker field (`ado_work_item`, `github_issue`, or `jira_issue`).

   **Write discovery notes now:** Save `<feature_dir>/discovery-notes.md` with Intent Summary and Q&A. Delete after spec.md is finalized.

4. **Generate spec** from discovery answers:
   - Identify actors, actions, data, constraints, success metrics
   - Fill: User Scenarios, Functional Requirements (testable), Success Criteria (measurable, tech-agnostic), Key Entities
   - **Write to `<feature_dir>/spec.md` immediately.** A partial spec on disk beats a perfect spec lost to context.

5. **Control map** (if 2+ interrelated flows/forms/screens): Create `<feature_dir>/control-map.md` with Flows and Shared Dependencies tables. Target: under 100 lines. Skip if single-flow feature.

6. **Validate spec** against quality checklist:
   - Requirements testable, success criteria measurable and tech-agnostic
   - If items fail: fix spec.md and re-validate (max 3 iterations)
   - Save checklist to `<feature_dir>/checklists/requirements.md`

7. **Auto-review**: Re-read spec end-to-end, identify gaps, update spec.md on disk. Delete `discovery-notes.md` once finalized.

## Phase 2: Implementation Planning

Proceed directly to planning (eliminates separate `/polaris.plan` step).

**Planning interrogation** - scaled to complexity: suggest options and confirm rather than open-ended questions. End each question with `WAITING_FOR_PLANNING_INPUT`. Summarize into **Engineering Alignment** note and confirm.

**Plan generation**:
1. Run `polaris agent feature setup-plan --feature <feature-slug> --json`
2. Read spec and `.polaris/memory/constitution.md` (if exists)
3. Update Technical Context, Constitution Check, generate research.md (if unknowns), data-model.md, contracts/, quickstart.md
4. Commit planning artifacts

## Spec Guidelines

- Focus on **WHAT** and **WHY**, never HOW
- Written for business stakeholders; mandatory sections completed
- Make informed guesses using industry standards; document in Assumptions
- Success criteria: measurable, tech-agnostic, user-focused, verifiable

## On Completion

- If `--no-continue`: STOP and report spec path
- Default: ask "Spec and plan are ready. Proceed with autopilot? (y/n)"
  - **y**: Launch `/polaris.autopilot` with the current feature
  - **n**: Stop and report spec path


**Telemetry**: Run: `polaris telemetry record specify --feature <slug> --phase complete --agent claude`
