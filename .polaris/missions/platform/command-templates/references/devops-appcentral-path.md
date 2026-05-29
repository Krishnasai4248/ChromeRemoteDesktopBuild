# DevOps: Path A AppCentral

Full 35-step execution procedure for AppCentral-deployed applications.

## STEP 0 - Load Skill Files (BLOCKING)

Read both files now before doing anything else:

1. Read `.polaris/skills/devops-pipeline.skill.md`
2. Read `.polaris/skills/helm-runtime.skill.md`

Apply ALL invariants from both files. If either file is missing, HALT with:

```
ERROR: Required skill file missing: <filename>
Run `polaris upgrade` to deploy skill files, then retry /polaris.devops.
```

Do NOT proceed until both files are loaded and all rules are internalized.

---

## ABSOLUTE RULES

These rules apply to every step. No exceptions.

- MUST NOT create `templates/service` in the target repository
- MUST copy ONLY explicitly listed files from the reference repository
- MUST treat the reference repository as READ-ONLY - make no modifications to it
- MUST NOT delete or rename any existing files in the target repository
- MUST NOT copy `scripts/github/environments/` into the target repository
- Commands MUST be shell-correct for the active shell. No Bash-only operators (`&&`, `||`, `$()`) in a PowerShell context

---

## REFERENCE REPOSITORY

`Shared-Technology-Group/next-devops-repository-template`

Clone with:
```
git clone --depth 1 --filter=blob:none https://github.com/Shared-Technology-Group/next-devops-repository-template <temp-dir>
```

MUST NOT reconstruct template content from memory. ALL copied files MUST originate from the cloned repository.

---

## MIGRATION JOB AUTOMATIC DETECTION (DATABASE-AWARE)

The agent MUST automatically detect whether the repository uses a database.
If a database is detected, the migration job MUST be included.
The agent MUST NOT ask the user whether to include migrations.

1. Database Detection (MANDATORY):
   The agent MUST scan the target repository for database usage:
   - Look for ORM configuration files (alembic.ini, manage.py, ormconfig.ts, etc.)
   - Look for migration directories (migrations/, alembic/, db/migrate/, etc.)
   - Inspect dependency files (package.json, requirements.txt, *.csproj) for database libraries (sequelize, typeorm, prisma, sqlalchemy, alembic, django, entity-framework, npgsql, etc.)
   - Check for database connection strings in configuration files
   - Check Dockerfile for database-related setup steps
   - Check config/MainManifest.yml infrastructure.databases section (if exists)

2. If database IS detected:
   - Include the migration job section in helm values file
   - Copy it exactly from the reference template
   - Determine application-specific migration configuration
   - Log: "Database detected - migration job will be included"

3. If NO database is detected:
   - Exclude the entire jobs: section from the values file
   - Keep it as jobs: [] below cronjobs: []
   - Log: "No database detected - migration job excluded"

4. Migration Configuration Detection (when migration job is included):
   a) Working Directory: scan repo for backend code location, check Dockerfile WORKDIR, default to /app
   b) Migration Tool Detection: scan for alembic.ini, manage.py, package.json scripts, migration directories, Dockerfile migration steps
   c) If tool cannot be detected with confidence: ask user "What migration command should be used?"
   d) Validation: verify workingDir exists in Dockerfile structure, verify detected tool is in dependencies

Rules:
- The migration job section MUST be copied from the reference template as-is
- Token replacement and placeholder substitution happen during normal file processing
- workingDir, command, and args MUST be determined based on application structure
- DO NOT use hardcoded values unless application structure matches exactly
- Database detection happens during Step 17 of the execution order
- The agent decides inclusion/exclusion automatically; it does NOT ask the user

---

## EXECUTION ORDER (35 steps - nothing skipped)

**Step 1 - Identify target repository**

Determine the owner and repository name of the target repository (the one being scaffolded, not the reference repo).

**Step 2 - Derive ServiceName, Namespace, ReleaseName, RepoName, OrgName**

Follow `devops-pipeline.skill.md` AUTHORITATIVE SERVICE NAMING CONTRACT rules exactly:

