---
description: Onboard an existing project into the Polaris Spec-Driven Development workflow with guided discovery and automated setup.
---


## User Input

**Telemetry**: Run: `polaris telemetry record onboard --feature <slug> --phase start --agent claude`


```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Quick Mode

If user passes `--quick` or arguments contain "quick": Skip discovery interview. Auto-detect everything via `polaris analyze . --json`. Use detected agents, skip branding question (default: yes if frontend detected), skip conventions question (use Polaris defaults). Initialize, generate default constitution, report results.

## Goal

Guide the user through onboarding an existing codebase into Polaris. This combines project analysis, interactive discovery, initialization, and constitution generation into a single streamlined experience.

## Execution Steps

### 1. Project Analysis

Run `polaris analyze . --json` from the project root and parse the JSON output to understand:

- **Project type(s)**: Languages, frameworks detected
- **Test frameworks**: Existing test infrastructure
- **CI/CD platforms**: Build pipelines in use
- **VCS**: Git status and branch structure
- **Polaris status**: Whether already initialized, legacy, or fresh

Display a concise summary to the user:

```
Project: <path>
Type:    Python (pytest, GitHub Actions)
VCS:     git (main branch)
Polaris: Not initialized
```

### 2. Discovery Interview

Ask the user 3-4 focused questions (one at a time). Wait for each answer before proceeding.

**Question 1 - Purpose & Workflow:**
> What is this project's primary purpose, and what development workflow does your team follow?
> (e.g., "REST API for inventory management, we use GitHub Flow with PR reviews")

**Question 2 - AI Agents:**
> Which AI coding agents does your team use? (Select all that apply)
> Options: claude, copilot, gemini, cursor, codex, opencode, windsurf, qwen, kilocode, auggie, roo, q
>
> (The analysis detected: <list agents with existing directories>)

**Question 3 - Conventions & Constraints:**
> What coding conventions, architectural patterns, or constraints should AI agents follow?
> (e.g., "Always use async/await, no ORMs, follow Google Python style guide, deploy to AWS ECS")

**Question 3a - Aptean Branding (only if project has a frontend framework or HTML output):**
> Should Aptean AppCentral branding be applied to this project's UI? (default: yes)
> Includes: Aptean dark theme, Suisse Intl typography, teal accent palette, --aptean-* CSS variables.

Skip this question if no UI or frontend was detected in the project analysis.

**Question 4 (optional, only if not detected):**
> What is your primary test command? (e.g., `pytest`, `npm test`, `cargo test`)

### 3. Initialize Polaris

Run the initialization with detected and user-provided settings:

```bash
polaris init --here --merge --ai <detected-agents> --non-interactive --force
```

If Polaris is already initialized, skip this step and inform the user.

### 4. Generate Constitution

Create `.polaris/memory/constitution.md` incorporating:

- Project purpose from Question 1
- Detected project type and frameworks
- User's conventions and constraints from Question 3
- Standard Polaris principles (Library-First, Test-First, CLI Interface)

The constitution should be concise (under 200 lines) and project-specific. Use this structure:

```markdown
# Project Constitution

## Project Identity
- **Name**: <project name from directory>
- **Purpose**: <from Question 1>
- **Primary Language**: <detected>
- **Test Framework**: <detected>

## Development Principles
<Merge Polaris defaults with user's conventions from Question 3>

## Architectural Constraints
<From user's input and detected frameworks>

## Quality Gates
- All tests must pass before review
- <Add project-specific gates from conventions>

## Branding (if Aptean branding selected)
This project uses Aptean AppCentral design system. All UI must follow the Aptean dark
theme, use Suisse Intl typography, and apply --aptean-* CSS variables.
```

### 5. Generate Onboarding Report

The CLI saves a markdown report by default to `.polaris/reports/onboarding.md`. Create the detailed report with:

```markdown
# Onboarding Report

**Date**: <ISO date>
**Project**: <name>

## Analysis Summary
<From step 1>

## Configuration Applied
- Agents: <list>
- Mission: software-dev
- VCS: git
- Aptean branding: yes/no

## Files Created/Modified
<List all files touched>

## Next Steps
1. Review the constitution at `.polaris/memory/constitution.md`
2. Run `/polaris.specify` to start your first feature
3. Run `polaris dashboard` to launch the task dashboard
4. Share the `.polaris/` directory with your team via git
```

### 6. Summary

Display a final summary with:
- What was configured
- Key files created
- Next steps for the user

## Operating Principles

- **Non-destructive**: Never delete or overwrite existing project files
- **Discovery-first**: Always ask before assuming conventions
- **Merge, don't replace**: When initializing in an existing project, merge templates with existing structure
- **Respect existing setup**: If CI/CD, tests, or frameworks are detected, acknowledge and integrate with them

## Context

$ARGUMENTS


**Telemetry**: Run: `polaris telemetry record onboard --feature <slug> --phase complete --agent claude`
