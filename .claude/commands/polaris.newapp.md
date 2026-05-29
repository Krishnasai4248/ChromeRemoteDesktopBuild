---
description: Scaffold a new application from organization monorepo template with guided setup.
---


## User Input

**Telemetry**: Run: `polaris telemetry record newapp --feature <slug> --phase start --agent claude`


```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Quick Mode

If user passes `--quick` or arguments contain "quick": Skip discovery questions EXCEPT the Security & Compliance block (Step 1B) - those answers are non-negotiable. Use Aptean defaults: fullstack app, Aptean branding yes, AKS deployment. Require only project name (from arguments or ask once) and the four security answers, then scaffold.

## Goal

Scaffold a new application following the organization monorepo template. ALL version floors are sourced from `src/specify_cli/scaffolds/version_pins.yaml` - read the manifest at scaffold time and use whatever it says. The Aptean standard tech stack today is **Django 5.1+ on Python 3.12+ backend, Vite / Next 16+ / React 19+ frontend on Node 22+ LTS, PostgreSQL 17+** (these values match the manifest as of 2026-05-07; do not hard-code them in the scaffold output, always read from the manifest). Supports frontend, backend, worker, MCP server, and full-stack application types. Every scaffolded app includes audit-log infrastructure, a security folder layout, and a seeded threat-model placeholder; no app ships without these.

## Execution Steps

### 1. Discovery

Ask the user about their project requirements:

- **Application type**: frontend, backend, worker, mcp, or fullstack
- **Project name**: kebab-case identifier (e.g., `my-new-service`)
- **Description**: Brief one-liner for README and package metadata
- **Aptean branding**: Should AppCentral design system be applied? (default: yes)
  - Yes: Aptean dark theme, Suisse Intl typography, teal accent, `--aptean-*` CSS variables
  - No: neutral default theme
- **Deployment target**:
  - Kubernetes (AKS) for AppCentral (default) - Helm charts, AKS manifests, ACR registry
  - Standalone / feature app - Docker Compose only, no K8s

The default stack reads from `src/specify_cli/scaffolds/version_pins.yaml` - **Django 5.1+ / 6+ on Python 3.12+ backend, Vite / Next 16+ / React 19+ frontend on Node 22 LTS, PostgreSQL 17+**. Do NOT ask the user to choose a language or framework - these are the Aptean standard. If the user explicitly requests a different stack in their arguments, honor it but note it deviates from the Aptean standard. Never recommend Node 18 or 20, Next 14 or 15, React 18, Python 3.10 or 3.11, Java 11 or 17, .NET 6 or 7, PostgreSQL below 17, or any framework version below the manifest floor.

If the user provided arguments, extract answers from there first.

### 1B. Security & Compliance Discovery (MANDATORY - never skipped)

Before any files are written, capture the four security baseline answers. These are non-negotiable; even in `--quick` mode they must be answered. If the user has already run `/polaris.constitution`, inherit the answers from `.polaris/memory/constitution.md` (Phase 2) and confirm; otherwise ask:

- **S1 Data tier**: What is the most sensitive data tier the application will store or process? (Public | Internal | Confidential | Restricted - PII/PHI/payment/secrets). The answer drives database encryption defaults, log redaction rules, and the threat-model template.
- **S2 Audit log policy**: Which event classes MUST be logged to an append-only audit trail, and for how long?
  - Default minimum (always enforced): authentication outcomes, authorization denials, all writes/deletes against Confidential or Restricted data, configuration changes, admin actions.
  - Default retention: 1 year. Confirm or override.
- **S3 AuthN / AuthZ model**: How do callers authenticate (none, API key, OIDC/OAuth2, SSO, mTLS), and how is authorization decided (RBAC, ABAC, ownership-based)? Default-deny is required - the scaffold seeds a deny-by-default policy point that the user wires up.
- **S4 Threat surface**: Where does untrusted input enter (public HTTP, webhook, file upload, queue, scheduled job consuming external data, third-party API)? Multi-tenant?

Persist these into `.polaris/memory/constitution.md` (Phase 2 - Security & Audit Baseline) at the end of scaffolding. They also seed the `security/threat-model.md` placeholder created in Step 4c.

### 2. Scaffold from Template

**Online mode** (preferred): Clone the organization template repository:

```bash
git clone --depth 1 https://github.com/Shared-Technology-Group/workspaces-sdd-repo-template.git <project-name>
cd <project-name>
python -c "import shutil; shutil.rmtree('.git')"
git init --initial-branch main
```

**Offline mode** (fallback): Generate the standard monorepo structure (every directory below is required - do not omit `audit-trail/`, `security/`, or `docs/security/` even for prototype apps):

```
<project-name>/
  src/
    <app-type>/
  tests/
  docs/
    security/
      threat-model.md            # seeded from Step 1B answers
      data-classification.md     # records the S1 answer + per-entity tier
  audit-trail/                   # append-only JSONL audit logs (logs themselves gitignored)
    .gitignore                   # ignores *.jsonl and *.gz; itself tracked, keeps the dir in git
    README.md                    # explains retention, sink, schema, and PII handling
  security/
    authz-policy.md              # default-deny rules (S3 answer)
    secrets.md                   # how secrets are sourced (env, vault, KMS)
  .github/
    workflows/
      ci.yml
  docker-compose.yml
  Dockerfile
  README.md
  VERSION
  CHANGELOG.md
  .gitignore                     # must include audit-trail/*.jsonl
