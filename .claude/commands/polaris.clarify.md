---
description: Identify underspecified areas in the current feature spec by asking up to 5 highly targeted clarification questions and encoding answers back into the spec.
---

## Model Guidance

This command does planning work. Use **claude-opus-4-6** for this session.

Deep reasoning, synthesis, and decision-making here propagate to all downstream work. Opus-level reasoning is insurance, not indulgence.

If you are currently on Sonnet: switch to Opus before proceeding (`/model claude-opus-4-6`).

---

**Path reference rule:** When you mention directories or files, provide either the absolute path or a path relative to the project root (for example, `polaris-specs/<feature>/tasks/`). Never refer to a folder by name alone.


*Path: [.polaris/templates/commands/clarify.md](.polaris/templates/commands/clarify.md)*

**Telemetry**: Run: `polaris telemetry record clarify --feature <slug> --phase start --agent claude`



## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

---

## Location Pre-flight Check

**BEFORE PROCEEDING:** Verify you are working in the feature worktree.

```bash
pwd
git branch --show-current
```

**Expected output:**
- `pwd`: Should end with `.worktrees/001-feature-name` (or similar feature worktree)
- Branch: Should show your feature branch name like `001-feature-name` (NOT `main`)

**If you see the main branch or main repository path:**

⛔ **STOP - You are in the wrong location!**

This command updates your feature's spec.md file. You must be in the feature worktree to ensure changes go to the correct location.

**Correct the issue:**
1. Navigate to your feature worktree: `cd .worktrees/001-feature-name`
2. Verify you're on the correct feature branch: `git branch --show-current`
3. Then run this clarify command again

---

## What You Have Available

