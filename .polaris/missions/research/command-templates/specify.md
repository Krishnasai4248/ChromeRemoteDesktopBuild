---
description: Create or update the research specification from a natural language research question.
---

# /polaris.specify - Create Research Specification

**Version**: 0.11.0+

## 📍 WORKING DIRECTORY: Stay in planning repository

**Telemetry**: Run: `polaris telemetry record specify --feature <slug> --phase start --agent {{AGENT_NAME}}`


**IMPORTANT**: Specify works in the planning repository. NO worktrees are created.

```bash
# Run from project root:
cd /path/to/project/root  # Your planning repository

# All planning artifacts are created in the planning repo and committed:
# - polaris-specs/###-feature/spec.md → Created in planning repo
# - Committed to target branch (meta.json → target_branch)
# - NO worktrees created
```

**Worktrees are created later** during `/polaris.implement`, not during planning.

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Discovery Gate (mandatory)

Before running any scripts or writing to disk you **must** conduct a structured discovery interview.

### Research-Specific Discovery Questions

For research missions, focus on:

1. **Research Question**: What is the primary question you want to answer?
2. **Research Type**: Literature review, empirical study, case study, competitive analysis?
3. **Scope**: What's in scope and out of scope for this research?
4. **Deliverables**: What outputs do you expect? (Report, analysis, recommendations, data)
5. **Audience**: Who will consume this research? (Technical, business, academic)

### Scope Proportionality (CRITICAL)

- **Simple Research** (quick analysis, single-source review): Ask 2-3 questions, then proceed
- **Standard Research** (multi-source analysis, comparative study): Ask 3-5 questions
- **Complex Research** (systematic review, multi-method study): Full discovery with 5+ questions

### Discovery Requirements

1. Maintain a **Discovery Questions** table internally. Do **not** render to user.
2. When you have sufficient context, paraphrase into an **Intent Summary** and confirm.
3. If user explicitly asks to skip questions, acknowledge and proceed with minimal discovery.

## Research Deliverables Location (CRITICAL)

**IMPORTANT**: Research missions have TWO types of artifacts:

| Type | Location | Purpose |
|------|----------|---------|
| **Planning Artifacts** | `polaris-specs/###/research/` | Evidence/sources for PLANNING this sprint |
| **Research Deliverables** | `deliverables_path` | Actual research OUTPUT (your work product) |

### Determining deliverables_path

During discovery, you MUST ask:

> "Where should I store the research outputs (reports, analysis, findings)?
>
> Recommended: `docs/research/<feature-name>/`
>
> Other options:
> - `research-outputs/<feature-name>/`
> - `docs/<feature-name>/`
> - Custom path (must NOT be inside `polaris-specs/`)"

**Default**: If user doesn't specify, use `docs/research/<feature-slug>/`

**Validation Rules**:
- Must NOT be inside `polaris-specs/` (reserved for planning artifacts)
- Must NOT be just `research/` at root (ambiguous)
- Should include feature name/slug for clarity

## Workflow (0.11.0+)

**Planning happens in the planning repository - NO worktree created!**

1. Creates `polaris-specs/###-feature/spec.md` directly in planning repo
2. Creates `polaris-specs/###-feature/meta.json` with `deliverables_path`
3. Automatically commits to target branch
4. No worktree created during specify

**Worktrees created later**: Use `polaris implement WP##` to create a workspace for each work package.

## Location

- Work in: **Planning repository** (not a worktree)
- Creates: `polaris-specs/###-feature/spec.md`
- Commits to: target branch (`meta.json` → `target_branch`)

## Outline

### 0. Generate a Research Title

- Summarize the research question into a short, descriptive title (≤7 words)
- Use the confirmed title to derive the kebab-case feature slug

### 1. Discovery Phase

- Conduct discovery interview (scaled to complexity)
- Determine deliverables_path (ask user or use default)
- Confirm Intent Summary with user

### 2. Create Feature

When discovery is complete, run:

```bash
polaris agent feature create-feature "<slug>" --json
```

Parse the JSON output for `feature` and `feature_dir`.

### 3. Create meta.json with deliverables_path

**CRITICAL**: Include `deliverables_path` in meta.json:

```json
{
  "feature_number": "<number>",
  "slug": "<full-slug>",
  "friendly_name": "<Research Title>",
  "mission": "research",
  "deliverables_path": "<confirmed-path>",
  "source_description": "$ARGUMENTS",
  "created_at": "<ISO timestamp>"
}
```

Example with default path:
```json
{
  "feature_number": "018",
  "slug": "018-market-research",
  "friendly_name": "Market Research Analysis",
  "mission": "research",
  "deliverables_path": "docs/research/018-market-research/",
  "source_description": "Research the competitive landscape",
  "created_at": "2025-01-25T10:00:00Z"
}
```

### 4. Load Research Spec Template

The spec template is bundled with polaris and will be used automatically. The research mission uses a specialized template optimized for research projects.

### 5. Generate Research Specification

Fill in:
- **Research Question**: Primary and sub-questions
- **Methodology**: Approach, data sources, analysis framework
- **Scope**: What's included/excluded
- **Success Criteria**: How we know the research is complete

### 6. Write Specification

Write to `<feature_dir>/spec.md`

### 7. Validation

Validate spec against quality criteria:
- Research question is clear and answerable
- Methodology is appropriate for the question
- Deliverables are defined
- Success criteria are measurable

### 8. Auto-Review & Clarification

After writing and validating the spec, automatically perform a final review pass:

1. Re-read the completed spec end-to-end as a critical reviewer
2. Identify any gaps, ambiguities, or missing acceptance criteria
3. If issues are found, list them as numbered questions and ask the user to address them
4. Update the spec with the user's clarifications
5. Confirm the spec is ready for planning (Phase 2 below)

This replaces the need for a separate `/polaris.clarify` step. The spec should be fully clarified before leaving `/polaris.specify`.

## Phase 2: Research Planning

After the spec is validated and clarified, proceed directly to planning. This eliminates the need for a separate `/polaris.plan` step.

### Planning Interrogation

For research missions, planning interrogation is lighter:
- **Simple projects** (single-source review): 1-2 questions about methodology preferences
- **Complex projects** (multi-method study): 2-3 questions about analysis approach

**Always suggest the best option**: Rather than asking open-ended questions, propose the recommended approach. Example: "I recommend a comparative analysis framework for this study. Sound good?"

Ask one planning question at a time. End with `WAITING_FOR_PLANNING_INPUT` if questions remain.

When you have sufficient context, summarize into an **Engineering Alignment** note and confirm.

### Plan Generation

Once planning interrogation is confirmed:

1. **Setup**: Run `polaris agent feature setup-plan --feature <feature-slug> --json` from the repository root.

2. **Load context**: Read the spec and `.polaris/memory/constitution.md` if it exists.

3. **Phase 0: Research/Gap Analysis**:
   - Extract unknowns from spec
   - For each NEEDS CLARIFICATION -> research task
   - For each dependency -> best practices task
   - Consolidate findings in `research.md`

4. **Phase 1: Design & Contracts**:
   - Generate `data-model.md` with research entities
   - Generate `contracts/` if applicable
   - Generate `quickstart.md` with research workflow
   - Update agent context

5. **Commit planning artifacts** to the target branch.

### 9. Report Completion

Report:
- Feature directory path
- Spec file path
- Plan file path
- Deliverables path (from meta.json)
- Readiness for `/polaris.tasks`

**STOP**: This command ends after generating spec AND plan artifacts. The user should run `/polaris.tasks` next.

## Research-Specific Guidelines

### Focus On

- **WHAT**: The research question and expected outcomes
- **WHY**: The purpose and value of this research
- **SCOPE**: Clear boundaries on what's in/out

### Avoid

- Implementation details (how data will be collected)
- Technology choices (which tools to use)
- Timeline commitments (handled in planning)

### Research Question Quality

Good research questions are:
- **Specific**: Focused on a particular topic
- **Answerable**: Can be investigated with available resources
- **Relevant**: Addresses a real need or gap
- **Bounded**: Has clear scope limits

### Success Criteria for Research

Research success criteria should be:
- **Completion-based**: "All identified sources reviewed"
- **Quality-based**: "Findings validated by domain expert"
- **Outcome-based**: "Recommendations are actionable"

NOT implementation-focused like:
- "Database populated with 1000 records"
- "Analysis script runs without errors"


**Telemetry**: Run: `polaris telemetry record specify --feature <slug> --phase complete --agent {{AGENT_NAME}}`