- ServiceName: a SINGLE word (no hyphens, no underscores, no separators), 2-12 characters, alphabetic only. This is the ONE identity used everywhere - file names, helm charts, K8s resources, routing paths, AND `iamDetails.code` (uppercased). It MUST be max 12 chars to fit Azure Key Vault 24-char naming limit: kv-{region}-{lower(iamDetails.code)}-{env}. Derived by concatenating meaningful words from the repository name and abbreviating if needed. Common patterns: customer-management-service=custmgmt, employee-portal-app=employportal, personal-assistant-workspace=persasst, inventory-backend-service=inventback, adr-workspace=adrws. MUST be globally unique across all Aptean products - avoid generic names (assist, service, admin, portal). Before finalizing, verify no collision: `gh search code "iamDetails" --owner Shared-Technology-Group --owner Aptean-Labs`. In MainManifest.yml `iamDetails.code`: ServiceName in ALL UPPERCASE. In all other files: all lowercase. If no meaningful 2-12 character name can be derived, ask the user.
- Namespace: identical to ServiceName. DNS-1123 compliant, max 63 chars.
- ReleaseName: adjective-noun format, deterministic (e.g. brave-eagle).
- RepoName: the target repository name (e.g., my-customer-app). Used in infra workflow files for `{{ .RepoName }}` token replacement.
- OrgName: the GitHub organization name of the target repository (e.g., Shared-Technology-Group, Aptean-Labs). Used in infra workflow files for `{{ .OrgName }}` token replacement.

Show all five derived values to the user and wait for confirmation before proceeding.

CRITICAL: ServiceName is used consistently everywhere. Lowercase in file names, helm, workflows, K8s. Uppercase ONLY in MainManifest.yml `iamDetails.code`. There is NO separate IamCode - it is simply ServiceName.toUpperCase().

**Step 3 - Confirm skill file rules loaded**

State explicitly: "Rules from devops-pipeline.skill.md and helm-runtime.skill.md are loaded and will be enforced throughout execution."

**Step 4 - Check Azure CLI**

Run: `az --version`

- If success: continue (do NOT reinstall)
- If failure: install Azure CLI using the OS-appropriate method

**Step 5 - Check Azure login**

Run: `az account show`

- If success: user is already authenticated, continue (do NOT re-run az login)
- If failure: run `az login` and allow interactive authentication

If login fails or is cancelled: STOP with clear error. Do NOT proceed.

**Step 6 - Clone reference repository**

Clone into a temporary directory:
```
git clone --depth 1 --filter=blob:none https://github.com/Shared-Technology-Group/next-devops-repository-template <temp-dir>
```

**Step 7 - Verify reference repository structure**

Check that ALL of these paths exist in the cloned repository:
- `templates/service/.github/workflows/`
- `templates/service/helm/`
- `templates/service/infrastructure/`
- `templates/service/config/`
- `templates/service/config/MainManifest.example.yml`
- `templates/service/config/manifest-schema.json`
- `templates/service/manage-appConfig-secrets/`
- `templates/service/manage-appConfig-secrets/azureConfig/`
- `templates/service/manage-appConfig-secrets/bgmConfig/`
- `templates/service/scripts/github/environments/`
- `templates/service/scripts/github/environments/set-env-secrets.ps1`
- `templates/service/scripts/github/environments/set-env-vars.ps1`

List all `.yml` files found in `templates/service/.github/workflows/`.

If ANY path is missing: STOP with the exact missing path in the error message.

**Step 8 - Create branch in target repository**

Create branch `feature-<ServiceName>-devops` in the target repository.

---

**--- PRE-SCAN PHASE (BLOCKING) ---**

**Step 8a - Scan target repository and validate Dockerfile(s) (MANDATORY BEFORE FILE CREATION)**

The agent MUST locate and read ALL Dockerfiles in the target repo BEFORE any file creation or copy operations begin. Discovery rules are defined in the DevOps Pipeline Skill (DOCKERFILE DISCOVERY & BUILD CONTEXT RESOLUTION section).

Repositories may have:
- A SINGLE Dockerfile at root level serving ONE service
- A SINGLE Dockerfile at root level serving MULTIPLE services (multi-stage builds)
- MULTIPLE Dockerfiles in different directories (e.g., frontend/Dockerfile, backend/Dockerfile)

The agent MUST discover ALL Dockerfiles, inspect their contents, and determine the scenario before proceeding. If NO Dockerfile is found: STOP with clear error.

The agent MUST validate EACH discovered Dockerfile:

1. Syntax and Structure: valid syntax, valid FROM base images, correct multi-stage references, consistent WORKDIR, no duplicate EXPOSE
2. File and Dependency References: all COPY/ADD source paths exist, dependency files present, entry point scripts exist, .dockerignore not excluding needed files
3. Build Correctness: EXPOSE port matches app port, final stage has CMD/ENTRYPOINT, RUN instructions match present dependency files, correct build context, `COPY --from=<stage>` source paths exist (add `RUN mkdir -p <dir>` if needed)
4. Micro-services Specific: all build targets exist as directories, build args properly defined
5. Multi-Dockerfile Consistency: no overlapping build contexts, clear component mapping

