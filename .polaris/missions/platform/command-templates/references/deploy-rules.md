# Deploy Phase Rules

## PR Auto-Merge Rules

Used by Step 6. Governs how the agent safely auto-merges the devops scaffolding PR before triggering pipelines.

**Pre-merge validation (MANDATORY):**
1. Verify PR exists and is open: `gh pr view <number> --json state --jq .state`
2. Verify PR contains only infrastructure files. Allowed: `.github/workflows/*.yml`, `helm/**`, `infrastructure/**`, `manage-appConfig-secrets/**`, `config/MainManifest.yml`, Dockerfile fixes. If PR contains application source code: STOP with "PR contains non-infrastructure changes. Please review and merge manually."
3. Verify PR was created by devops scaffolding (branch matches `feature-*-devops` or `automation/scaffold-pipelines`). If not: warn but allow.

**Merge command:** `gh pr merge <pr-number> --squash`

**Post-merge verification (MANDATORY):**
1. Wait 5 seconds for GitHub propagation.
2. Verify workflow files exist on default branch: `gh api repos/{owner}/{repo}/contents/.github/workflows/docker-build-push-<ServiceName>.yml --jq .name`
3. If verification fails: STOP with "Workflow files not found on default branch after merge."

**Merge failure handling:**
- Required reviewers -> "PR requires reviewer approval. Approve in GitHub then re-run /polaris.deploy."
- Branch protection -> "Branch protection prevents auto-merge. Merge the PR manually then re-run."
- Merge conflicts -> "PR has merge conflicts. Resolve conflicts and re-run."
- On ANY merge failure: do NOT proceed to pipeline triggering.

**Safety rules:**
- ONLY merge PRs created by `/polaris.devops`.
- Use `--squash` to keep main branch history clean.
- Do NOT use `--delete-branch`.
- MUST NOT force-merge or bypass branch protection.

---

## Pipeline Trigger Rules

Used by every `gh workflow run` call in Steps 7 and 8.

**Trigger pattern:** `gh workflow run "<workflow-file>.yml" [-f <input>=<value>]`

| Workflow | Command | Cardinality |
|---|---|---|
| Build | `gh workflow run "docker-build-push-<ServiceName>.yml"` | Once, env-agnostic |
| Infra | `gh workflow run "infra.<ServiceName>.deploy.yml" -f environments=<env>` | Per environment |
| Helm | `gh workflow run "helm.<ServiceName>.deploy.yml" -f environments=<env>` | Per environment |

**Polling for run completion (MANDATORY after every trigger):**
1. After triggering, wait 5 seconds before polling for run ID.
2. Poll: `gh run list --workflow "<workflow-file>.yml" --limit 1 --json databaseId,status --jq ".[0]"`
3. If no run ID found: retry up to 6 times with 10-second intervals.
4. Once run ID obtained, watch until NATURAL completion: `gh run watch <run-id>`. Do NOT set an artificial timeout.
5. Exit code 0: pipeline SUCCEEDED. Non-zero: pipeline FAILED.

**Completion detection (CRITICAL):**
- When `gh run watch` exits with code 0, the pipeline is DONE. Trust the exit code.
- Do NOT re-trigger after success. Do NOT poll again. Do NOT re-check status. Mark completed and proceed.

**Failure handling:**
- On non-zero exit: display "Pipeline <name> failed.", display run URL, ask "Retry this step? (Yes/No)". If Yes: re-trigger. If No: stop and report completed steps.

**Step tracking (MANDATORY):**
- Maintain `[build, infra-dev, keyvault-dev, helm-dev, infra-tst, keyvault-tst, helm-tst]`.
- On retry, skip all steps already marked completed.
- Build completes ONCE for all environments.
- NEVER re-execute a completed step.

**Execution order (STRICT):**
1. `docker-build-push-<ServiceName>.yml` (once)
2. `infra.<ServiceName>.deploy.yml` (per environment)
3. KeyVault update (per environment)
4. `helm.<ServiceName>.deploy.yml` (per environment)

Steps 2-4 repeat per environment. MUST NOT start N+1 until N succeeds.

**Environment ordering (STRICT):**
- dev MUST complete fully before tst is offered.
- After dev completes, ask: "Deploy to QA (tst)? (Yes/No)".
- If user passes `all`: deploy dev then tst without prompting.

---

## KeyVault Helm Values Update Rules

Used by Step 8b. Governs automatic resolution and write of `DATABASE_URL` into Azure Key Vault. MUST NOT ask user for connection string. MUST NOT display it.

**Target secret:**
- Vault: `akv-eastus-lwr-devops`
- Secret: `helm-values-<ServiceName>-eastus-<env>` (env = `dev` or `tst`)

**Source secret (DATABASE_URL template):**
- Vault: `kv-eastus-labs`
- Secret: `psql-eastus-rnd-apteanone-master`
- Contains: `postgresql://apteanone:<password>@psql-eastus-rnd-apteanone.postgres.database.azure.com:5432/{db-name}?sslmode=require`

**Auto-resolution sequence (MANDATORY):**
1. Read source: `az keyvault secret show --vault-name "kv-eastus-labs" --name "psql-eastus-rnd-apteanone-master" --query "value" -o tsv`
2. Construct database name: `<ServiceName>-db-<env>`
3. Replace `{db-name}` in template -> resolved DATABASE_URL
4. Read current target: `az keyvault secret show --vault-name "akv-eastus-lwr-devops" --name "helm-values-<ServiceName>-eastus-<env>" --query "value" -o tsv`
5. Parse as YAML, add/update `DATABASE_URL`. Preserve ALL existing fields and ordering.
6. Write back: `az keyvault secret set --vault-name "akv-eastus-lwr-devops" --name "helm-values-<ServiceName>-eastus-<env>" --value "<updated-yaml>"`

**Security rules (CRITICAL):**
- MUST NOT display the connection string.
- MUST NOT log the connection string.
- MUST NOT include in commit messages.
- MAY display: "DATABASE_URL resolved and updated for <env> environment".

**Preservation rules (CRITICAL):**
- Read current target BEFORE making any changes.
- MUST NOT remove, rename, or reorder existing fields.
- MUST NOT re-format YAML beyond adding the new field.
- If target secret does not exist: create with only `DATABASE_URL`.
- If `DATABASE_URL` already exists: update value, preserve everything else.

**Error handling:**
- Source vault inaccessible -> STOP: "Cannot access source Key Vault (kv-eastus-labs). Verify az login."
- Source secret missing -> STOP: "Source database connection string not found in kv-eastus-labs."
- Target vault inaccessible -> STOP: "Cannot access target Key Vault. Verify az login."
- Target secret 404 -> create new secret with only `DATABASE_URL`.
- Target secret write fails -> STOP (do NOT display the value).
