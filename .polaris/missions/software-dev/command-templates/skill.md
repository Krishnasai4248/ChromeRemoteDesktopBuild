---
description: Apply and integrate a reusable skill into the current project with guided analysis and approval. Everything runs inside Claude - no terminal commands needed.
---
## Model Guidance

This command does implementation work. Use **claude-sonnet-4-6** for this session.

Execution against a defined plan - this is where call volume lives and where savings compound.

---


## User Input

**Telemetry**: Run: `polaris telemetry record skill --feature <slug> --phase start --agent {{AGENT_NAME}}`


```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). Input should be a skill name (e.g., `iam`, `mcp-server`, `studio`, `devops`, `workflow`, `appcentral-shell`).

## Hard Rules

1. **NO POLARIS CLI COMMANDS** -- only the Step 1 bash command below. Use Read/Glob/Grep for everything else.
2. **NO SUBAGENTS for skill analysis** -- all skill analysis done directly with Read, Glob, Grep tools. (Subagents are used in implement context only, not here.)

## Steps

### 1. Discover Skills

The Python package is **`specify_cli`** (NOT `polaris`). Locate its install path without invoking `python` directly - on Windows, `python` and `python3` may resolve to the Microsoft Store stub even when Python is installed, which produces a confusing "not installed" failure.

**1a. Find the install location.** Try in order, stopping at the first one that returns a real path:

```bash
pip show specify_cli 2>&1 | grep -E "^Location:"
```

If pip returns nothing or "not found":

```bash
pipx list --short 2>&1 | grep -E "(^|\s)specify_cli(\s|$)"
```

If both fail with "not found" (not just a missing pip / Store-stub error), STOP and tell the user `specify_cli` is not installed in any reachable Python environment, and suggest `pip install specify_cli` (or the team's private install command).

If pip itself fails with a "Python was not found" / Microsoft Store / exit-code-49 error, the issue is the Windows Python alias, not a missing package. Tell the user to either disable the Microsoft Store Python alias (Settings > Apps > Advanced app settings > App execution aliases) or run pip from the directory of their real Python install. Do NOT conclude that specify_cli is missing.

**1b. Compute the base path.** Parse the `Location:` value from `pip show`. The skills base is `<Location>/specify_cli/skills/builtin`. Store this as `BASE_PATH`.

**1c. Enumerate skills with Glob** (do not list the directory via bash). Pattern: `<BASE_PATH>/*/SKILL.md`. The unique parent directory names are the available skill names.

If no skill name was provided in `$ARGUMENTS`, show the discovered skill names and ask the user which one to apply.

### 2. Analyze Project

Scan with Glob/Grep (parallel where possible, NO bash):

- **Entry points**: `**/main.py`, `**/app.py`, `**/index.ts`, `**/Program.cs`
- **Package manager**: `poetry.lock`, `uv.lock`, `yarn.lock`, `pnpm-lock.yaml`, `pyproject.toml`, `package.json`
- **Env files**: `.env`, `.env.example` -- Read any found
- **Structure**: Check `frontend/`, `client/`, `web/` for `package.json` and `.git` (separate repos?)
- **Active skills**: `.polaris/skills/*.md`
- **Existing skill code** (Grep for skill-specific patterns):
  - `iam`: `Depends\(get_current_user\)|require_auth|JWTBearer|passport\.authenticate`
  - `studio`: `APTEAN_STUDIO|AzureOpenAI|studio_client`
  - `devops`: Glob `.github/workflows/*.yml`, `Dockerfile`
  - `workflow`: `APTEAN_WORKFLOW|workflow_client`
  - `mcp-server`: `FastMCP|McpServer|@mcp\.tool`
  - `appcentral-shell`: `useAppCentralLocale|useAppCentralTheme|APPCENTRAL_LOCALE_CHANGE|APPCENTRAL_THEME_CHANGE|AppCentralShellProvider`
- **Routes**: `@app\.(get|post|put|delete)|@router\.|app\.use\(`
- **Frontend code**: Glob `frontend/src/**/*.{ts,tsx,js}`, `src/**/*.{ts,tsx,jsx}`, `static/**/*.{html,js}`
  - Look for: field access patterns on API responses, auth patterns, API call patterns (fetch/axios)
- **Tests**: Glob `tests/**/*.py` or `**/*.test.ts`, Read 1-2

Determine: framework, package manager, project structure (monolith/separate-folders/separate-repos), frontend root, existing skill code, consumer field expectations, frontend auth gaps.

### 3. Read SKILL.md, Config Questions, Deploy Guardrail

**3a.** Read `<BASE_PATH>/<skill-name>/SKILL.md`. Parse `config:` frontmatter entries (key, type, prompt, default, options).

**3b.** Pre-fill answers from Step 2 analysis (e.g., detected `helm/` -> `DEPLOY_TARGET=helm`, `APTEAN_IAM_*` env vars -> `AUTH_PROVIDER=keycloak`). Tell user what was detected.

**3c.** Ask remaining config questions interactively. **For `iam`: ALWAYS ask identity provider -- never silently default to Entra. Company default is Aptean IAM (Keycloak).** If user presses Enter, use defaults.

**3d.** Read `<BASE_PATH>/<skill-name>/guardrail.md`, replace `{{PROJECT_NAME}}` with project dir name, write to `.polaris/skills/<skill-name>.md`.

### 4. Read Guardrail

Read the deployed guardrail. Its Patterns, Anti-Patterns, Testing Rules, and File Conventions are non-negotiable constraints. Config answers determine which path to follow.

### 5. Cross-Skill Awareness

Read `.polaris/skills/` for active skills. Note interactions (e.g., IAM+Studio share tokens, DevOps CI should test all skills).

### 6. Present Integration Plan -- WAIT FOR APPROVAL

Do NOT modify files until approved. Present: framework, package manager, config, project structure, frontend root, consumer field expectations, existing code found, active skill interactions, files to create, files to modify, frontend changes, auto-actions (install deps, run tests, setup .env).

Wait for: approve all / skip specific files / cancel / questions.

### 7. Execute Integration

Apply config-driven implementation following guardrail patterns:
- Wire imports (match project style, no duplicates)
- Register middleware (correct order, integrate with existing)
- Protect routes per guardrail spec (skip already-protected)
- **Auto-wire consumer fields**: match existing frontend field names (e.g., `user.username` not `preferred_username`)
- Environment variables: append to `.env.example`, copy to `.env` if missing
- Tests: follow project patterns, include positive + negative cases
- Frontend: follow guardrail's Frontend section; inject auth headers, wire UI components; note separate-repo commits

### 8. Install Dependencies

Use detected package manager (`pip`/`poetry add`/`uv add`/`npm`/`yarn`/`pnpm`/`dotnet restore`). Stop on failure.

### 9. Validate and Test

Syntax check modified files, run skill tests, fix failures, verify guardrail compliance (no anti-patterns).

### 10. Summary

Past-tense summary: config used, guardrail deployed, files created/modified, deps installed, test results, brownfield/frontend notes. Only manual step: fill `.env` credentials.

Context: {ARGS}


**Telemetry**: Run: `polaris telemetry record skill --feature <slug> --phase complete --agent {{AGENT_NAME}}`