If ANY validation issue would cause a guaranteed build failure: fix before proceeding. This step is BLOCKING.

---

**--- FILE COPY PHASE (BLOCKING) ---**

**Step 9 - Copy whitelisted files only**

Verify each source file exists before copying. Log the full source path. STOP if any source file is missing.

From `<ref-repo>/templates/service/.github/workflows/` to `.github/workflows/`:
- `bgm.{{ .ServiceName }}.lwr.deploy.yml`, `bgm.{{ .ServiceName }}.lwr.swap.yml`
- `bgm.{{ .ServiceName }}.upr.deploy.yml`, `bgm.{{ .ServiceName }}.upr.swap.yml`
- `bgm.helm.lwr.{{ .ServiceName }}.deploy.yml`, `bgm.helm.step.{{ .ServiceName }}.deploy.yml`
- `bgm.helm.upr.{{ .ServiceName }}.deploy.yml`, `bgm.step.template.yml`
- `docker-build-push-{{ .ServiceName }}.yml`, `docker.acr-images.promote-{{ .ServiceName }}.yml`
- `docker.step.build-push-{{ .ServiceName }}.yml`, `helm.{{ .ServiceName }}.deploy.yml`
- `helm.step.{{ .ServiceName }}.deploy.yml`, `helm.upr.{{ .ServiceName }}.deploy.yml`
- `terraform-{{ .ServiceName }}.deploy.yml`, `terraform.step.{{ .ServiceName }}.deploy.yml`
- `infra.{{ .ServiceName }}.deploy.yml`, `infra.step.{{ .ServiceName }}.deploy.yml`

From `<ref-repo>/templates/service/helm/<ServiceName>/` to `helm/<ServiceName>/`:
- `values-{{ .ServiceName }}.yml`

From `<ref-repo>/templates/service/infrastructure/<ServiceName>/` to `infrastructure/<ServiceName>/`:
- `main.tf`, `variables.tf`, `versions.tf`

From `<ref-repo>/templates/service/manage-appConfig-secrets/` to `manage-appConfig-secrets/`:
- `manage-azureConfig.ps1`, `README.md`, `azureConfig/**`, `bgmConfig/**`

Config (generated, not copied):
- `config/MainManifest.yml` (created by agent using example + schema as reference, only if not already present)

After copy, verify: all 18 workflow files exist, all 3 terraform files exist, azureConfig and bgmConfig directories are present, config/MainManifest.yml exists.

---

**--- TOKEN REPLACEMENT AND CONFIGURATION PHASE (BLOCKING) ---**

**Step 10 - Apply token replacement (single pass)**

Follow `devops-pipeline.skill.md` TOKEN REPLACEMENT rules exactly.

Replace in ALL copied files (BOTH `{{ .Token }}` with spaces AND `{{.Token}}` without spaces):
- `{{ .ServiceName }}`, `{{ .Namespace }}`, `{{ .ReleaseName }}`, `{{ .ReleaseNameTwo }}`
- `{{ .RepoName }}`, `{{ .OrgName }}`, `{{ .DeploymentName }}`
- `{{ .ServiceName | replace "-" "_" | upper }}` and `{{ .ServiceName | replace "-" "_" | lower }}` transforms

Use regex `\{\{\s*\.TokenName\s*\}\}` to match both spacing variants.

Helm values placeholder normalization: `{{{ .ServiceName | replace "-" "_" | upper }}_IMAGE_TAG}` -> `#{SERVICE_NAME_IMAGE_TAG}#`

Token replacement is MANDATORY for: all workflow files, all Helm values files, all azureConfig files, all bgmConfig files, `manage-azureConfig.ps1`.

DO NOT modify YAML structure, jobs, steps, comments, ACR placeholders, or PowerShell variables.

After replacement: verify no remaining `{{ .* }}` or `{{.* }}` tokens in any file. If any remain: STOP with file path and line number.

**Step 10a - Generate config/MainManifest.yml (if not already present)**

If file exists: do NOT modify it. If it does NOT exist: read `MainManifest.example.yml` and `manifest-schema.json` from reference repo, scan target repo, CREATE new file with: manifestVersion 1.0, product.name, product.iamDetails.code (ServiceName UPPERCASE, max 12 chars), cloud azure, detected deployments with ports/healthCheck/capacity/configuration, infrastructure (databases - postgres only), empty storage/caching/messaging, routing, dependencies. Validate against schema. If databases/infrastructure unclear: ask user.

