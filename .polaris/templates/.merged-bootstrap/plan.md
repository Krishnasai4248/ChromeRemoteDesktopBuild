---
description: Execute the implementation planning workflow using the plan template to generate design artifacts.
---

# /polaris.plan - Create Implementation Plan

**Version**: 0.11.0+

## Model Guidance

This command does planning work. Use **claude-opus-4-6** for this session.

Architecture decisions made here define implementation scope for every WP that follows. If you are on Sonnet: switch to Opus (`/model claude-opus-4-6`).

---

## 📍 WORKING DIRECTORY: Stay in planning repository

**Telemetry**: Run: `polaris telemetry record plan --feature <slug> --phase start --agent {{AGENT_NAME}}`


**IMPORTANT**: Plan works in the planning repository. NO worktrees created.

```bash
# Run from project root (same directory as /polaris.specify):
# You should already be here if you just ran /polaris.specify

# Creates:
# - polaris-specs/###-feature/plan.md → In planning repository
# - Commits to target branch
# - NO worktrees created
```

**Do NOT cd anywhere**. Stay in the planning repository root.

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Location Check (0.11.0+)

This command runs in the **planning repository**, not in a worktree.

- Verify you're on the target branch (meta.json → target_branch) before scaffolding plan.md
- Planning artifacts live in `polaris-specs/###-feature/`
- The plan template is committed to the target branch after generation

**Path reference rule:** When you mention directories or files, provide either the absolute path or a path relative to the project root (for example, `polaris-specs/<feature>/tasks/`). Never refer to a folder by name alone.

## Decision Memory (only if memory file exists)

Skip this section entirely if `.polaris/memory/decisions-summary.md` does not exist (greenfield projects).

If the file exists, read it once and reuse settled architectural decisions (tech stack, patterns, storage choices) unless the spec explicitly requires something different. When you make a new key design decision during planning, record it:
```bash
polaris memory record-decision --context "<planning context>" --decision "<what you chose>" --rationale "<why>" --tags <keyword> --tags <keyword>
```

---

## Planning Interrogation

The Discovery Gate in `/polaris.specify` already gathered intent. Do NOT repeat that interview here.

Read the spec and ask at most 1-2 questions, only for tech choices the spec leaves unresolved (e.g., "framework not specified, use X?"). If the spec is self-contained, or the user said "use defaults" / "just make it simple" / "vanilla HTML", proceed directly to plan generation with no questions.

If you do ask, end with `WAITING_FOR_PLANNING_INPUT`. Do not maintain a question table; do not require an "Engineering Alignment" confirmation step.

## Outline

1. **Detect feature context** (CRITICAL - prevents wrong feature selection):

   Before running any commands, detect which feature you're working on:

   a. **Check git branch name**:
      - Run: `git rev-parse --abbrev-ref HEAD`
      - If branch matches pattern `###-feature-name` or `###-feature-name-WP##`, extract the feature slug (strip `-WP##` suffix if present)
      - Example: Branch `020-my-feature` or `020-my-feature-WP01` → Feature `020-my-feature`

   b. **Check current directory**:
      - Look for `###-feature-name` pattern in the current path
      - Examples:
        - Inside `polaris-specs/020-my-feature/` → Feature `020-my-feature`
        - Not in a worktree during planning (worktrees only used during implement): If detection runs from `.worktrees/020-my-feature-WP01/` → Feature `020-my-feature`

   c. **Prioritize features without plan.md** (if multiple exist):
      - If multiple features exist and none detected from branch/path, list all features in `polaris-specs/`
      - Prefer features that don't have `plan.md` yet (unplanned features)
      - If ambiguous, ask the user which feature to plan

   d. **Extract feature slug**:
      - Feature slug format: `###-feature-name` (e.g., `020-my-feature`)
      - You MUST pass this explicitly to the setup-plan command using `--feature` flag
      - **DO NOT** rely on auto-detection by the CLI (prevents wrong feature selection)

