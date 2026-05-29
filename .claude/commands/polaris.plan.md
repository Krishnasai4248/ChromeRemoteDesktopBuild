---
description: Execute the implementation planning workflow using the plan template to generate design artifacts.
---


## Model Guidance

This command does planning work. Use **claude-opus-4-6** for this session.

Architecture decisions and technical plans made here define implementation scope for every WP that follows. If you are on Sonnet: switch to Opus (`/model claude-opus-4-6`).

---

## User Input

```text

**Telemetry**: Run: `polaris telemetry record plan --feature <slug> --phase start --agent claude`

$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Branch Pre-flight
Run `git branch --show-current`. Planning does not use worktrees - if pwd contains `.worktrees/`, STOP and switch back to the main repo first.

## Location Check (0.11.0+)

This command runs in the **main repo**, not in a worktree. NO worktrees are created during planning.

- Verify you are on the target branch before scaffolding plan.md
- Planning artifacts live in `polaris-specs/###-feature/`
- The plan is committed to the target branch after generation

**Path reference rule:** Provide either absolute paths or paths relative to the project root (e.g., `polaris-specs/<feature>/tasks/`). Never refer to a folder by name alone.

## Decision Memory (only if memory file exists)

Skip this section entirely if `.polaris/memory/decisions-summary.md` does not exist (greenfield projects).

If the file exists, read it once and reuse settled architectural decisions (tech stack, patterns, storage choices) unless the spec explicitly requires something different. When you make a new key design decision during planning, record it:
```bash
polaris memory record-decision --context "<planning context>" --decision "<what you chose>" --rationale "<why>" --tags <keyword> --tags <keyword>
```

---

## Planning Interrogation

The Discovery Gate in `/polaris.specify` already gathered intent. Do NOT repeat that interview here.

Read the spec and ask at most 1-2 questions, only for tech choices the spec leaves unresolved (e.g., "framework not specified, use X?"). If the spec is self-contained, or the user said "use defaults" / "just make it simple", proceed directly to plan generation with no questions.

If you do ask, end with `WAITING_FOR_PLANNING_INPUT`. Do not maintain a question table; do not require an "Engineering Alignment" confirmation step.

## Outline

1. **Setup**: Run `polaris agent feature setup-plan -Json` from repo root and parse JSON for FEATURE_SPEC, IMPL_PLAN, SPECS_DIR.

2. **Load context**: Read FEATURE_SPEC and `.polaris/memory/constitution.md` if it exists.

3. **Execute plan workflow**: Follow the structure in IMPL_PLAN template:
   - Phase 0: Generate research.md
   - Phase 1: Generate data-model.md, contracts/, quickstart.md

4. **STOP and report**: Report plan.md path, generated artifacts, and suggest `/polaris.tasks`.

## Key rules

- Use absolute paths
- ERROR on gate failures or unresolved clarifications
- Planning happens in main repo - NO worktrees created
- Commit plan artifacts to polaris-specs/###-feature/


**Telemetry**: Run: `polaris telemetry record plan --feature <slug> --phase complete --agent claude`
