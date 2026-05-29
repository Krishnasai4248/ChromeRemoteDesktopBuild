---
name: DevOps Pipeline Skill
description: |
Governs CI/CD pipeline and Docker build invariants.
---

## PATH CONTROL RULES

manage-appConfig-secrets/**
    - Structure MUST NOT change
    - Existing values MUST NOT be removed
manage-appConfig-secrets/azureConfig/**
    - Agent MUST inspect the target repository for:
        - Environment variables
        - Application configuration usage
        - Known config keys referenced in code or manifests
    - Agent MUST add missing keys to appconfig and keyvault files
    - Agent MUST NOT remove or rename existing keys
    - If the required value cannot be inferred:
        - Insert the key with the existing default value
        - OR leave the placeholder value unchanged

## MIGRATION-AWARE HELM HOOK ANNOTATIONS (CONDITIONAL)

If migration job is included in the deployment:

The agent MUST add Helm hook annotations to the following sections
in all azureConfig files AND bgmConfig files present inside manage-appConfig-secrets folder:

1. configs[] section in appconfig*.yml files:
     annotations:
       helm.sh/hook: pre-install,pre-upgrade
       helm.sh/hook-weight: "-5"

2. secrets[] section in keyvault-secrets*.yml files:
     annotations:
       helm.sh/hook: pre-install,pre-upgrade
       helm.sh/hook-weight: "-10"

3. containerRegistries[] section in keyvault-secrets*.yml files:
     annotations:
       helm.sh/hook: pre-install,pre-upgrade
       helm.sh/hook-weight: "-10"

If migration job is NOT included:

Keep annotations as empty objects:
     annotations: {}

CRITICAL EXECUTION RULES:

1. This MUST happen immediately after database detection confirms a database is present
2. The agent MUST scan ALL files in:
     - manage-appConfig-secrets/azureConfig/appconfig-*.yml
     - manage-appConfig-secrets/azureConfig/keyvault-secrets-*.yml
     - manage-appConfig-secrets/bgmConfig/appconfig-*.yml (BGM files too)
3. For EACH file, the agent MUST:
     - Locate the configs[] section (if present in appconfig files)
       * Add annotations under each config item
     - Locate the secrets[] section (if present in keyvault-secrets files)
       * Add annotations under each secret item
     - Locate the containerRegistries[] section (if present in keyvault-secrets files)
       * Add annotations under each containerRegistry item
       * annotation doesnot exist in the template add annotations to it
4. Annotations MUST be indented correctly according to YAML structure
5. The agent MUST verify annotations were added after processing:
     - Check configs[] in appconfig files
     - Check secrets[] in keyvault-secrets files
     - Check containerRegistries[] ONLY if the section has items
6. If annotations are NOT found in configs[] or secrets[] or containerRegistries[] after database was detected → add it

Rules:
- Annotations MUST be added ONLY if a database is detected in the repository
- Hook weights MUST be set as specified above
- DO NOT modify any other fields in these sections
- DO NOT add annotations to any other sections
- This applies to ALL environment-specific azureConfig files
- This applies to ALL environment-specific bgmConfig files
- Donot add helm.sh/hook-delete-policy: before-hook-creation to the annotations
- Make sure annotations are included in:
    - configs section in appconfig* files (both azureConfig/ and bgmConfig/)
    - secrets and containerRegistries sections in keyvault-secrets* files (azureConfig/ only)
- bgmConfig files typically contain only appconfig files, not keyvault-secrets

## APP CONFIG & SECRETS SCOPING (STRICT)

For Micro-Frontend services:

- AppConfig and KeyVault entries MUST be:
      - Shared across all containers
      - Defined ONCE per environment

Rules:

1. The agent MUST NOT create:
       - Per-container appConfig files
       - Per-container secret definitions

2. All containers MUST consume the SAME:
       - AppConfig
       - KeyVault
       - Environment variables

## AUTHORITATIVE SERVICE NAMING CONTRACT (BLOCKING PHASE)

ServiceName, Namespace, and ReleaseName MUST be derived strictly by these rules. The agent MUST NOT invent alternate naming logic.

### ServiceName

The ONE identity used consistently across file names, helm charts, K8s resources, routing paths, Key Vault names, Terraform state, and IAM product codes.

| Constraint | Requirement |
|---|---|
| Source | Derived from repository name |
| Length | 2-12 characters (inclusive) |
| Form | SINGLE word, no hyphens, no underscores, no separators |
| Case in `MainManifest.yml iamDetails.code` | ALL UPPERCASE (e.g. `PERSASST`) |
| Case everywhere else | all lowercase (e.g. `persasst`) |
| Charset | lowercase letters only, starts with a letter, no digits or separators |
| Compatibility | DNS-label compatible |

**Derivation steps (STRICT):**
1. Analyze the repository name to understand its core purpose.
2. Split on `-` and `_`.
3. Remove ONLY generic technical filler words: `service`, `application`, `app`, `repo`, `test`, `workspace`. Words that describe architecture or domain (e.g. `micro`, `frontend`, `backend`, `docker`) MUST NOT be removed blindly.
4. From the remaining meaningful words, concatenate (no separators) into a single 2-12 character name. Abbreviate if needed.
5. The result MUST be immediately recognizable, MUST be globally unique across Aptean products, and MUST NOT be a generic word like `assist`, `service`, `admin`, `portal`, `backend`.
6. UNIQUENESS CHECK (mandatory before finalizing): `gh search code "iamDetails" --owner Shared-Technology-Group --owner Aptean-Labs`. If a collision is found, choose a different name.
7. If no meaningful 2-12 character name can be derived: ask the user.

**Examples:**

| Repo | ServiceName |
|---|---|
| `customer-management-service` | `custmgmt` |
| `employee-portal-app` | `employportal` |
| `micro-frontend-admin` | `microfrontend` |
| `inventory-backend-service` | `inventback` |
| `personal-assistant-workspace` | `persasst` |
| `notification-scheduler` | `notifschedlr` |
| `analytics-dashboard` | `analyticsdash` |
| `order-processing-service` | `orderprocess` |
| `adr-workspace` | `adrws` |

**Key Vault naming:** `kv-{region}-{lower(iamDetails.code)}-{env}` (e.g. `kv-eus-persasst-tst`). Budget: `kv-` (3) + region (4) + code (2-12) + `-` (1) + env (3-4) <= 24 chars.

### Namespace

- Derived directly from ServiceName (typically IDENTICAL to ServiceName since ServiceName has no hyphens or suffixes).
- MUST be lowercase, DNS-1123 compliant, <= 63 characters.
- DNS-1123 rules: lowercase, alphanumeric and hyphens only, starts with a letter, ends with letter or number.
- If Namespace violates constraints: STOP with a clear error.

### ReleaseName

- Generated by agent. Format: `<adjective>-<noun>`. Deterministic per execution.

### BGM Configuration Release Names (CRITICAL)

For `bgmConfig` files (`manage-appConfig-secrets/bgmConfig/`), TWO distinct release names are required. Each `setName` (`one`, `two`) MUST have a unique release name; both MUST follow the same format and be deterministic.

| Token | Maps to | Used by |
|---|---|---|
| `{{ .ReleaseName }}` | Primary release name (e.g. `brave-eagle`) | Service with `setName: one` |
| `{{ .ReleaseNameTwo }}` | Secondary release name (e.g. `swift-falcon`) | Service with `setName: two` |

The agent MUST replace BOTH tokens with DIFFERENT values.

Example (before -> after):
```yaml
services:
- name: {{ .ReleaseName }}-{{ .ServiceName }}-svc-{{ .ServiceName }}
  releaseName: {{ .ReleaseName }}
  setName: one
- name: {{ .ReleaseNameTwo }}-{{ .ServiceName }}-svc-{{ .ServiceName }}
  releaseName: {{ .ReleaseNameTwo }}
  setName: two
```
After token replacement: `brave-eagle-{{ .ServiceName }}-svc-{{ .ServiceName }}` / `releaseName: brave-eagle` / `setName: one`, and `swift-falcon-{{ .ServiceName }}-svc-{{ .ServiceName }}` / `releaseName: swift-falcon` / `setName: two`.

## TOKEN REPLACEMENT (STRICT + TRANSFORMS)

### Base tokens (ALWAYS supported)

| Token | Replacement | Notes |
|---|---|---|
| `{{ .ServiceName }}` | derived service name (lowercase, no hyphens) | |
| `{{ .Namespace }}` | derived namespace | |
| `{{ .ReleaseName }}` | generated release name | |
| `{{ .ReleaseNameTwo }}` | secondary release name | BGM only |
| `{{ .RepoName }}` | full target repo name | infra workflow files |
| `{{ .DeploymentName }}` | `name` from `config/MainManifest.yml` deployments[] | Helm values `envFrom` and job containers |
| `{{ .OrgName }}` | GitHub org name of target repo | infra workflow files |

**Spacing variants:** templates may use `{{ .Token }}` OR `{{.Token}}`. The agent MUST replace BOTH variants for every token. Use regex `\{\{\s*\.TokenName\s*\}\}` to handle both forms in one pass. After replacement, verify NEITHER variant remains in any file.

### DeploymentName resolution (MANDATORY)

- Read `config/MainManifest.yml` and locate the `deployments[]` array.
- `{{ .DeploymentName }}` MUST be replaced with the `name` field of the deployment matching the current context (e.g. `api`, `ui`, `worker`).
- In Helm values files, this token appears in `envFrom` (configMapRef/secretRef names) and in job containers.
- Single-deployment service: use that deployment's name. Multi-deployment service: match the context (e.g. migration jobs use the backend/api deployment).
- If `config/MainManifest.yml` does not exist yet (being generated in Step 10a): use the deployment name determined during repository scanning.
- Typical names: `api` (backend), `ui` (frontend), or the specific name from the manifest.

### Supported ServiceName transforms

Pipe transforms are allowed ONLY on `ServiceName`. Only `replace`, `upper`, `lower` are supported. Order: `replace` -> `upper`/`lower`. Any unsupported transform: STOP with error.

| Pattern | Result | Example (`ServiceName=test-repo`) |
|---|---|---|
| `{{ .ServiceName \| replace "-" "_" \| upper }}` | `SERVICE_NAME` | `TEST_REPO` |
| `{{ .ServiceName \| replace "-" "_" \| lower }}` | `service_name` | `test_repo` |

### Helm values file pattern (CRITICAL)

Pattern: `{{{ .ServiceName | replace "-" "_" | upper }}_IMAGE_TAG}` (note the TRIPLE opening braces `{{{`).

Two-step transform:
1. Apply transform -> `{{{TEST_REPO_IMAGE_TAG}`
2. Normalize: replace `{{{` with `#{`, replace closing `}` with `}#` -> `#{TEST_REPO_IMAGE_TAG}#`

### Execution requirements

- Token replacement MUST happen IMMEDIATELY after files are copied.
- Process ALL copied files in a single pass.
- Verify no remaining variants of any token across all files.
- If ANY unreplaced token remains: STOP with clear error showing file and line.

### Files where replacement is MANDATORY

- ALL workflow files (`.github/workflows/*.yml`)
- ALL Helm values files (`helm/**/values-*.yml`)
- ALL azureConfig files (`manage-appConfig-secrets/azureConfig/*.yml`)
- ALL bgmConfig files (`manage-appConfig-secrets/bgmConfig/*.yml`)
- `manage-appConfig-secrets/manage-azureConfig.ps1` (PowerShell script). It contains patterns like `bgm-configuration-{{ .ServiceName }}-eastus-$Environment`. Replace the `{{ .ServiceName }}` portion only. PowerShell variables (`$Environment`, `$Name`, etc.) MUST NOT be modified.

### What to NOT modify

YAML structure, jobs, steps, comments, ACR placeholders, or PowerShell variables (`$Environment`, `$Name`).

## DOCKERFILE-AWARE AUGMENTATION

- Read Dockerfile in target repo
- If Micro-Frontend detected:
      - Add additional container repository entries
- Else:
      - Extract exposed port
      - Update ONLY port values in Helm values file
Additive only. No deletions. No reformatting.

Once Micro-Frontend vs Standard Service is determined:
- ALL generated files MUST reflect that classification.
- No later step may override or ignore this result.
If any file violates this invariant:
    → The agent MUST correct it during the single reconciliation phase
    
The result of Dockerfile-aware augmentation is AUTHORITATIVE.
    
## DOCKERFILE DISCOVERY & BUILD CONTEXT RESOLUTION (MANDATORY)

The agent MUST NOT assume the Dockerfile name, location, or count, and MUST NOT assume a single Dockerfile means a single service.

### Discovery rules (STRICT)

Scan the ENTIRE target repository for Dockerfiles. Match filenames `Dockerfile` and `Dockerfile.*` (case-sensitive). Search ALL directories, not just the root.

### Classification of discovery results

**a) Single Dockerfile, single service** (one final stage, one `EXPOSE`, one CMD/ENTRYPOINT):
- Standard single-build scenario.
- Derive `dockerfile` path (relative to repo root) and `build context` (parent directory).
- One build configuration in docker workflows.

**b) Single Dockerfile, MULTIPLE services** (one file builds multiple services):
- Detection signals (any of):
  - Multiple named build stages, each with its own CMD/ENTRYPOINT producing a runnable image.
  - `ARG` instructions that select which app/service to build (e.g. `ARG APP_NAME`, `ARG BUILD_TARGET`).
  - Multiple `EXPOSE` instructions in different stages.
  - Repository structure references multiple app directories.
- Handling: follow the SAME pattern as Micro-Frontend multi-image (see `devops-microfrontend.skill.md`). The agent MUST NOT create separate workflow files. Instead, use the SAME workflow file set with multiple build jobs WITHIN each file, where each job passes the appropriate build args or targets the correct stage. Image names MUST distinguish services (e.g. `{{ .ServiceName }}-frontend`, `{{ .ServiceName }}-backend`). Helm values MUST have separate `deployments[]`, `services[]`, and ingress entries per service. Docker promote, BGM, and helm.step workflows MUST handle ALL images.

**c) MULTIPLE Dockerfiles in DIFFERENT directories** (multi-component repo):
- Each Dockerfile typically maps to a different deployment component (e.g. `frontend/Dockerfile`, `backend/Dockerfile`).
- Identify the component each Dockerfile serves by inspecting:
  - Parent directory name (`frontend/`, `backend/`, `api/`, `worker/`).
  - Dockerfile content (base images, `EXPOSE` ports, build output).
  - Repository structure (`package.json`, `requirements.txt` in same directory).
- Same handling as case (b): SAME workflow files, multiple build jobs within them, each specifying the correct Dockerfile path, correct build context, and a distinct image name. If a Dockerfile's purpose cannot be determined: ask the user.

**d) MULTIPLE Dockerfiles in the SAME directory:**
- If one is named exactly `Dockerfile` (no extension), prefer it.
- `Dockerfile.dev`, `Dockerfile.test` etc. are non-production and should be excluded.
- If ambiguity remains: ask the user which file to use for production builds.

**e) NO Dockerfile found:** STOP with a clear error.

### Dockerfile-to-workflow mapping summary

| Scenario | Build configurations |
|---|---|
| Single Dockerfile, single service | ONE build configuration in docker workflows |
| Single Dockerfile, multi-service | Separate build configs per service WITHIN the same workflow files (each job uses different build args / target stage) |
| Multi-Dockerfile, multi-component | Separate build configs per component WITHIN the same workflow files (each job uses its Dockerfile path + build context) |

### Injection and structure rules

- Resolved Dockerfile path(s) MUST be injected into `docker-build-push-{{ .ServiceName }}.yml` and `docker.step.build-push-{{ .ServiceName }}.yml`.
- Resolved build context(s) MUST be updated accordingly.
- YAML structure MUST NOT change beyond adding build jobs for additional services/Dockerfiles.
- For multi-service or multi-Dockerfile repos, ALL docker, helm, and BGM workflow files MUST handle ALL discovered components.
- The agent MUST NOT create separate workflow files per service or Dockerfile. All build jobs MUST be added WITHIN the existing workflow file set.
- This resolution MUST occur BEFORE Dockerfile-aware augmentation and before post-processing reconciliation.

## AZURE PRECHECK (REMOVED)

The agent does NOT log into Azure. All Azure-touching work for the K8s
flow is performed by the central Polaris Bootstrap workflow at
`Aptean-Labs/polaris-devops`.

Local preflight is ONLY:
- Run: `gh auth status`
- If not authenticated: STOP with "GitHub CLI not authenticated. Run `gh auth login` first."

Rules:
- DO NOT run `az --version`, `az account show`, `az login`, or any other `az` command.
- DO NOT install Azure CLI.
- DO NOT prompt the user for Azure credentials.
- DO NOT execute `set-env-secrets.ps1` or `set-env-vars.ps1` locally.

## ENVIRONMENT SETUP (BOOTSTRAP WORKFLOW)

The agent triggers the central Polaris Bootstrap workflow to populate
`AZURE_CREDENTIAL_AUTOMATION` secrets and configuration variables in
the target app repo's GitHub Environments. The workflow runs in the
cloud; the agent only triggers and watches.

Execution sequence (STRICT):

1. Determine target owner and repo:
     - `gh repo view --json owner,name --jq "\(.owner.login) \(.name)"`

2. Trigger the bootstrap workflow:
     - `gh workflow run bootstrap.yml -R Aptean-Labs/polaris-devops -f target_owner=<owner> -f target_repo=<repo> -f environments=dev,tst,devops-build,prd-a`
     - Default environments are `dev,tst,devops-build,prd-a`. The
       `devops-build` env is required by the docker-build-push pipeline
       and reuses the `DEV_*` source values (build ACR is the dev ACR
       per Aptean convention). Remove `prd-a` only if the PRDA org
       secret or PRDA repo-level variables in `polaris-devops` are not
       yet populated for your tenant.

3. Resolve run ID (after a 5-second wait):
     - `gh run list --workflow bootstrap.yml --repo Aptean-Labs/polaris-devops --limit 1 --json databaseId --jq ".[0].databaseId"`
     - Retry up to 3 times with 5-second intervals if no run ID is returned.

4. Watch the run:
     - `gh run watch <run-id> --repo Aptean-Labs/polaris-devops`

5. On non-zero exit:
     - Fetch logs: `gh run view <run-id> --log-failed --repo Aptean-Labs/polaris-devops`
     - STOP with a clear error pointing to the run URL. Do NOT retry the
       bootstrap workflow automatically. Common causes are misconfigured
       org secrets, the target repo not in the PAT's allow list, or
       missing repo-level variables in `polaris-devops`. None are fixable
       by retry from the agent.

6. On success: verify the writes landed (single pass, no polling).
     - For each requested environment:
         `gh secret list --env <env> --repo <owner>/<repo>` -> expect `AZURE_CREDENTIAL_AUTOMATION`.
         `gh variable list --env <env> --repo <owner>/<repo>` -> expect `CLUSTER_NAME`, `CLUSTER_RG_NAME`, `ACR_NAME`, `ACR_HOSTNAME`, `OCI_REGISTRY_URL` at minimum.

7. Proceed to reviewer assignment (separate phase).

Execution constraints:
    - The agent MUST NOT execute `set-env-secrets.ps1` or `set-env-vars.ps1`.
    - The agent MUST NOT call any `az` command.
    - The agent MUST NOT trigger the bootstrap workflow more than twice
      for the same target repo within one ship session (the second time
      only after a clear, fixable error such as a transient GitHub API
      hiccup).

## SECRET VALUE INTEGRITY (REFERENCE)

The bootstrap workflow at `Aptean-Labs/polaris-devops` is responsible
for preserving `AZURE_CREDENTIAL_AUTOMATION` byte-for-byte. The agent
no longer fetches or writes this value; it is documented here only so
operators understand the contract the org-level secrets must follow.

**AZURE_CREDENTIAL_AUTOMATION format (single-line JSON, required keys):**
```
{"clientId":"<value>","clientSecret":"<value>","subscriptionId":"<value>","tenantId":"<value>"}
```
The `terraformSPObjectId` key may also be present and is preserved.

**Source values for the bootstrap workflow:**
- Org-level secrets in Aptean-Labs (one SPN JSON per environment):
    `DEV_AZURE_CREDENTIAL_AUTOMATION`, `TST_AZURE_CREDENTIAL_AUTOMATION`, `PRDA_AZURE_CREDENTIAL_AUTOMATION`
- Org-level secret for cross-repo writes:
    `POLARIS_DEVOPS_PAT`
- Repo-level variables on `Aptean-Labs/polaris-devops`, prefixed by env:
    `<DEV|TST|PRDA>_ACR_HOSTNAME`, `<...>_ACR_NAME`, `<...>_APTEANONE_PGSQL_SERVER_NAME`,
    `<...>_CLUSTER_NAME`, `<...>_CLUSTER_RG_NAME`, `<...>_DB_RG_NAME`,
    `<...>_OCI_REGISTRY_URL`, `<...>_REMOTE_BACKEND_STORAGE_ACCOUNT`, `<...>_TF_RG_NAME`

If any required source value is missing the bootstrap workflow stops
with a clear error and the agent surfaces it via the run URL. The agent
does NOT attempt to re-create or re-fetch these values.

## CROSS-ORGANIZATION REPOSITORY ACCESS (CONDITIONAL)

When the target repository is OUTSIDE the "Shared-Technology-Group" GitHub
organization, workflow files that reference Shared-Technology-Group repositories
will FAIL because they cannot access private repos across organizations.

Detection:
- Check the target repository's owner/organization
- If owner == "Shared-Technology-Group" → SKIP this entire section
- If owner != "Shared-Technology-Group" → Apply the rules below

Rules:

1. Scan ALL workflow files (.github/workflows/*.yml) for references to
     Shared-Technology-Group repositories. Look for:
     - uses: Shared-Technology-Group/{repo}/.github/...
     - repository: Shared-Technology-Group/{repo}
     - Any path referencing Shared-Technology-Group

2. For EACH workflow file that references a Shared-Technology-Group repo:
     - Add a checkout step that uses the org-level REPO_ACCESS_TOKEN secret
     - The checkout step MUST be placed BEFORE any step that uses files
       from the referenced repository
     - Format:
       ```yaml
       - name: Checkout {referenced-repo}
         uses: actions/checkout@v4
         with:
           repository: Shared-Technology-Group/{referenced-repo}
           token: ${{ secrets.REPO_ACCESS_TOKEN }}
           path: .github/.external/{referenced-repo}
           ref: main
       ```
     - Update any subsequent path references in the workflow to use
       the checkout path (.github/.external/{referenced-repo}/...)

3. REPO_ACCESS_TOKEN:
     - This secret already exists at the ORGANIZATION level
     - Do NOT create or modify this secret
     - Do NOT set it as a repository secret
     - It is automatically available to all repos in the org

4. Files that typically reference Shared-Technology-Group:
     - Workflow files that use reusable workflows from next-deployment-workflows
     - Workflow files that reference shared action definitions
     - The agent MUST scan each workflow file individually

5. Do NOT add the checkout step to files that do NOT reference
     Shared-Technology-Group repositories

This rule is NON-NEGOTIABLE for cross-org repositories.
Without it, ALL pipelines will fail with authentication errors.

## GITHUB ENVIRONMENT SCOPE & IDEMPOTENCY

- All GitHub Environments, secrets, and variables MUST be created
    ONLY in the TARGET repository where the agent is executed.
- The reference repository MUST NEVER be modified.
Environment handling rules:
1. Detect required environments from reference configuration.
2. For each required environment:
     - Check if the environment already exists in the TARGET repo.
     - If it exists:
         - DO NOT recreate it
         - DO NOT reset existing secrets or variables
     - If it does NOT exist:
         - Create the environment in the TARGET repo
3. Secrets and variables:
     - MUST be set ONLY in the TARGET repo environments
     - MUST be additive
     - MUST NOT overwrite existing values unless explicitly required
Any attempt to create or modify environments in the reference repo:
    → STOP immediately with error

## ENVIRONMENT REQUIRED REVIEWERS (POST-SETUP, MANDATORY)

Required reviewers are added AFTER all environments are created, all secrets and variables are written successfully, and all verifications pass. Reviewer assignment MUST NOT block environment creation.

### Scope

- Reviewers ARE applied to: production-grade environments (anything other than `devops-build`, `dev`, `tst`).
- Reviewers MUST NOT be applied to: `devops-build`, `dev`, `tst`.
- Existing environments MUST NOT be modified.
- Process environments sequentially. Verify after each assignment.

### Reviewer roster

Two reviewers per applicable environment:
1. The authenticated user (always required).
2. `svc-GitHub_aptean` service account (best-effort; warn-and-continue if unavailable).

### Service account setup (best-effort, resilient)

Add `svc-GitHub_aptean` as repository collaborator BEFORE assigning reviewers. Retry policy:

| Step | Command | On failure |
|---|---|---|
| 1. Add as admin | `gh api "repos/{owner}/{repo}/collaborators/svc-GitHub_aptean" -X PUT -f permission=admin` | Retry once. If still fails, try `permission=write`. If ALL attempts fail: log warning, mark svc unavailable, CONTINUE. |
| 2. Get numeric ID | `gh api "users/svc-GitHub_aptean" --jq .id` -> `$svcUserId` | Retry once. If retry fails: log warning, mark svc unavailable, CONTINUE. |

### Authenticated user resolution (mandatory automatic)

| Step | Command | Notes |
|---|---|---|
| 1. Username | `gh api user --jq .login` | Returns actual login (e.g. `hanirudh_aptean`, NOT `HAnirudh`). MUST complete without user interaction. |
| 2. Numeric ID | `gh api "users/$username" --jq .id` | Required - reviewers are assigned by numeric ID, not username. |
| 3. Fallback | `gh api repos/{owner}/{repo} --jq .owner.login` then `gh api "users/{owner-login}" --jq .id` | Used only if step 1/2 fails. |
| 4. Hard stop | If all above fail: STOP with clear error. The authenticated user is required. |

### Assignment payload (CRITICAL format)

Both reviewers MUST be specified by NUMERIC `id` with `type: "User"` (NEVER team, NEVER username string).

```powershell
$username = gh api user --jq .login
$userId = gh api "users/$username" --jq .id
$svcUserId = gh api "users/svc-GitHub_aptean" --jq .id
$json = "{`"reviewers`":[{`"type`":`"User`",`"id`":$userId},{`"type`":`"User`",`"id`":$svcUserId}]}"
$json | gh api "repos/{owner}/{repo}/environments/{env-name}" -X PUT --input -
```

Execution pattern (any deviation = execution failure):
- Construct JSON body in PowerShell.
- Pipe via stdin to `gh api --input -` (NEVER bash heredocs or redirection).
- Include `deployment_branch_policy = null`.
- Use `ConvertTo-Json` with sufficient depth.
- NEVER prompt the user for usernames or IDs.

If only the authenticated user is available (svc unavailable), assign just `$userId` and log a clear warning per environment.

### Per-environment loop

For EACH applicable environment:
1. Assign reviewer(s) per the payload above.
2. Verify reviewers were added.
3. If verification fails: retry ONCE. If still fails: log warning, CONTINUE to next environment (do NOT stop).

### Final reporting (MANDATORY)

- Check each environment for reviewers.
- Build a summary of reviewer status per environment.
- If any environment is missing a reviewer: log warning, include in the final summary, proceed to commit/PR.
- Reviewer failures are warnings - the agent MUST continue execution.

## MAINMANIFEST.YML GENERATION RULES (BLOCKING)

Reference files (from cloned reference repo):
- `templates/service/config/MainManifest.example.yml` (comprehensive example)
- `templates/service/config/manifest-schema.json` (JSON schema for validation)

### When to generate

| Existing file state | Action |
|---|---|
| `config/MainManifest.yml` exists | Do NOT overwrite, do NOT regenerate. Only add missing required configuration entries if absent. If no changes needed, skip. |
| `config/MainManifest.yml` does not exist | Read BOTH reference files. Create from scratch conforming to `manifest-schema.json`, following the patterns in the example. |

### Required structure

The generated file MUST include these sections:

**a) `manifestVersion: "1.0"`**

**b) `product`:**
- `name`: human-readable repo name
- `description`: brief description derived from repo inspection
- `iamDetails.code`: the IamCode (see iamDetails rules below)
- `repository.url`: target repository URL
- `repository.branch`: `main`
- `cloud`: `azure`
- `category`: one of `microservice | monolith | library | job` (detect from repo)
- `service-domain`: derived from repo context
- `audience`: one of `internal | external | partner`

**c) `infrastructure`:**
- `databases`: array of database declarations. Only `postgres` is currently supported. Each entry needs `name`, `type`, `sku` (per-environment sizing). Secrets auto-stored in infra Key Vault as `{app}-{name}-connection-string`, `-db-host`, `-db-username`, `-db-password`, `-db-name`.
- `storage`, `caching`, `messaging`: `[]` (FUTURE - not yet implemented).

**d) `deployments`:** array of Kubernetes workload declarations. Each entry MUST include:

| Field | Required value |
|---|---|
| `name` | deployment name (e.g. `ui`, `api`, `worker`) |
| `type` | `frontend` / `backend` (creates K8s Service, eligible for Ingress) / `worker` (no Service, no Ingress) / `cronjob` (K8s CronJob, no Service) |
| `port` | container port (1-65535) |
| `bgmEnabled` | true/false (blue-green deployment support) |
| `healthCheck` | `{ path, port, initialDelaySeconds, periodSeconds }` |
| `languages` | array of languages used (informational) |
| `capacity` | per-environment resource specs: `replicas: { min, max }` (HPA bounds), `resources: { cpu, cpuLimit, memory, memoryLimit }` |
| `configuration` | array of env vars: `{ name (UPPER_SNAKE_CASE), type: applicationConfig | applicationSecret, defaultValue (optional, applicationConfig only) }` |

**Configuration type rule:** ALL secret-type configuration entries MUST use type `applicationSecret`. The type `infrastructureSecret` MUST NOT be used. Infrastructure secrets (DB credentials, connection strings) are auto-managed by the platform via Key Vault and do NOT appear in the configuration array.

**e) `routing`:**
- `domains`: per-environment domain mapping. Use `{name}` placeholder for the lowercased `iamDetails.code` (e.g. `{name}.dev.apteanone.com`).
- `tls: true`.
- `routes`: path-based routing rules with `path`, `deployment`, optional `port`, optional `rewrite`.

**f) `dependencies`:**
- `internal: []` (internal service dependencies).
- `external: []` (external API dependencies).

### Repository scanning (MANDATORY when creating)

| Detect | How |
|---|---|
| Deployments | Typically `ui` (frontend) + `api` (backend). Microfrontend repos: each app is an additional deployment. Background services: add as `type: worker`. Inspect the repo structure to determine ALL deployments. Detect ports from Dockerfiles, `package.json`, or application configs. Detect health check paths from existing code. |
| Required configuration entries | EVERY deployment MUST include: `IAM_CLIENT_ID` (applicationConfig), `IAM_CLIENT_SECRET` (applicationSecret), `IAM_POID` (applicationConfig), `API_URL` (applicationConfig), `API_KEY` (applicationSecret). Add more entries based on what the repo code actually uses. |
| Infrastructure | Scan for database usage (PostgreSQL only). Look for connection strings, ORM configs, migration files. Storage/caching/messaging: empty arrays (FUTURE). If DBs cannot be determined with confidence: ask the user. |
| Routing | Determine paths from deployment types. Frontend typically gets `/{{ .ServiceName }}`. Backend typically gets `/{{ .ServiceName }}/api` with rewrite to `/`. |

### iamDetails.code rules

- ServiceName and `iamDetails.code` are the SAME identity (different case): code is ALL UPPERCASE (e.g. `PERSASST`, `CUSTMGMT`, `INDUSTRYHUB`); ServiceName is the same string lowercased.
- Alphabetic only (no numbers, no hyphens). 2-12 characters. Starts with a letter.
- MUST NOT exceed 12 characters (Azure Key Vault 24-char name limit constraint).
- Key Vault naming: `kv-{region}-{lower(iamDetails.code)}-{env}` (e.g. `kv-eus-persasst-tst`). Budget: `kv-` (3) + region (4) + code (2-12) + `-` (1) + env (3-4) <= 24.
- This is the ONLY file where ServiceName appears in uppercase.
- MUST be globally unique across all Aptean products to prevent Key Vault name collisions, Terraform state file conflicts (`{code}-{env}.tfstate`), and IAM product code conflicts in AppCentral.
- UNIQUENESS CHECK (mandatory before finalizing): `gh search code "iamDetails" --owner Shared-Technology-Group --owner Aptean-Labs`. If a collision is found, choose a different code.
- Avoid generic codes like `ASSIST`, `SERVICE`, `ADMIN`, `PORTAL`, `BACKEND`.
         Prefix with product domain for uniqueness (e.g., PERSASST not ASSIST).