2. **Setup**: Run `polaris agent feature setup-plan --feature <feature-slug> --json` from the repository root and parse JSON for:
   - `result`: "success" or error message
   - `plan_file`: Absolute path to the created plan.md
   - `feature_dir`: Absolute path to the feature directory

   **Example**:
   ```bash
   # If detected feature is 020-my-feature:
   polaris agent feature setup-plan --feature 020-my-feature --json
   ```

   **Error handling**: If the command fails with "Cannot detect feature" or "Multiple features found", verify your feature detection logic in step 1 and ensure you're passing the correct feature slug.

3. **Load context**: Read FEATURE_SPEC and `.polaris/memory/constitution.md` if it exists. If the constitution file is missing, skip Constitution Check and note that it is absent. Load IMPL_PLAN template (already copied).

4. **Execute plan workflow**: Follow the structure in IMPL_PLAN template, using the validated planning answers as ground truth:
   - Update Technical Context with explicit statements from the user or discovery research; mark `[NEEDS CLARIFICATION: …]` only when the user deliberately postpones a decision
   - If a constitution exists, fill Constitution Check section from it and challenge any conflicts directly with the user. If no constitution exists, mark the section as skipped.
   - Evaluate gates (ERROR if violations unjustified or questions remain unanswered)
   - Phase 0: Generate research.md (commission research to resolve every outstanding clarification)
   - Phase 1: Generate data-model.md, contracts/, quickstart.md based on confirmed intent
   - Phase 1: Update agent context by running the agent script
   - Re-evaluate Constitution Check post-design, asking the user to resolve new gaps before proceeding

5. **STOP and report**: This command ends after Phase 1 planning. Report branch, IMPL_PLAN path, and generated artifacts.

   **⚠️ CRITICAL: DO NOT proceed to task generation!** The user must explicitly run `/polaris.tasks` to generate work packages. Your job is COMPLETE after reporting the planning artifacts.

## Phases

### Phase 0: Outline & Research

1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

### Phase 1: Design & Contracts

**Prerequisites:** `research.md` complete

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Agent context update**:
   - Run `{AGENT_SCRIPT}`
   - These scripts detect which AI agent is in use
   - Update the appropriate agent-specific context file
   - Add only new technology from current plan
   - Preserve manual additions between markers

**Output**: data-model.md, /contracts/*, quickstart.md, agent-specific file

## Key rules

- Use absolute paths
- ERROR on gate failures or unresolved clarifications

---

## ⛔ MANDATORY STOP POINT

**This command is COMPLETE after generating planning artifacts.**

After reporting:
- `plan.md` path
- `research.md` path (if generated)
- `data-model.md` path (if generated)
- `contracts/` contents (if generated)
- Agent context file updated

**YOU MUST STOP HERE.**

Do NOT:
- ❌ Generate `tasks.md`
- ❌ Create work package (WP) files
- ❌ Create `tasks/` subdirectories
- ❌ Proceed to implementation

The user will run `/polaris.tasks` when they are ready to generate work packages.

**Next suggested command**: `/polaris.tasks` (user must invoke this explicitly)

---

## On Completion

After the plan is committed and reported to the user:

1. **Check for `--no-continue` flag**: If the user passed `--no-continue` in the arguments, STOP here and report the plan path. Do NOT auto-progress.

2. **Auto-progress to tasks** (default behavior):
   - Print: "Plan complete. Auto-progressing to task generation..."
   - Invoke `/polaris.tasks` automatically
   - If task generation fails, retry once with self-healing (fix the error and retry)
   - If retry also fails, report the error and suggest the user run `/polaris.tasks` manually

3. **Error recovery**:
   - If the plan commit fails, do NOT auto-progress - report the commit error
   - If the tasks command is not available, suggest running `/polaris.tasks` manually


**Telemetry**: Run: `polaris telemetry record plan --feature <slug> --phase complete --agent {{AGENT_NAME}}`