**Step 10b - Cross-Organization Repository Access (conditional)**

If target repo is OUTSIDE Shared-Technology-Group: scan all workflow files for references to Shared-Technology-Group repos. For each workflow file that references such repos, add a checkout step using REPO_ACCESS_TOKEN before any step that uses those files. Only add to files that actually need it.

**Step 11 - Inspect Dockerfile**

Use classification and build context from Step 8a.

**Step 12 - Classify service**

Determine: Micro-Frontend or Standard Service. FINAL and AUTHORITATIVE.

**Step 13 - Resolve build targets**

Micro-Frontend: multiple build units (one per app). Standard: single build unit.

**Step 14 - Apply Dockerfile-aware augmentation (additive only)**

Follow `devops-pipeline.skill.md` DOCKERFILE-AWARE AUGMENTATION rules. Micro-Frontend: add additional container repository entries. Standard: extract exposed port, update ONLY port values in Helm values. Inject resolved Dockerfile path into docker workflow files. No deletions. No reformatting.

**Step 15 - Apply Helm runtime configuration**

Follow `helm-runtime.skill.md` HELM RUNTIME CONFIGURATION RULES: exactly ONE `envFrom` block per Helm release, use `nameOverride` by default, no duplicate secrets/AppConfig references.

**Step 16 - Configure ingress paths**

Follow `helm-runtime.skill.md` INGRESS PATH STRUCTURE RULES: backend=`/<ServiceName>/api`, frontend=`/<ServiceName>/<frontend-segment>`, Micro-Frontend=discover all paths from Dockerfile.

**Step 17 - Detect database usage and determine migration inclusion (AUTOMATIC)**

Scan for database usage (see MIGRATION JOB AUTOMATIC DETECTION above). MUST NOT ask user.

If database IS detected: determine migration config, IMMEDIATELY add Helm hook annotations to azureConfig and bgmConfig files. If annotations NOT found after processing: ADD them immediately.

If NO database: note to exclude migration job, keep azureConfig annotations as `annotations: {}`.

Store detection result for Step 28.

**Step 18 - Generate two BGM release names**

Per `devops-pipeline.skill.md` BGM CONFIGURATION RELEASE NAMES rules: Primary ReleaseName (e.g. `brave-eagle`), Secondary ReleaseNameTwo (e.g. `swift-falcon`). Both deterministic, both different. Apply to bgmConfig: setName `one` uses ReleaseName, setName `two` uses ReleaseNameTwo.

**Step 19 - Update azureConfig values**

Inspect target repo for environment variables and known config keys. Add missing keys to appconfig and keyvault files. NEVER remove or rename existing keys. Additive only.

**Step 20 - Micro-Frontend conditional build logic (if applicable)**

Only if Micro-Frontend. Read `.polaris/skills/devops-microfrontend.skill.md` first, then follow its rules: add path-based `detect-changes` job, per-app conditional build jobs, update promote/build-push/helm-step workflows, update Helm values with separate deployments/services/ingress for EACH container, update ALL BGM workflow files.

---

**--- ENVIRONMENT SETUP PHASE (BLOCKING, SEQUENTIAL) ---**

FORBIDDEN during this phase: `Start-Sleep`, polling loops, repeated environment listing, status checks between scripts.

**Step 21 - Verify all files are saved**

Confirm all generated and modified files are written to disk.

**Step 22 - Verify environment scripts exist**

Check both scripts exist in reference repo: `set-env-secrets.ps1` and `set-env-vars.ps1`. STOP with exact expected path if missing.

**Step 23 - CREATE ENVIRONMENTS AND SECRETS**

CRITICAL: Before executing set-env-secrets.ps1, verify the script uses stdin piping (`$value | gh secret set $name -e $env`) NOT the `-b"$value"` flag. Fix if needed.

Execute with FULL ABSOLUTE PATH: `<ref-repo>/templates/service/scripts/github/environments/set-env-secrets.ps1 -env all`

Wait for COMPLETE execution. Do NOT proceed until finished. Do NOT add sleep.

Log each environment and secret created. If script fails: STOP.

**Step 24 - CREATE VARIABLES**

IMMEDIATELY after Step 23, with NO delay.

Execute: `<ref-repo>/templates/service/scripts/github/environments/set-env-vars.ps1 -env all`

Do NOT add `Start-Sleep`. Do NOT poll. If script fails: STOP.

**Step 25 - VERIFY SECRETS AND VARIABLES (single check only)**