After running `polaris agent -Json -PathsOnly`, you will have paths to:
- **FEATURE_DIR**: Absolute path to your feature directory (polaris-specs/001-feature-name/)
- **FEATURE_SPEC**: Absolute path to spec.md (the file you'll be clarifying)

You may also have:
- **plan.md**: If planning has started (optional)
- **tasks.md**: If task breakdown exists (optional)

---

## Workflow Context

**Before this**: `/polaris.specify` created spec.md (your starting requirements)

**This command**:
- Identifies ambiguities and gaps in your spec
- Asks clarification questions (max 5)
- Updates spec.md with clarifications directly
- Reduces downstream rework risk

**After this**:
- Review clarified spec
- Run `/polaris.plan` to create implementation plan
- Or run `/polaris.clarify` again if more questions arise post-planning

This command is optional but recommended before planning to reduce rework.

---

## Outline

Goal: Detect and reduce ambiguity or missing decision points in the active feature specification and record the clarifications directly in the spec file.

Note: This clarification workflow is expected to run (and be completed) BEFORE invoking `/polaris.plan`. If the user explicitly states they are skipping clarification (e.g., exploratory spike), you may proceed, but must warn that downstream rework risk increases.

Execution steps:

1. Run `polaris agent -Json -PathsOnly` from repo root **once** (combined `--json --paths-only` mode / `-Json -PathsOnly`). Parse minimal JSON payload fields:
   - `FEATURE_DIR`
   - `FEATURE_SPEC`
   - (Optionally capture `IMPL_PLAN`, `TASKS` for future chained flows.)
   - If JSON parsing fails, abort and instruct user to re-run `/polaris.specify` or verify feature branch environment.

2. Load the current spec file. Perform a structured ambiguity & coverage scan using this taxonomy. For each category, mark status: Clear / Partial / Missing. Produce an internal coverage map used for prioritization (do not output raw map unless no questions will be asked).

   Functional Scope & Behavior:
   - Core user goals & success criteria
   - Explicit out-of-scope declarations
   - User roles / personas differentiation

   Domain & Data Model:
   - Entities, attributes, relationships
   - Identity & uniqueness rules
   - Lifecycle/state transitions
   - Data volume / scale assumptions

   Interaction & UX Flow:
   - Critical user journeys / sequences
   - Error/empty/loading states
   - Accessibility or localization notes

   Non-Functional Quality Attributes:
   - Performance (latency, throughput targets)
   - Scalability (horizontal/vertical, limits)
   - Reliability & availability (uptime, recovery expectations)
   - Observability (logging, metrics, tracing signals)
   - Security & privacy (authN/Z, data protection, threat assumptions)
   - Compliance / regulatory constraints (if any)

   Integration & External Dependencies:
   - External services/APIs and failure modes
   - Data import/export formats
   - Protocol/versioning assumptions

   Edge Cases & Failure Handling:
   - Negative scenarios
   - Rate limiting / throttling
   - Conflict resolution (e.g., concurrent edits)

   Constraints & Tradeoffs:
   - Technical constraints (language, storage, hosting)
   - Explicit tradeoffs or rejected alternatives

   Terminology & Consistency:
   - Canonical glossary terms
   - Avoided synonyms / deprecated terms

   Completion Signals:
   - Acceptance criteria testability
   - Measurable Definition of Done style indicators

   Misc / Placeholders:
   - TODO markers / unresolved decisions
   - Ambiguous adjectives ("robust", "intuitive") lacking quantification

   For each category with Partial or Missing status, add a candidate question opportunity unless:
   - Clarification would not materially change implementation or validation strategy
   - Information is better deferred to planning phase (note internally)

3. Generate the full list of clarification questions internally (do not output yet). Apply these rules:

   - Scan ALL taxonomy categories with Partial or Missing status (from the coverage map in Step 2).
   - For each such category, generate one focused question that resolves the primary ambiguity in that category.
   - Each question must be answerable with EITHER:
      * A short multiple-choice selection (2-5 distinct, mutually exclusive options), OR
      * A short phrase (explicitly constrain: "Answer in <=10 words").
   - Only include questions whose answers materially impact architecture, data modeling, task decomposition, test design, UX behavior, operational readiness, or compliance validation.
   - Exclude questions already answered, trivial stylistic preferences, or plan-level execution details (unless blocking correctness).
   - Favor clarifications that reduce downstream rework risk or prevent misaligned acceptance tests.
   - For vague qualitative terms ("fast", "robust", "intuitive", "scalable"): generate a question that converts the term to a measurable target. Format as: "The spec says '<term>' - what is the measurable target? (e.g., '<example metric>')"
   - For missing edge case handling: generate one question per unaddressed failure mode category (not per individual edge case).
   - Scale question count to spec complexity: a spec with 2 gaps gets 2 questions; a spec with 10 gaps gets up to 10 questions. Never ask questions for Clear categories.
   - If zero categories have Partial or Missing status: skip Steps 4-6 entirely and jump to Step 7 with no questions (report "No critical ambiguities detected" in Step 8).

4. Ask questions one at a time, sequentially. For each question:

   Format:
   "[<N> remaining] [Category: <taxonomy category>] <question text>
   Options: (A) ... (B) ... (C) ... (D) Custom answer (<=10 words)"
   OR for open-ended: "[<N> remaining] [Category: <taxonomy category>] <question text>
   Format: Short answer (<=10 words)"

   End each question with `WAITING_FOR_CLARIFICATION_INPUT`.

   After receiving the answer:
   - If the answer is "skip": document as "Deferred - not answered" in the Clarifications section. Move to next question. Do NOT re-ask.
   - If the answer is ambiguous: apply best-effort interpretation and note the interpretation used.
   - If the user says "stop", "done", or "proceed": treat all remaining questions as skipped and jump to Step 7.
   - For each accepted answer: immediately apply the integration rules from Step 5 and save the spec.
   - Then ask the next question.

   Continue until all questions in the internal list are asked and answered (or skipped).

4b. Completeness check after all questions answered:

   Re-scan all taxonomy categories against the newly updated spec. If any answers revealed NEW gaps
   (i.e., an answer introduced a new entity or constraint that is itself unspecified), generate up to
   5 follow-up questions covering only those newly revealed gaps. Ask them sequentially in the same
   format as Step 4.

   No further rounds after this follow-up pass. Any remaining gaps are marked as
   "Deferred to planning phase" in the Clarifications section.

   If no new gaps are revealed: skip this step.

5. Integration after EACH accepted answer (incremental update approach):
    - Maintain in-memory representation of the spec (loaded once at start) plus the raw file contents.
    - For the first integrated answer in this session:
       * Ensure a `## Clarifications` section exists (create it just after the highest-level contextual/overview section per the spec template if missing).
       * Under it, create (if not present) a `### Session YYYY-MM-DD` subheading for today.
    - Append a bullet line immediately after acceptance: `- Q: <question> → A: <final answer>`.
    - Then immediately apply the clarification to the most appropriate section(s):
       * Functional ambiguity → Update or add a bullet in Functional Requirements.
       * User interaction / actor distinction → Update User Stories or Actors subsection (if present) with clarified role, constraint, or scenario.
       * Data shape / entities → Update Data Model (add fields, types, relationships) preserving ordering; note added constraints succinctly.
       * Non-functional constraint → Add/modify measurable criteria in Non-Functional / Quality Attributes section (convert vague adjective to metric or explicit target).
       * Edge case / negative flow → Add a new bullet under Edge Cases / Error Handling (or create such subsection if template provides placeholder for it).
       * Terminology conflict → Normalize term across spec; retain original only if necessary by adding `(formerly referred to as "X")` once.
    - If the clarification invalidates an earlier ambiguous statement, replace that statement instead of duplicating; leave no obsolete contradictory text.
    - Save the spec file AFTER each integration to minimize risk of context loss (atomic overwrite).
    - Preserve formatting: do not reorder unrelated sections; keep heading hierarchy intact.
    - Keep each inserted clarification minimal and testable (avoid narrative drift).

6. Validation (performed after EACH write plus final pass):
   - Clarifications session contains exactly one bullet per accepted answer (no duplicates).
   - Updated sections contain no lingering vague placeholders the new answer was meant to resolve.
   - No contradictory earlier statement remains (scan for now-invalid alternative choices removed).
   - Markdown structure valid; only allowed new headings: `## Clarifications`, `### Session YYYY-MM-DD`.
   - Terminology consistency: same canonical term used across all updated sections.

7. Write the updated spec back to `FEATURE_SPEC`.

8. Report completion (after all questions answered or no questions found):
   - Number of questions asked & answered.
   - Path to updated spec.
   - Sections touched (list names).
   - Coverage summary listing each taxonomy category with one of these status labels:
     - "Resolved": category was Partial/Missing and is now fully addressed by answers in this session.
     - "Clear": category was already Clear at session start.
     - "Deferred-to-planning": category gap was intentionally skipped or could not be resolved.
     Present as plain text or bullet list, not a table.
   - There must be NO "Outstanding" items after a complete session. If any taxonomy category
     remains Partial/Missing and was NOT explicitly deferred, return to Step 4b for a final pass.
   - If all categories are Resolved or Clear: output "Spec is fully clarified. Ready for /polaris.plan."
     Do NOT suggest running /polaris.clarify again.
   - If any Deferred-to-planning items exist: list them and note they will be resolved during planning.
   - Suggested next command.

Behavior rules:
- If no meaningful ambiguities found at session start: respond "No critical ambiguities detected. Spec is ready for /polaris.plan." and stop. Do not ask any questions.
- If a second invocation is run on a fully clarified spec: respond "No critical ambiguities detected. Spec was fully clarified in the previous session." and stop.
- If spec file missing: instruct user to run `/polaris.specify` first (do not create a new spec here).
- Avoid speculative tech stack questions unless the absence blocks functional clarity.
- Respect user early termination signals ("stop", "done", "proceed").
- If no questions asked due to full coverage, output a compact coverage summary (all categories Clear) then output "Spec is ready for /polaris.plan."

Context for prioritization: $ARGUMENTS

**Telemetry**: Run: `polaris telemetry record clarify --feature <slug> --phase complete --agent claude`
