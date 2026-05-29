---
description: Set up CI/CD pipelines, Docker, Helm charts, and deployment configuration.
---

## User Input

**Telemetry**: Run: `polaris telemetry record devops --feature <slug> --phase start --agent {{AGENT_NAME}}`


```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

---

## Route Detection

Before any other action, ask the user:

> "Is this application deployed through AppCentral? (Yes / No)"

- **Yes** -> follow Path A: AppCentral below
- **No** -> follow Path B: Generic below

---

## Path A: AppCentral

Load @references/devops-appcentral-path.md for the complete AppCentral scaffolding procedure (skill loading, absolute rules, reference repository, migration detection, all 35 execution steps, failure handling, and contextual update mode).

### ABSOLUTE RULES (summary)

These rules apply to every step in Path A. No exceptions.

- MUST NOT create `templates/service` in the target repository
- MUST copy ONLY explicitly listed files from the reference repository
- MUST treat the reference repository as READ-ONLY - make no modifications to it
- MUST NOT delete or rename any existing files in the target repository
- MUST NOT copy `scripts/github/environments/` into the target repository
- Commands MUST be shell-correct for the active shell. No Bash-only operators (`&&`, `||`, `$()`) in a PowerShell context

---

### REFERENCE REPOSITORY

`Shared-Technology-Group/next-devops-repository-template`

Clone with:
```
git clone --depth 1 --filter=blob:none https://github.com/Shared-Technology-Group/next-devops-repository-template <temp-dir>
```

MUST NOT reconstruct template content from memory. ALL copied files MUST originate from the cloned repository.

---

### MIGRATION JOB AUTOMATIC DETECTION (DATABASE-AWARE)

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

### EXECUTION ORDER (35 steps - nothing skipped)

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

**Step 4 - Verify GitHub authentication**

Run: `gh auth status`

- If success: continue.
- If failure: STOP with "GitHub CLI not authenticated. Run `gh auth login` first."

The agent does NOT check for or use Azure CLI. All Azure work for this
flow is performed by the central Polaris Bootstrap workflow at
`Aptean-Labs/polaris-devops`. The developer never needs `az login` or
any personal Azure access.

**Step 5 - (reserved)**

This step is intentionally a no-op. It used to verify Azure login.
That responsibility moved to the Polaris Bootstrap workflow.

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
- A SINGLE Dockerfile at root level serving ONE service (e.g., just backend or just frontend)
- A SINGLE Dockerfile at root level serving MULTIPLE services (e.g., multi-stage builds producing both frontend and backend images, or build args selecting which app to build)
- MULTIPLE Dockerfiles in different directories (e.g., frontend/Dockerfile, backend/Dockerfile) - each serving a different component

The agent MUST discover ALL Dockerfiles, inspect their contents, and determine the scenario (single-service, multi-service single Dockerfile, or multi-Dockerfile) before proceeding. If NO Dockerfile is found: STOP with clear error.

PURPOSE: Validate that ALL Dockerfiles are correct and will build successfully when pipelines are triggered. Catch errors BEFORE creating CI/CD files.

The agent MUST validate EACH discovered Dockerfile:

1. Syntax and Structure:
   - Dockerfile has valid syntax (no malformed instructions)
   - All FROM instructions reference valid base images
   - Multi-stage builds have correct stage references (COPY --from= targets exist)
   - WORKDIR paths are consistent across instructions
   - No duplicate or conflicting EXPOSE statements

2. File and Dependency References:
   - All COPY and ADD source paths reference files/directories that ACTUALLY EXIST in the repository (relative to that Dockerfile's build context)
   - package.json, requirements.txt, *.csproj, or equivalent dependency files referenced in COPY instructions are present
   - Entry point scripts referenced in CMD or ENTRYPOINT exist
   - .dockerignore is not excluding files needed by the build

3. Build Correctness:
   - EXPOSE port matches the application's configured port
   - If multi-stage: final stage has a valid CMD or ENTRYPOINT
   - RUN instructions that install dependencies match the dependency files present (e.g., npm install after copying package.json)
   - Build context is correctly set (Dockerfile location relative to files it copies)
   - For every `COPY --from=<stage>` instruction, verify the source path EXISTS in that build stage. If the source directory may not be created by the build (e.g., `COPY --from=builder /app/public ./public` but `public/` is not guaranteed to exist), add `RUN mkdir -p <dir>` before the build step or use a fallback pattern. This is common with Next.js standalone builds where `public/` may be empty.

4. Micro-services Specific (if applicable):
   - All application build targets referenced in the Dockerfile exist as directories in the repository
   - Build arguments used for selecting apps are properly defined

5. Multi-Dockerfile Consistency (when multiple Dockerfiles are found):
   - Each Dockerfile's build context does not overlap with another's in ways that would cause conflicts
   - Component mapping is clear (which Dockerfile serves which deployment)
   - If purpose of any Dockerfile cannot be determined: ask the user

If ANY validation issue is found:
- Log the specific issue with file path and line number
- Fix it first
- If the issue would cause a guaranteed build failure: Fix the Dockerfile before proceeding to file creation

This step is BLOCKING. No file operations may begin before it completes.

---

**--- FILE COPY PHASE (BLOCKING) ---**

**Step 9 - Copy whitelisted files only**

Verify each source file exists before copying. Log the full source path for each file. STOP if any source file is missing.

From `<ref-repo>/templates/service/.github/workflows/` to `.github/workflows/` in target:
- `bgm.{{ .ServiceName }}.lwr.deploy.yml`
- `bgm.{{ .ServiceName }}.lwr.swap.yml`
- `bgm.{{ .ServiceName }}.upr.deploy.yml`
- `bgm.{{ .ServiceName }}.upr.swap.yml`
- `bgm.helm.lwr.{{ .ServiceName }}.deploy.yml`
- `bgm.helm.step.{{ .ServiceName }}.deploy.yml`
- `bgm.helm.upr.{{ .ServiceName }}.deploy.yml`
- `bgm.step.template.yml`
- `docker-build-push-{{ .ServiceName }}.yml`
- `docker.acr-images.promote-{{ .ServiceName }}.yml`
- `docker.step.build-push-{{ .ServiceName }}.yml`
- `helm.{{ .ServiceName }}.deploy.yml`
- `helm.step.{{ .ServiceName }}.deploy.yml`
- `helm.upr.{{ .ServiceName }}.deploy.yml`
- `terraform-{{ .ServiceName }}.deploy.yml`
- `terraform.step.{{ .ServiceName }}.deploy.yml`
- `infra.{{ .ServiceName }}.deploy.yml`
- `infra.step.{{ .ServiceName }}.deploy.yml`

From `<ref-repo>/templates/service/helm/<ServiceName>/` to `helm/<ServiceName>/`:
- `values-{{ .ServiceName }}.yml`

From `<ref-repo>/templates/service/infrastructure/<ServiceName>/` to `infrastructure/<ServiceName>/`:
- `main.tf`
- `variables.tf`
- `versions.tf`

From `<ref-repo>/templates/service/manage-appConfig-secrets/` to `manage-appConfig-secrets/`:
- `manage-azureConfig.ps1`
- `README.md`
- `azureConfig/**` (entire directory)
- `bgmConfig/**` (entire directory)

Config (generated, not copied):
- `config/MainManifest.yml` (created by agent using example + schema as reference, only if not already present)

After copy, verify: all 18 workflow files exist, all 3 terraform files exist, azureConfig and bgmConfig directories are present, config/MainManifest.yml exists (pre-existing or newly generated).

---

**--- TOKEN REPLACEMENT AND CONFIGURATION PHASE (BLOCKING) ---**

**Step 10 - Apply token replacement (single pass)**

Follow `devops-pipeline.skill.md` TOKEN REPLACEMENT rules exactly.

Replace in ALL copied files (BOTH `{{ .Token }}` with spaces AND `{{.Token}}` without spaces):
- `{{ .ServiceName }}` / `{{.ServiceName}}` with derived ServiceName
- `{{ .Namespace }}` / `{{.Namespace}}` with derived Namespace
- `{{ .ReleaseName }}` / `{{.ReleaseName}}` with generated ReleaseName
- `{{ .ReleaseNameTwo }}` / `{{.ReleaseNameTwo}}` with secondary ReleaseName (BGM only)
- `{{ .RepoName }}` / `{{.RepoName}}` with the target repository name (used in infra workflow files)
- `{{ .OrgName }}` / `{{.OrgName}}` with the GitHub organization name of the target repo (used in infra workflow files)
- `{{ .DeploymentName }}` / `{{.DeploymentName}}` with the deployment name from `config/MainManifest.yml` `deployments[].name` (e.g., "api"). For migration jobs and envFrom references, this is the backend/api deployment name. Read the manifest (or use the scanning result from Step 10a if manifest is being generated) to determine the correct deployment name.
- `{{ .ServiceName | replace "-" "_" | upper }}` transform
- `{{ .ServiceName | replace "-" "_" | lower }}` transform

Use a regex like `\{\{\s*\.TokenName\s*\}\}` to match both spacing variants in one pass.

Helm values placeholder normalization per `helm-runtime.skill.md`:
- `{{{ .ServiceName | replace "-" "_" | upper }}_IMAGE_TAG}` -> `#{SERVICE_NAME_IMAGE_TAG}#`

Token replacement is MANDATORY for: all workflow files, all Helm values files, all azureConfig files, all bgmConfig files, `manage-azureConfig.ps1`.

DO NOT modify YAML structure, jobs, steps, comments, ACR placeholders, or PowerShell variables (`$Environment`, `$Name`).

After replacement: verify no remaining `{{ .ServiceName }}`, `{{.ServiceName}}`, `{{ .Namespace }}`, `{{.Namespace}}`, `{{ .ReleaseName }}`, `{{.ReleaseName}}`, `{{ .ReleaseNameTwo }}`, `{{.ReleaseNameTwo}}`, `{{ .RepoName }}`, `{{.RepoName}}`, `{{ .OrgName }}`, `{{.OrgName}}`, or `{{ .DeploymentName }}`, `{{.DeploymentName}}` tokens exist in any file. If any remain: STOP with the file path and line number.

**Step 10a - Generate config/MainManifest.yml (if not already present)**

- If the file already exists in the target repo: do NOT modify it
- If the file does NOT exist:
  * Read `templates/service/config/MainManifest.example.yml` from the cloned reference repo
  * Read `templates/service/config/manifest-schema.json` from the cloned reference repo
  * Scan the entire target repository structure
  * CREATE a new `config/MainManifest.yml` following the schema structure:
    - Set `manifestVersion: "1.0"`
    - Set `product.name` to the repository name
    - Set `product.iamDetails.code` to ServiceName in ALL UPPERCASE (e.g., PERSASST, CUSTMGMT). Max 12 chars, alphabetic only. Key Vault will be named kv-{region}-{lower(iamDetails.code)}-{env}
    - Set `product.cloud` to "azure"
    - Add detected deployments (ui, api, workers, microfrontend apps) with ports, healthCheck, capacity, and configuration
    - Add required configuration for each deployment: IAM_CLIENT_ID, IAM_CLIENT_SECRET, IAM_POID, API_URL, API_KEY
    - Add detected infrastructure (databases - postgres only currently)
    - Set storage, caching, messaging as empty arrays (FUTURE)
    - Add routing with domain patterns and path-based routes
    - Add dependencies (internal/external)
  * Validate the generated file against manifest-schema.json structure
  * If databases/infrastructure cannot be detected: ask the user

**Step 10b - Cross-Organization Repository Access (conditional)**

- Determine if target repository is OUTSIDE the "Shared-Technology-Group" organization
- If the target repo IS inside Shared-Technology-Group: SKIP this step
- If the target repo is OUTSIDE Shared-Technology-Group:
  * Scan ALL copied workflow files (.github/workflows/*.yml) for references to Shared-Technology-Group repositories (e.g., reusable workflow calls, action definitions)
  * For EACH workflow file that references a Shared-Technology-Group repository:
    - Add a checkout step using REPO_ACCESS_TOKEN (org-level secret):
      ```yaml
      - name: Checkout {referenced-repo}
        uses: actions/checkout@v4
        with:
          repository: Shared-Technology-Group/{referenced-repo}
          token: ${{ secrets.REPO_ACCESS_TOKEN }}
          path: .github/.external/{referenced-repo}
          ref: main
      ```
    - Place this checkout step BEFORE any step that uses files from the referenced repository
    - Update subsequent path references to use the checkout path (.github/.external/{referenced-repo}/...)
  * Only add checkout to files that ACTUALLY reference Shared-Technology-Group paths - do NOT add to files that don't need it
  * Do NOT modify the org-level REPO_ACCESS_TOKEN secret (it already exists)
  * The detailed rules are defined in the DevOps Pipeline Skill

**Step 11 - Inspect Dockerfile**

Use the Dockerfile discovery results from Step 8a. The Dockerfiles were already located, validated, and classified during the PRE-SCAN PHASE. Apply the classification and build context information determined earlier.

**Step 12 - Classify service**

Determine classification: Micro-Frontend or Standard Service. This decision is FINAL and AUTHORITATIVE. All subsequent steps must reflect it.

**Step 13 - Resolve build targets**

Based on the classification from Step 12, determine the build targets. Micro-Frontend: multiple build units (one per app). Standard: single build unit.

**Step 14 - Apply Dockerfile-aware augmentation (additive only)**

Follow `devops-pipeline.skill.md` DOCKERFILE-AWARE AUGMENTATION rules.

- Micro-Frontend: add additional container repository entries
- Standard: extract exposed port, update ONLY port values in Helm values file

Inject resolved Dockerfile path into `docker-build-push-{{ .ServiceName }}.yml` and `docker.step.build-push-{{ .ServiceName }}.yml`.

No deletions. No reformatting.

**Step 15 - Apply Helm runtime configuration**

Follow `helm-runtime.skill.md` HELM RUNTIME CONFIGURATION RULES:
- Exactly ONE `envFrom` block per Helm release
- Use `nameOverride` (not `fullnameOverride`) by default
- Secrets and AppConfig references MUST NOT be duplicated per container

**Step 16 - Configure ingress paths**

Follow `helm-runtime.skill.md` INGRESS PATH STRUCTURE RULES:
- Backend service: `/<ServiceName>/api`
- Frontend service: `/<ServiceName>/<frontend-segment>`
- Micro-Frontend: discover all paths from Dockerfile, validate each path independently per its type (frontend or backend rule)

**Step 17 - Detect database usage and determine migration inclusion (AUTOMATIC)**

This step is MANDATORY and MUST NOT be skipped.
The agent MUST scan the repository for database usage (see MIGRATION JOB AUTOMATIC DETECTION section above). The agent MUST NOT ask the user.

If database IS detected:
- Determine migration configuration (tool, workingDir, command)
- IMMEDIATELY add Helm hook annotations to azureConfig and bgmConfig files:
  - Scan manage-appConfig-secrets/azureConfig/appconfig-*.yml
  - Scan manage-appConfig-secrets/azureConfig/keyvault-secrets-*.yml
  - Scan manage-appConfig-secrets/bgmConfig/appconfig-*.yml
  - Add annotations to configs[], secrets[], containerRegistries[] sections
  - Verify annotations were added successfully
- If annotations are NOT found after processing: ADD them immediately
- Rules are mentioned in the DevOps Pipeline Skill

If NO database detected:
- Note to exclude migration job section
- Keep azureConfig annotations as empty objects: `annotations: {}`

Store detection result for Step 28.

**Step 18 - Generate two BGM release names**

Per `devops-pipeline.skill.md` BGM CONFIGURATION RELEASE NAMES rules:
- Primary ReleaseName: adjective-noun (e.g. `brave-eagle`)
- Secondary ReleaseNameTwo: different adjective-noun (e.g. `swift-falcon`)
- Both deterministic, both different from each other

Apply to bgmConfig files: setName `one` uses ReleaseName, setName `two` uses ReleaseNameTwo.

**Step 19 - Update azureConfig values**

Inspect the target repository for environment variables and known config keys. Add missing keys to appconfig and keyvault files. NEVER remove or rename existing keys. This is additive only.

**Step 20 - Micro-Frontend conditional build logic (if applicable)**

Only if service is classified as Micro-Frontend. Read `.polaris/skills/devops-microfrontend.skill.md` first, then follow its MICRO-FRONTEND DEPLOYMENT STRUCTURE and MICRO-FRONTEND MULTI-IMAGE WORKFLOW HANDLING rules:

- Add path-based `detect-changes` job to docker workflow
- Each build job executes only when its folder has changes OR `force_build_all` is triggered
- Update `docker.acr-images.promote` with steps for ALL images
- Update `docker.step.build-push` with build steps for ALL images
- Update `helm.step` deploy with image tag handling for ALL images
- Update Helm values with separate `deployments[]`, `services[]`, `ingress[]` for EACH container
- Update ALL BGM workflow files (`bgm.helm.step`, `bgm.helm.lwr`, `bgm.helm.upr`) with ALL image handling

---

**--- ENVIRONMENT SETUP PHASE (BLOCKING, SEQUENTIAL) ---**

In this phase the agent triggers the central Polaris Bootstrap workflow
at `Aptean-Labs/polaris-devops` to populate per-environment Azure SPN
credentials and configuration variables in the target app repo. The
agent does NOT execute any local PowerShell, does NOT call `az`, and
does NOT read Key Vault or App Configuration directly.

FORBIDDEN during this phase: `Start-Sleep` between trigger and watch,
local execution of `set-env-secrets.ps1` or `set-env-vars.ps1`, any `az`
command, retrying the bootstrap workflow more than once.

**Step 21 - Verify all files are saved**

Confirm all generated and modified files are written to disk.

**Step 22 - TRIGGER POLARIS BOOTSTRAP WORKFLOW**

Determine the target repo's owner and name:
```
gh repo view --json owner,name --jq "\(.owner.login) \(.name)"
```
Store as `<owner>` and `<repo>`.

Trigger the central bootstrap workflow:
```
gh workflow run bootstrap.yml \
  -R Aptean-Labs/polaris-devops \
  -f target_owner=<owner> \
  -f target_repo=<repo> \
  -f environments=dev,tst,devops-build,prd-a
```
Default environments are `dev,tst,devops-build,prd-a`. The `devops-build`
env is required by the docker-build-push pipeline; it reuses the `DEV_*`
source values (build ACR is the dev ACR per Aptean convention). Remove
`prd-a` from this list only if the PRDA org secret or PRDA repo-level
variables in `polaris-devops` are not yet populated for your tenant.

Wait 5 seconds, then resolve the run ID:
```
gh run list --workflow bootstrap.yml \
  --repo Aptean-Labs/polaris-devops \
  --limit 1 --json databaseId --jq ".[0].databaseId"
```
If no run ID is returned, retry up to 3 times with 5-second intervals
(GitHub needs a moment to register the dispatch).

Watch until completion:
```
gh run watch <run-id> --repo Aptean-Labs/polaris-devops
```

If `gh run watch` exits non-zero: fetch logs and surface them:
```
gh run view <run-id> --log-failed --repo Aptean-Labs/polaris-devops
```
Then STOP with: "Bootstrap workflow failed. Run URL printed above. Common
causes: missing org secret in Aptean-Labs (DEV/TST/PRDA_AZURE_CREDENTIAL_AUTOMATION
or POLARIS_DEVOPS_PAT), this repo not in 'Selected repositories' for those
secrets, PAT lacks write on target repo. Contact the platform team."
Do NOT retry the bootstrap workflow automatically.

If success: log "Bootstrap workflow completed for <owner>/<repo>."

**Step 23 - VERIFY SECRETS AND VARIABLES IN TARGET REPO (single check)**

List environments ONCE:
```
gh api repos/<owner>/<repo>/environments --jq ".environments[].name"
```

For EACH environment that was requested in Step 22 (e.g. dev, tst):
- Verify `AZURE_CREDENTIAL_AUTOMATION` secret exists:
  ```
  gh secret list --env <env> --repo <owner>/<repo> --json name --jq ".[] | select(.name==\"AZURE_CREDENTIAL_AUTOMATION\") | .name"
  ```
- Verify the expected variables exist:
  ```
  gh variable list --env <env> --repo <owner>/<repo> --json name --jq ".[].name"
  ```
  Expected: at minimum `CLUSTER_NAME`, `CLUSTER_RG_NAME`, `ACR_NAME`, `ACR_HOSTNAME`, `OCI_REGISTRY_URL`. Other variables (DB_RG_NAME, APTEANONE_PGSQL_SERVER_NAME, REMOTE_BACKEND_STORAGE_ACCOUNT, TF_RG_NAME) are also written by the bootstrap workflow when their source values are present in `Aptean-Labs/polaris-devops` repo variables.

If ANY required entry is missing for an environment that was bootstrapped
successfully: STOP with "Bootstrap workflow reported success but secret/
variable not found in target repo. Run URL: <run-id>. Possible cause:
source value missing in `polaris-devops` (variable named `<PFX>_<NAME>`
not set on that repo)."

Do NOT add sleep. Do NOT poll repeatedly. Do NOT re-trigger the bootstrap
workflow.

Log: "All required secrets and variables verified for <owner>/<repo>."

**Step 26 - ADD REQUIRED REVIEWERS**

Follow `devops-pipeline.skill.md` ENVIRONMENT REQUIRED REVIEWERS rules exactly.

Reviewer resolution (automatic, no user input):
1. Get authenticated username: `gh api user --jq .login`
2. Get numeric user ID: `gh api "users/{username}" --jq .id`
3. Add svc-GitHub_aptean as repository collaborator with admin access (MANDATORY):
   - Execute: `gh api "repos/{owner}/{repo}/collaborators/svc-GitHub_aptean" -X PUT -f permission=admin`
   - If fails: retry ONCE, then try with write permission
   - If ALL attempts fail: log WARNING, continue execution, mark svc-GitHub_aptean as unavailable
4. Get svc-GitHub_aptean numeric user ID:
   - Execute: `gh api "users/svc-GitHub_aptean" --jq .id`
   - If fails: retry ONCE, log WARNING if still fails, mark as unavailable
5. If authenticated user resolution fails: try repo owner as fallback
6. If all methods fail for authenticated user: STOP with clear error

For EACH environment EXCEPT `devops-build`, `dev`, and `tst` (`prd-wus2`, `prd-eus`, `prd-gwc`, `prd-gen`, `uat`, `uat-a`, `dmo`, `prd-a`):

If svc-GitHub_aptean is available, add BOTH reviewers:
```powershell
$json = "{`"reviewers`":[{`"type`":`"User`",`"id`":$userId},{`"type`":`"User`",`"id`":$svcUserId}]}"
$json | gh api "repos/{owner}/{repo}/environments/{env}" -X PUT --input -
```

If svc-GitHub_aptean is NOT available, add authenticated user only:
```powershell
$json = "{`"reviewers`":[{`"type`":`"User`",`"id`":$userId}]}"
$json | gh api "repos/{owner}/{repo}/environments/{env}" -X PUT --input -
```

- `type` MUST be `"User"`
- `id` MUST be the NUMERIC user ID (not username string)
- No sleep between assignments
- Verify reviewers were added. Retry ONCE if failed.
- If retry fails: log WARNING, continue to next environment (DO NOT STOP)

Log: "Reviewers assignment completed"

**Step 27 - FINAL REVIEWER VERIFICATION**

Check each environment (except `devops-build`, `dev`, and `tst`) ONCE. If missing: log which environment and reviewer is missing for manual addition. Do NOT retry repeatedly.

Log: "Reviewer verification completed"

---

**--- POST-PROCESSING (BLOCKING) ---**

**Step 28 - Apply migration job decision to Helm values**

Using the decision stored in Step 17:
- YES: include migration job section with detected config (`workingDir`, command, args)
- NO: exclude `jobs:` section, keep as `jobs: []`

**Step 29 - FAST MODE RECONCILIATION (single pass, non-recursive)**

Scope: only files listed in the whitelist, Dockerfile, Helm values, and workflow files. Do NOT traverse unrelated files. Do NOT re-classify service type.

- Validate Dockerfile classification consistency across all generated files
- Validate token replacement: no remaining `{{ .ServiceName }}`, `{{.ServiceName}}`, `{{ .DeploymentName }}`, `{{.DeploymentName}}`, `{{ .OrgName }}`, `{{.OrgName}}`, or any other `{{ .* }}` / `{{.* }}` tokens. No malformed GitHub expressions, no escaped Helm placeholders, no extra backtick-wrapped braces
- Validate NO `TO_BE_CONFIGURED` placeholders remain in any generated file. If found, resolve them using the derived values (e.g., Helm values paths should use `helm/<ServiceName>/values-<ServiceName>.yml`)
- Validate GitHub Actions version consistency across ALL workflow files:
  - `actions/checkout` MUST be `@v4` (not v2 or v3)
  - `Azure/login` MUST be `@v2.1.1` (not v1)
  - `docker/setup-buildx-action` MUST be `@v3` (not v1)
  - `azure/CLI` MUST be `@v2` (not v1)
  If the reference template has outdated versions, update them during reconciliation.
- Validate environment name casing: all environment references MUST be lowercase (e.g., `uat-a` not `uat-A`). GitHub environments are case-sensitive.
- Validate variable names in workflow files: `vars.CLUSTER_RG_NAME` (not `vars.RG_CLUSTER`). The expected names are written by the Polaris Bootstrap workflow at `Aptean-Labs/polaris-devops` and are: `CLUSTER_NAME`, `CLUSTER_RG_NAME`, `ACR_NAME`, `ACR_HOSTNAME`, `OCI_REGISTRY_URL`, `DB_RG_NAME`, `APTEANONE_PGSQL_SERVER_NAME`, `REMOTE_BACKEND_STORAGE_ACCOUNT`, `TF_RG_NAME`.
- Validate secrets handling consistency: prefer `secrets: inherit` over explicit secret listing in reusable workflow calls. Standardize across all workflow files.
- Validate Helm invariants: exactly one Helm release, exactly one `envFrom`, no multi-container deployments for micro-frontends (per `helm-runtime.skill.md`)
- Validate all required files exist. STOP if any are missing. Do NOT attempt regeneration.
- Validate required reviewers per environment. Log missing ones for manual addition.
- If a violation is found: fix it ONCE. Do NOT restart reconciliation. Do NOT perform additional scans.

**Step 30 - Verify all required files exist**

Verify that all files required for the classified service type (Micro-Frontend or Standard) are present.

**Step 31 - Micro-Frontend multi-container verification (if applicable)**

Only if service is classified as Micro-Frontend with multiple containers. Verify:
- Promote workflow has steps for ALL images
- Build workflow has jobs for ALL images
- `helm.step` workflow has `--set` commands for ALL images
- Helm values file has `deployments[]`, `services[]`, `ingress[]` for ALL images
- BGM workflows (`bgm.helm.step`, `bgm.helm.lwr`, `bgm.helm.upr`) handle ALL images

If any are missing: fix them.

**Step 32 - Enforce final newline rules**

Ensure all generated files end with a single newline character.

---

**--- FINALIZATION ---**

**Step 33 - Display comprehensive final summary report**

```
FILES CREATED:
  .github/workflows/ - list each .yml file with its purpose (BGM/Docker/Helm/Terraform)
  helm/<ServiceName>/values-<ServiceName>.yml - Kubernetes deployment configuration
  infrastructure/<ServiceName>/main.tf - Terraform configuration
  infrastructure/<ServiceName>/variables.tf
  infrastructure/<ServiceName>/versions.tf
  manage-appConfig-secrets/azureConfig/* - Azure App Configuration and Key Vault
  manage-appConfig-secrets/bgmConfig/* - Blue-Green deployment configuration
  config/MainManifest.yml - Service manifest with deployments, infrastructure, routing, and environment configuration

REQUIRED REVIEWERS:
  <env-name>: Added / Missing
  (for each environment except devops-build, dev, and tst)
  (if any missing: instructions to add manually via GitHub Settings -> Environments)

NEXT STEP:
  Run /polaris.deploy to merge the PR and trigger all pipelines automatically.
  The deploy command will handle: PR merge, Docker build, infrastructure provisioning,
  DATABASE_URL configuration, and Helm deployment for dev (and optionally tst).

DOCUMENTATION: See manage-appConfig-secrets/README.md

WARNINGS/MANUAL ACTIONS: (list any issues encountered or manual steps needed)
```

**Step 34 - Commit all changes**

Commit all created and modified files to the `feature-<ServiceName>-devops` branch.

**Step 35 - Open PR to main branch**

Open a pull request from `feature-<ServiceName>-devops` to the default branch.

---

### FAILURE HANDLING

On any violation: DO NOT partially apply changes. DO NOT open a PR. Exit with a clear error message identifying the violation and what needs to be fixed.

**Exception**: Reviewer assignment failure MUST NOT fail the agent. Log reviewer failures and continue.

---

### CONTEXTUAL UPDATE MODE (POST-SCAFFOLDING CHANGES)

When the user requests changes to specific sections after the initial scaffolding run (e.g., "add migrations", "fix helm values", "update bgm config"), the agent MUST follow the Contextual Update Skill (`.polaris/skills/contextual-update.skill.md`).

The skill defines:
- The 5-step procedure (re-read agent definition, load skills, inspect state, apply changes, verify)
- Common scenario-to-step mappings (migrations, helm, bgm, workflows, MainManifest, annotations)
- Critical rules for contextual mode execution

The agent MUST NOT re-run the entire scaffolding process.
The agent MUST load and follow the Contextual Update Skill for every post-scaffolding request.

---


## Path B: Generic

## Quick Mode

If user passes `--quick` or arguments contain "quick": Skip discovery questions. Auto-detect language/framework. Use defaults: GitHub Actions CI/CD, Kubernetes deployment, all environments (dev/staging/prod). Generate Dockerfile, workflows, Helm charts, and .env.example immediately.

## Goal

Set up a complete DevOps pipeline following organization standards. Generates CI/CD workflows, Dockerfiles, container orchestration configs, and environment management.

## Steps

### 1. Discovery

Detect project context:
- **Language/framework**: Scan for package.json, pyproject.toml, go.mod, Cargo.toml, etc.
- **Existing CI/CD**: Check .github/workflows/, .gitlab-ci.yml, azure-pipelines.yml
- **Existing Docker**: Check Dockerfile, docker-compose.yml
- **Test framework**: Detect test runner

Ask the user:
- **CI/CD platform**: GitHub Actions (default), Azure DevOps, GitLab CI
- **Deployment target**: Container registry, Kubernetes, cloud service, or none (CI-only)
- **Environments**: dev, staging, production
- **Container registry**: ghcr.io, Docker Hub, ACR, ECR (if deploying containers)

### 2. Generate CI/CD Pipeline

Based on selected platform, generate workflow files:

**GitHub Actions** (.github/workflows/): `ci.yml` (lint+test+build on PR), `release.yml` (container build+push on tag), `deploy.yml` (K8s deployment)

**Azure DevOps** (azure-pipelines.yml): Build pipeline with stages: lint, test, build, deploy

**GitLab CI** (.gitlab-ci.yml): Pipeline with stages: lint, test, build, deploy

Each pipeline includes: language-appropriate build, test execution with coverage, container image build/push, environment-specific deployment gates.

### 3. Generate Dockerfile

If no Dockerfile exists, create one with:
- Multi-stage build (separate build and runtime stages)
- Non-root user for security
- HEALTHCHECK instruction
- Standard OCI labels
- Language-specific optimizations: Python=slim base+requirements caching, Node=alpine+package.json caching, Go=static binary+scratch/distroless, C#=SDK build+aspnet runtime

### 4. Generate Docker Compose

If deploying with docker-compose, generate standard service config with build, ports, env_file, and healthcheck.

### 5. Generate Helm Charts (if Kubernetes)

Create complete Helm chart structure under `helm/`:

```
helm/
  Chart.yaml              # apiVersion v2, app metadata
  values.yaml             # Base: replicaCount=1, image config, service ClusterIP:80->8080,
                          # resources (100m-500m CPU, 128Mi-512Mi mem), liveness/readiness probes
  values-staging.yaml     # replicaCount=2, ingress enabled, staging domain
  values-production.yaml  # replicaCount=3, ingress+TLS, autoscaling 3-10 replicas, 500m-1000m CPU
  templates/
    _helpers.tpl          # Standard name, fullname, labels, selectorLabels helpers
    deployment.yaml       # Standard Deployment with all values references
    service.yaml          # ClusterIP service
    ingress.yaml          # Conditional ingress with TLS support
    hpa.yaml              # Conditional HPA with CPU/memory targets
    serviceaccount.yaml   # Conditional ServiceAccount
    configmap.yaml        # Optional ConfigMap
    secret.yaml           # Optional Secret
```

Use standard Helm chart patterns. All templates must reference values via `{{ .Values.* }}` and use the helper functions from `_helpers.tpl`. Security: `runAsNonRoot: true, runAsUser: 1000`.

### 5b. Generate CD Pipeline

Generate deployment pipeline for the selected CI/CD platform that deploys to Kubernetes using Helm:
- **GitHub Actions**: `deploy.yml` with staging (on release) and production (manual dispatch) jobs using `azure/setup-helm@v3` and `azure/k8s-set-context@v3`
- **Azure DevOps**: `azure-pipelines-deploy.yml` with parameterized environment and version, using `HelmInstaller@1` and `Kubernetes@1` tasks
- **GitLab CI**: Deploy stages using `alpine/helm:3.13.0` image with kubeconfig from secrets

Each pipeline: `helm upgrade --install` with namespace per environment, values files overlay, image tag override, `--wait --timeout 5m`, followed by `kubectl rollout status` verification.

### 6. Environment Configuration

Create `.env.example` with all required variables (no real values). Document environment-specific overrides.

### 7. Validation

1. Lint generated workflow files
2. Build Docker image locally: `docker build -t <project>:dev .`
3. Run container with health check
4. Verify CI config syntax

### 8. Summary

List all generated files (workflows, Dockerfile, docker-compose, .env.example, helm/), then next steps: review configs, set up repository secrets (registry creds, kubeconfig), update helm values with actual registry/domain, push to trigger CI, run `/polaris.healthcheck`.

## Principles

- Detect before generating (scan existing setup first)
- Never store secrets (only .env.example with placeholders)
- Multi-stage Docker builds (minimize size and attack surface)
- Health checks everywhere
- Ask before overwriting existing configs

Context: {ARGS}


**Telemetry**: Run: `polaris telemetry record devops --feature <slug> --phase complete --agent {{AGENT_NAME}}`
