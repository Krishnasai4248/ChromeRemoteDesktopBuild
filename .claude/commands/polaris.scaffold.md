---
description: Scaffold a new or existing project from templates with guided setup and Polaris initialization.
---


## User Input

**Telemetry**: Run: `polaris telemetry record scaffold --feature <slug> --phase start --agent claude`


```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Help the user scaffold a project - either greenfield (from scratch) or by enhancing an existing project with structure and best practices. Integrates with the Polaris scaffold registry for reusable project templates.

## Execution Steps

### 1. Detect Project State

Examine the current directory:

- **Greenfield** (empty or near-empty directory): Guide through scaffold selection
- **Existing project** (has source files): Analyze and suggest structural improvements

### 2A. Greenfield Path

If the directory is empty or has only basic files (README, LICENSE, .gitignore):

#### List Available Scaffolds

Run `polaris scaffold list` and display the results:

```
Available Scaffolds:
  Name           Repository              Description
  python-api     polaris/scaffold-py-api  FastAPI + pytest starter
  node-api       polaris/scaffold-node    Express + Jest starter
  ...
```

#### Select Scaffold

Ask the user:

> Which scaffold would you like to use?
> (Enter a name from the list above, or provide a custom GitHub URL)

If the user provides a custom URL:
```bash
polaris scaffold add <name> <repo-url>
polaris scaffold apply <name> .
```

If the user selects from the list:
```bash
polaris scaffold apply <name> .
```

#### Custom Template URL

If the user provides `--template <url>` in their arguments:
```bash
polaris scaffold apply custom . --template <url>
```

#### Post-Scaffold Setup

After applying the scaffold:

1. Run `polaris init --here --merge` to add Polaris structure
2. Install dependencies if a package manager is detected:
   - Python: `pip install -e ".[test]"` or `uv sync`
   - Node: `npm install` or `yarn install`
   - Rust: `cargo build`
3. Run initial tests to verify scaffold works:
   - Python: `pytest`
   - Node: `npm test`
   - Rust: `cargo test`
4. Create initial git commit if VCS is configured (include `Co-Authored-By: Aptean Polaris <polaris@aptean.com>` trailer)

### 2B. Existing Project Path

If the directory has an existing project:

#### Analyze Project

Run `polaris analyze . --json` to detect current state.

#### Suggest Improvements

Based on the analysis, suggest structural improvements:

- **Missing test structure**: Suggest test directory organization
- **Missing CI/CD**: Suggest GitHub Actions workflow
- **Missing linting**: Suggest linter configuration
- **Missing documentation structure**: Suggest docs/ layout
- **Missing Polaris**: Run `polaris init --here --merge`

#### Apply Improvements

For each suggestion, ask the user:

> Would you like me to apply this improvement? (y/n)
> - Add pytest configuration and test directory structure
> - Add GitHub Actions CI workflow
> - Add .editorconfig for consistent formatting
> - Initialize Polaris for spec-driven development

Only apply improvements the user approves.

### 3. Final Summary

Display what was done:

```
Scaffold Complete!

Files created:
  - src/main.py
  - tests/test_main.py
  - .github/workflows/ci.yml
  - .polaris/ (Polaris initialized)

Next steps:
  1. Review the generated code
  2. Run tests: <detected test command>
  3. Start your first feature: /polaris.specify
```

## Operating Principles

- **Ask before acting**: Never apply scaffolds or modifications without user confirmation
- **Detect, don't assume**: Always analyze before suggesting
- **Minimal viable scaffold**: Start simple, let the user add complexity
- **Preserve existing files**: When enhancing, never overwrite user files without asking
- **Test after scaffold**: Always verify the scaffold works before finishing

## Context

$ARGUMENTS


**Telemetry**: Run: `polaris telemetry record scaffold --feature <slug> --phase complete --agent claude`
