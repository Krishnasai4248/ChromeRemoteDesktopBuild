---
description: Set up a new Aptean application or onboard an existing project.
---

## Model Guidance

This command does planning work. Use **claude-opus-4-6** for this session.

Deep reasoning, synthesis, and decision-making here propagate to all downstream work. Opus-level reasoning is insurance, not indulgence.

If you are currently on Sonnet: switch to Opus before proceeding (`/model claude-opus-4-6`).

---


# /polaris.setup - Project Setup

**Version**: 2026.3.0+
**Purpose**: Composite command that detects context (new vs existing project) and chains the appropriate setup commands with Aptean defaults.

## User Input

**Telemetry**: Run: `polaris telemetry record setup --feature <slug> --phase start --agent claude`


```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Workflow

### Step 1: Detect Context

Determine whether this is a new project or an existing codebase:

- **New project indicators**: Empty directory, no `package.json`/`pyproject.toml`/`Cargo.toml`, user says "new app" or "create"
- **Existing project indicators**: Source files present, build configs exist, user says "onboard" or "existing"

If ambiguous, ask the user:
> "Is this a new application or an existing project you want to onboard into Polaris?"

### Step 2: Execute Setup

**For new projects** - Run `/polaris.newapp` with Aptean defaults:
- Django 6+ backend with REST framework
- Vite + React 19+ frontend
- PostgreSQL 17+ database
- AKS deployment target with Helm charts and ACR registry
- Aptean branding: Suisse Intl typography, `--aptean-*` CSS variables, teal #54B3BE accent
- Health probes and CI/CD pipeline scaffolding

The user can override any of these defaults during the newapp discovery process.

**For existing projects** - Run `/polaris.onboard` with guided discovery:
- Detect existing tech stack and project structure
- Ask about Aptean branding adoption (fonts, CSS variables, theme)
- Set up Polaris workflow (polaris-specs/, .polaris/, agent directories)

### Step 3: Establish Principles

Run `/polaris.constitution` to create or update project governing principles:
- Coding standards and conventions
- Architecture decisions
- Team workflow preferences
- Quality gates and review requirements

### Step 4: Summary

Display a summary of what was set up:
- Project type (new/onboarded)
- Tech stack configured
- Aptean branding status
- Constitution highlights
- Next steps: `/polaris.specify` to define and plan a feature, or `/polaris.autopilot` for full pipeline

## Cross-Platform Notes

All commands used here are Polaris CLI commands that work on Windows, macOS, and Linux. No shell-specific commands are used.


**Telemetry**: Run: `polaris telemetry record setup --feature <slug> --phase complete --agent claude`