```

### 3. Configure for Default Stack

Set up the Aptean standard stack. Read floors from `src/specify_cli/scaffolds/version_pins.yaml`:

- **Backend**: `pyproject.toml` (Django >= floor, Python >= floor), `manage.py`, Django settings module, virtual environment setup. `requires-python` matches the manifest's `runtimes.python.min`.
- **Frontend**: `package.json` with `"engines": {"node": ">=22"}`, `tsconfig.json`, Vite or Next.js 16+ config with React 19+. Pin Node base image tag from `container_base_images.node` (`node:22-alpine`).
- **Database**: PostgreSQL 17+ connection in Django settings, initial migration. Compose service uses the `container_base_images.postgres` tag.
- **Docker**: multi-stage `Dockerfile`, `docker-compose.yml` with PostgreSQL service. Base image tags MUST come from the manifest - never hard-code `node:20`, `python:3.10`, `postgres:14`, etc.

If the user explicitly requested a non-default stack, use the appropriate language patterns instead (Python: pyproject.toml; TypeScript/JS: package.json, tsconfig.json; Go: go.mod; Rust: Cargo.toml; C#: .csproj; Java: pom.xml or build.gradle). The version floor for any non-default stack still comes from `version_pins.yaml`.

### 4. Initialize Polaris

```bash
polaris init --here --merge
```

### 4a. Apply Aptean Branding (if selected)

If the user selected Aptean branding (default: yes):

- Copy Suisse Intl fonts to `static/fonts/` (backend) or `public/fonts/` (frontend)
- Generate base CSS with `--aptean-*` design tokens (dark theme, teal accent `#54B3BE`, Suisse Intl typography)
- Apply dark-theme-first color system
- Add Aptean logo SVG to static assets
- Reference `aptean-style/SKILL.md` for the full token set

### 4b. Seed Audit & Security Scaffolding (mandatory)

Write the following content to the directories created in Step 2 - never empty placeholders, the user should be able to read them and understand the intent without further guidance:

- `audit-trail/README.md`: documents retention (defaults to 1 year, override per S2), sink (filesystem / Splunk / Sentinel / S3+Object-Lock), event schema (actor, action, target, ts ISO-8601 UTC, outcome, correlation id), and the gitignore line that excludes the `.jsonl` files but tracks the README. Reference the constitution's Phase 2 baseline.
- `audit-trail/.gitignore`: contains `*.jsonl` and `*.gz` so logs never land in the repo while the directory itself stays tracked.
- `security/authz-policy.md`: states the default-deny rule, names the policy enforcement point, and shows a worked example matching the S3 answer (e.g., "Express middleware checking JWT role" or "Django `permission_classes` requiring an explicit allow rule").
- `security/secrets.md`: documents how secrets enter the app (env, mounted file, KMS, Key Vault) and explicitly forbids committing `.env*` to the repo.
- `docs/security/threat-model.md`: seeded with the four S1-S4 answers, an OWASP Top 10 checklist, and a "trust boundaries" diagram placeholder. Marked DRAFT so it gets updated as the app evolves.
- `docs/security/data-classification.md`: records the S1 answer and provides a small table where each persisted entity is classified.
- A baseline audit-log middleware/decorator stub appropriate to the stack (Django: a small `audit_log_middleware.py`; Express: a `requestAudit.ts` Pino transform; Next.js: a `lib/audit.ts` helper). The stub writes one event per state-changing request and points at `audit-trail/<feature>.jsonl` by default.

### 4c. Configure Deployment Target

**Kubernetes (AKS) for AppCentral** (default):

- Create `helm/` directory with:
  - `Chart.yaml`, `values.yaml`, `values-staging.yaml`, `values-production.yaml`
  - Templates: `deployment.yaml`, `service.yaml`, `ingress.yaml`, `hpa.yaml`
  - Health probes (liveness, readiness, startup)
- Create `.github/workflows/deploy.yml` for AKS deployment
- Default container registry: Azure Container Registry (ACR)

**Standalone / feature app**:

- Create `docker-compose.yml` only (no Helm or K8s manifests)
- Create `.github/workflows/ci.yml` for test + build
- No Kubernetes resources

### 5. Post-Scaffold Validation

1. Install dependencies using detected package manager
2. Run initial test suite to verify scaffold works
3. Run a structural check: every directory listed in Step 2 must exist; `audit-trail/.gitignore` must contain `*.jsonl`; `docs/security/threat-model.md` must reference the S1-S4 answers (not be a literal template).
4. Create initial git commit. Do NOT add `Co-Authored-By` trailers - the project's `commit-msg` hook appends `Co-Authored-By: Aptean Polaris <polaris@aptean.com>` automatically.

### 6. Summary

Display what was created and suggest next steps:

```
Application scaffolded!

  Type:       <app-type>
  Stack:      <Django/Vite/Next>+<React>+PostgreSQL (versions read from version_pins.yaml)
  Branding:   Aptean AppCentral (yes/no)
  Deployment: AKS for AppCentral / Standalone
  Security:   data tier=<S1>, audit retention=<S2>, authn=<S3>, surfaces=<S4>
  Location:   <project-name>/

Next steps:
  1. cd <project-name>
  2. Review generated structure (especially docs/security/threat-model.md)
  3. /polaris.specify to define your first feature - the spec template now
     includes a mandatory Audit & Security section that inherits these answers
```

## Operating Principles

- **Ask before acting**: Confirm choices before generating files
- **Detect connectivity**: Try online template first, fall back to offline patterns
- **CalVer versioning**: Initialize VERSION file with CalVer format (YYYY.MM.PATCH)
- **Never overwrite**: If target directory has existing files, warn and confirm

## Context

$ARGUMENTS


**Telemetry**: Run: `polaris telemetry record newapp --feature <slug> --phase complete --agent claude`