List environments ONCE. For EACH environment: verify secrets exist (single check), verify variables exist (single check). If missing: retry creation ONCE. If still missing: STOP.

**Step 26 - ADD REQUIRED REVIEWERS**

Follow `devops-pipeline.skill.md` ENVIRONMENT REQUIRED REVIEWERS rules.

1. Get authenticated username: `gh api user --jq .login`
2. Get numeric user ID: `gh api "users/{username}" --jq .id`
3. Add svc-GitHub_aptean as collaborator with admin access (MANDATORY). If fails: retry once with write permission. If all fail: log WARNING, continue.
4. Get svc-GitHub_aptean numeric ID. If fails: log WARNING.

For EACH environment EXCEPT `devops-build`, `dev`, `tst`:

If svc-GitHub_aptean available, add BOTH reviewers (authenticated user + svc-GitHub_aptean).
If not available, add authenticated user only.

- `type` MUST be `"User"`, `id` MUST be numeric. No sleep between assignments.
- Verify reviewers were added. Retry ONCE if failed. If retry fails: log WARNING, continue.

**Step 27 - FINAL REVIEWER VERIFICATION**

Check each environment (except `devops-build`, `dev`, `tst`) ONCE. Log missing ones for manual addition. Do NOT retry repeatedly.

---

**--- POST-PROCESSING (BLOCKING) ---**

**Step 28 - Apply migration job decision to Helm values**

Using decision from Step 17: YES=include migration job section with detected config; NO=exclude `jobs:` section, keep as `jobs: []`.

**Step 29 - FAST MODE RECONCILIATION (single pass, non-recursive)**

Scope: only whitelisted files, Dockerfile, Helm values, workflow files.

Validate:
- Dockerfile classification consistency across all generated files
- No remaining `{{ .* }}` or `{{.* }}` tokens, no malformed GitHub expressions, no escaped Helm placeholders
- No `TO_BE_CONFIGURED` placeholders remain
- GitHub Actions version consistency: `actions/checkout@v4`, `Azure/login@v2.1.1`, `docker/setup-buildx-action@v3`, `azure/CLI@v2`
- Environment name casing: all lowercase (e.g., `uat-a` not `uat-A`)
- Variable names: `vars.CLUSTER_RG_NAME` (not `vars.RG_CLUSTER`)
- Secrets handling: prefer `secrets: inherit` over explicit listing
- Helm invariants: exactly one release, exactly one `envFrom`, no multi-container for micro-frontends

If violation found: fix ONCE. Do NOT restart reconciliation.

**Step 30 - Verify all required files exist**

Verify all files required for the classified service type are present.

**Step 31 - Micro-Frontend multi-container verification (if applicable)**

Verify: promote workflow has steps for ALL images, build workflow has jobs for ALL images, `helm.step` has `--set` commands for ALL images, Helm values has deployments/services/ingress for ALL images, BGM workflows handle ALL images.

**Step 32 - Enforce final newline rules**

Ensure all generated files end with a single newline character.

---

**--- FINALIZATION ---**

**Step 33 - Display comprehensive final summary report**

```
FILES CREATED:
  .github/workflows/ - list each .yml with purpose (BGM/Docker/Helm/Terraform)
  helm/<ServiceName>/values-<ServiceName>.yml
  infrastructure/<ServiceName>/main.tf, variables.tf, versions.tf
  manage-appConfig-secrets/azureConfig/*, bgmConfig/*
  config/MainManifest.yml

REQUIRED REVIEWERS:
  <env-name>: Added / Missing
  (for envs except devops-build, dev, tst)

NEXT STEP:
  Run /polaris.deploy to merge the PR and trigger all pipelines automatically.

DOCUMENTATION: See manage-appConfig-secrets/README.md

WARNINGS/MANUAL ACTIONS: (list any issues)
```

**Step 34 - Commit all changes**

Commit all created and modified files to `feature-<ServiceName>-devops` branch.

**Step 35 - Open PR to main branch**

Open a pull request from `feature-<ServiceName>-devops` to the default branch.

---

## FAILURE HANDLING

On any violation: DO NOT partially apply changes. DO NOT open a PR. Exit with a clear error message.

**Exception**: Reviewer assignment failure MUST NOT fail the agent. Log and continue.

---

## CONTEXTUAL UPDATE MODE (POST-SCAFFOLDING CHANGES)

When user requests changes after initial scaffolding (e.g., "add migrations", "fix helm values"), follow the Contextual Update Skill (`.polaris/skills/contextual-update.skill.md`). The agent MUST NOT re-run the entire scaffolding process.
