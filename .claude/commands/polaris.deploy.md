---
description: Trigger CI/CD pipelines to deploy a service to dev/tst environments.
---


## User Input

**Telemetry**: Run: `polaris telemetry record deploy --feature <slug> --phase start --agent claude`

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).
Parse environment from arguments: `dev` (default), `tst`, or `all`.

---

## Pre-flight Checks

### Step 1 - Load Skill Rules (BLOCKING)

Read `.polaris/skills/devops-pipeline.skill.md` for cross-cutting invariants (APP CONFIG SCOPING, SERVICE NAMING, MAINMANIFEST GENERATION RULES, etc.) that apply during deploy operations.

The deploy-phase procedural rules (PIPELINE TRIGGER, KEYVAULT HELM VALUES UPDATE, PR AUTO-MERGE) are inlined directly in this template (see the rules blocks below). The agent MUST follow them as written.

If skill file is missing, HALT with:
```
ERROR: Required skill file missing: devops-pipeline.skill.md
Run `polaris upgrade` to deploy skill files, then retry /polaris.deploy.
```

Do NOT proceed until skill rules are loaded.

---

## PR Auto-Merge Rules (DEPLOY PHASE)

Used by Step 6 below. These rules govern how the agent safely auto-merges the devops scaffolding PR before triggering pipelines.

**Pre-merge validation (MANDATORY):**
1. Verify the PR exists and is open: `gh pr view <number> --json state --jq .state`
2. Verify the PR contains only infrastructure files. Allowed paths: `.github/workflows/*.yml`, `helm/**`, `infrastructure/**`, `manage-appConfig-secrets/**`, `config/MainManifest.yml`, Dockerfile fixes. If the PR contains application source code changes: STOP with "PR contains non-infrastructure changes. Please review and merge manually."
3. Verify the PR was created by the devops scaffolding (branch matches `feature-*-devops` or `automation/scaffold-pipelines`). If not, warn but allow (user may have renamed the branch).

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
- Do NOT use `--delete-branch` (keep the branch for reference).
- The agent MUST NOT force-merge or bypass branch protection.

---

## Pipeline Trigger Rules (DEPLOY PHASE)

Used by every `gh workflow run` call in Steps 7 and 8 below.

**Trigger pattern:** `gh workflow run "<workflow-file>.yml" [-f <input>=<value>]`

| Workflow | Command | Cardinality |
|---|---|---|
| Build | `gh workflow run "docker-build-push-<ServiceName>.yml"` | Once, env-agnostic |
| Infra | `gh workflow run "infra.<ServiceName>.deploy.yml" -f environments=<env>` | Per environment |
| Helm | `gh workflow run "helm.<ServiceName>.deploy.yml" -f environments=<env>` | Per environment |

**Polling for run completion (MANDATORY after every trigger):**
1. After triggering, wait 5 seconds before polling for run ID (GitHub needs time to register).
2. Poll: `gh run list --workflow "<workflow-file>.yml" --limit 1 --json databaseId,status --jq ".[0]"`
3. If no run ID found: retry up to 6 times with 10-second intervals.
4. Once run ID obtained, watch until NATURAL completion: `gh run watch <run-id>`. Do NOT set an artificial timeout.
5. Check the exit code of `gh run watch`:
   - Exit code 0: pipeline SUCCEEDED. Move to the next step IMMEDIATELY.
   - Non-zero: pipeline FAILED. See failure handling below.

**Completion detection (CRITICAL):**
- When `gh run watch` exits with code 0, the pipeline is DONE. The agent MUST trust the exit code as the definitive signal.
- Do NOT re-trigger the same workflow after success.
- Do NOT poll `gh run list` again after a successful watch.
- Do NOT re-check status. Mark the step completed and proceed.

**Failure handling:**
- On non-zero exit: display "Pipeline <name> failed.", display the run URL, ask "Retry this step? (Yes/No)". If Yes: re-trigger from step 1 above. If No: stop deployment and report which steps completed.

**Step tracking (MANDATORY):**
- Maintain `[build, infra-dev, keyvault-dev, helm-dev, infra-tst, keyvault-tst, helm-tst]`.
- On retry, skip all steps already marked completed.
- The build step completes ONCE for all environments.
- A step is marked completed the moment `gh run watch` exits with code 0.
- NEVER re-execute a step that is already marked completed.

**Execution order (STRICT):**
1. `docker-build-push-<ServiceName>.yml` (once, env-agnostic)
2. `infra.<ServiceName>.deploy.yml` (per environment)
3. KeyVault update (per environment, not a pipeline)
4. `helm.<ServiceName>.deploy.yml` (per environment)

Steps 2-4 repeat for each environment. The agent MUST NOT start step N+1 until step N succeeds.

**Environment ordering (STRICT):**
- dev MUST complete fully (infra + keyvault + helm) before tst is offered.
- The agent MUST NOT deploy to tst before dev succeeds.
- After dev completes, ask: "Deploy to QA (tst)? (Yes/No)".
- If the user passes `all`: deploy dev then tst without prompting.

---

## KeyVault Helm Values Update Rules (DEPLOY PHASE)

Used by Step 8b below. The agent does NOT call `az` locally. Instead it
triggers the central **Update Helm Values DATABASE_URL** workflow at
`Aptean-Labs/polaris-devops`, which authenticates as the per-environment
Service Principal and updates the helm-values secret in the env's Key
Vault. The agent MUST NOT ask the user for the connection string and MUST
NOT display it.

**Trigger pattern:**

```
gh workflow run update-helm-values.yml \
  -R Aptean-Labs/polaris-devops \
  -f target_owner=<owner> \
  -f target_repo=<repo> \
  -f service_name=<ServiceName> \
  -f environment=<env>
```

`<owner>` and `<repo>` come from `gh repo view --json owner,name`.
`<ServiceName>` comes from Step 2 (the build pipeline filename pattern).
`<env>` is `dev`, `tst`, or `prd-a` (matching the current deploy iteration).

**What the workflow does (informational; the agent does not need to know
the internals):**

1. Logs into Azure as the per-env SPN (`<PFX>_AZURE_CREDENTIAL_AUTOMATION`,
   org-level secret in Aptean-Labs).
2. Reads the postgres connection-string template from the per-env vault
   (`<PFX>_AZURE_KEYVAULT_URL` selects the vault; the secret name is
   `vars.POSTGRES_TEMPLATE_SECRET_NAME` on `polaris-devops`, typically
   `postgres-master-template`).
3. Substitutes `{db-name}` -> `<ServiceName>-db-<env>`.
4. Reads the existing `helm-values-<ServiceName>-eastus-<env>` secret in
   the same vault (creates if absent), merges `DATABASE_URL` into the
   YAML, preserves all other fields, writes back.

**Polling and watching (MANDATORY after every trigger):**

1. Wait 5 seconds, then resolve the run ID:
   ```
   gh run list --workflow update-helm-values.yml \
     --repo Aptean-Labs/polaris-devops \
     --limit 1 --json databaseId --jq ".[0].databaseId"
   ```
   If no run ID, retry up to 3 times with 5-second intervals.

2. Watch:
   ```
   gh run watch <run-id> --repo Aptean-Labs/polaris-devops
   ```

3. On non-zero exit, fetch logs and surface them:
   ```
   gh run view <run-id> --log-failed --repo Aptean-Labs/polaris-devops
   ```
   Then STOP with the run URL. Do NOT retry automatically. Common causes:
   missing org secret, missing repo secret, missing repo variable
   (`POSTGRES_TEMPLATE_SECRET_NAME`), SPN lacks Secrets Officer role on
   the env's vault. None are fixable from the agent.

**Security rules (CRITICAL):**

- The agent MUST NOT display the connection string. The workflow runner
  masks it with `::add-mask::`; the agent never sees it either.
- The agent MUST NOT log the resolved DATABASE_URL.
- The agent MAY display: "DATABASE_URL resolved and updated for <env> via
  central workflow run #<run-id>".

**Preservation rules:**

The workflow's merge step preserves every existing field in the
helm-values secret and only adds or updates `DATABASE_URL`. The agent
does not need to enforce this; the workflow does.

**Failure modes the agent surfaces (does NOT auto-fix):**

- Workflow run fails with `Repo variable 'POSTGRES_TEMPLATE_SECRET_NAME' is not set` -> platform team fixes polaris-devops repo variables.
- Workflow run fails with `Repo secret '<PFX>_AZURE_KEYVAULT_URL' is missing` -> platform team fixes polaris-devops repo secrets.
- Workflow run fails with `Failed to read template secret` -> SPN lacks Secrets User on the env vault, or the template secret does not exist yet. Platform team fixes RBAC and/or creates the secret.
- Workflow run fails with `Failed to write helm-values secret` -> SPN lacks Secrets Officer on the env vault. Platform team fixes RBAC.
- Workflow run fails with `Template ... does not contain the {db-name} placeholder` -> the template secret in the env vault was set incorrectly. Platform team re-creates the secret with the correct format.

### Step 2 - Detect ServiceName

Scan `.github/workflows/` for files matching `docker-build-push-*.yml`.
Extract ServiceName from the filename pattern.

Example: `docker-build-push-simpleapp.yml` -> ServiceName = `simpleapp`

If no matching workflow found, check if there is an open PR from a devops branch
that contains workflow files (the PR may not be merged yet):
- Run: `gh pr list --state open --json number,headRefName,title --jq '.[] | select(.headRefName | test("devops|scaffold"))'`
- If an open PR is found: display the PR info and proceed to Step 5 (PR merge)
- If no PR found either: STOP with error:
  ```
  No build pipeline found in .github/workflows/ and no pending devops PR.
  Run /polaris.devops first to scaffold CI/CD pipelines.
  ```

If multiple matching workflows found: list them and ask user to select.

### Step 3 - Detect repository

Run: `gh repo view --json nameWithOwner --jq .nameWithOwner`

Parse owner and repo name. If this fails: STOP with error about GitHub CLI.

### Step 4 - Verify authentication

Verify GitHub CLI:
Run: `gh auth status`
If not authenticated: STOP with "GitHub CLI not authenticated. Run `gh auth login` first."

Azure CLI is NOT required by this command. All Azure-touching work runs
inside GitHub Actions:
- Deploy pipelines (build, infra, helm) authenticate as the runtime SPN
  using the `AZURE_CREDENTIAL_AUTOMATION` env-level secret that was
  populated by the Polaris Bootstrap workflow during `/polaris.devops`.
- The DATABASE_URL update (Step 8b below) triggers the central
  `update-helm-values.yml` workflow at `Aptean-Labs/polaris-devops`,
  which logs in as the per-env SPN and updates the helm-values secret in
  the env's Key Vault.

The agent on the laptop only uses `gh` (GitHub CLI) to trigger workflows
and watch their runs. The developer never needs Azure CLI installed or
personal Azure access for any step in this command.

---

## Step 5 - Ensure code is committed, pushed, and on main

**5a. Check for uncommitted changes:**

Run: `git status --porcelain`

If there are uncommitted changes (output is not empty):
- Display: "Uncommitted changes detected. Committing for deployment..."
- Stage all changes: `git add -A`
- Commit: `git commit -m "chore: prepare for deployment"`
- Display: "Changes committed."

**5b. Check current branch:**

Run: `git branch --show-current`

If NOT on main (or the default branch):
- Check if there are commits ahead of main: `git log main..HEAD --oneline`
- If commits exist on the feature branch:
  - Push the current branch: `git push origin <branch-name>`
  - Check if a PR exists for this branch: `gh pr list --head <branch-name> --state open --json number --jq '.[0].number'`
  - If no PR exists: create one: `gh pr create --base main --head <branch-name> --title "Deploy code changes" --body "Auto-created by /polaris.deploy for deployment."`
  - Merge the PR: `gh pr merge <number> --squash`
  - Switch to main: `git checkout main && git pull`
  - Display: "Code merged to main."
- If no commits ahead of main: just switch to main: `git checkout main && git pull`

If already on main:
- Check for unpushed commits: `git log origin/main..HEAD --oneline`
- If unpushed commits exist: push them: `git push origin main`
- Display: "Code is up to date on main."

---

## Step 6 - Detect and merge open devops PR (if needed)


Check if workflow files exist on the default branch:
`gh api repos/{owner}/{repo}/contents/.github/workflows/docker-build-push-<ServiceName>.yml --jq .name 2>/dev/null`

If workflow files already exist on the default branch: skip this step (PR already merged or workflows were added directly). Proceed to Step 7.

If workflow files do NOT exist on the default branch:

1. Search for open PRs from the devops scaffolding (sorted by newest first):
   `gh pr list --state open --json number,headRefName,title,createdAt --jq '[.[] | select(.headRefName | test("devops|scaffold"))] | sort_by(.createdAt) | reverse'`
   This filters for PRs with branch names containing "devops" or "scaffold" and sorts newest first.

2. If exactly ONE matching PR is found:
   Display: "Found open PR #<number>: <title>. Workflow files must be on the default branch before pipelines can be triggered."
   Ask: "Merge PR #<number> to enable deployment? (Yes/No)"

3. If MULTIPLE matching PRs are found:
   Display all matches in a numbered list:
   ```
   Multiple devops PRs found:
     1. PR #<number> - <title> (created <date>) [LATEST]
     2. PR #<number> - <title> (created <date>)
     3. PR #<number> - <title> (created <date>)
   ```
   Recommend the latest one (item 1).
   Ask: "Which PR should be merged? Enter the number (1-N), or 'skip' to merge manually."
   Use the selected PR for the merge step.

4. If a PR is selected for merge:
   Follow the **PR Auto-Merge Rules** section above.
   - Merge: `gh pr merge <number> --squash`
   - Wait 5 seconds for GitHub propagation
   - Verify workflow files now exist on default branch
   - If merge fails: display error with instructions and STOP

5. If no matching PRs found and workflows not on default branch:
   STOP with "Workflow files not found on default branch and no open devops PR. Run /polaris.devops first."

---

## BGM Detection

Scan `.github/workflows/` for files matching `bgm.*.deploy.yml` or `bgm.*.swap.yml`.

If found, display:
```
Note: This repository uses Blue-Green (BGM) deployment. BGM automated
deployment is not supported in this version. Standard deployment will
proceed. Trigger BGM workflows manually from GitHub Actions after completion.
```

Continue with standard deployment regardless.

---

## Failure Recovery

The agent MUST track completed pipeline steps throughout execution.
Completed steps: [build, infra-dev, keyvault-dev, helm-dev, infra-tst, keyvault-tst, helm-tst]

On any pipeline failure:
1. Display: "Step '<step-name>' failed. Run URL: <url>"
2. Ask: "Retry this step? (Yes/No)"
3. If Yes: re-run only the failed step, then continue from there
4. If No: display summary of completed vs. remaining steps and STOP

Previously completed steps are NEVER re-executed.
The build step is completed once for all environments.

---

## Execution

Follow the **Pipeline Trigger Rules** section above for every `gh workflow run` call below.

### Step 7 - Trigger build pipeline

1. Trigger: `gh workflow run "docker-build-push-<ServiceName>.yml"`
2. Wait 5 seconds, then poll for run ID:
   `gh run list --workflow "docker-build-push-<ServiceName>.yml" --limit 1 --json databaseId --jq ".[0].databaseId"`
3. Watch until completion: `gh run watch <run-id>`
4. If failed: display run URL, offer retry (see Failure Recovery above)
5. If succeeded: mark "build" as completed

The build runs ONCE regardless of how many environments will be deployed.

### Step 8 - Deploy to environment

Determine the deployment mode based on Step 5:
- If Step 6 merged a devops PR: this is a **first-time deployment**. Run all sub-steps (8a, 8b, 8c).
- If Step 6 was skipped (workflows already on main): this is a **re-deployment after code changes**. Skip 8a (infra) and 8b (keyvault), run only 8c (helm deploy). Infrastructure and DATABASE_URL are already configured from the first deployment.

For each target environment (dev first, then tst if requested):

**8a. Trigger infrastructure pipeline (FIRST-TIME ONLY - skip for re-deployments):**

`gh workflow run "infra.<ServiceName>.deploy.yml" -f environments=<env>`

Wait for completion. If failed: offer retry. Mark "infra-<env>" as completed.

**8b. Update DATABASE_URL in KeyVault (FIRST-TIME ONLY - skip for re-deployments):**

Follow the **KeyVault Helm Values Update Rules** section above. The agent
does NOT call `az` locally and does NOT need Azure access. The agent
triggers the central workflow and watches its run.

1. Determine `<owner>` and `<repo>` from `gh repo view --json owner,name`.

2. Trigger the central update-helm-values workflow:
   ```
   gh workflow run update-helm-values.yml \
     -R Aptean-Labs/polaris-devops \
     -f target_owner=<owner> \
     -f target_repo=<repo> \
     -f service_name=<ServiceName> \
     -f environment=<env>
   ```

3. Wait 5 seconds, then resolve the run ID:
   ```
   gh run list --workflow update-helm-values.yml \
     --repo Aptean-Labs/polaris-devops \
     --limit 1 --json databaseId --jq ".[0].databaseId"
   ```
   Retry up to 3 times with 5-second intervals if no run ID returned.

4. Watch the run until it finishes:
   ```
   gh run watch <run-id> --repo Aptean-Labs/polaris-devops
   ```

5. On non-zero exit code:
   - Fetch logs: `gh run view <run-id> --log-failed --repo Aptean-Labs/polaris-devops`
   - STOP with: "Update Helm Values workflow failed. Run URL printed above. Common causes: SPN missing Key Vault role, template secret missing in the env vault, repo variable POSTGRES_TEMPLATE_SECRET_NAME not set, repo secret <PFX>_AZURE_KEYVAULT_URL not set. Contact the platform team."
   - Do NOT retry automatically.

6. On success: display "DATABASE_URL resolved and updated for <env> environment via run #<run-id>". The agent does NOT see and does NOT log the connection string itself; the workflow handles it inside the cloud runner.

7. Mark "keyvault-<env>" as completed.

**8c. Trigger helm deploy pipeline (ALWAYS - both first-time and re-deployments):**

`gh workflow run "helm.<ServiceName>.deploy.yml" -f environments=<env>`

If the workflow does not accept an `environments` input (external dependency not yet applied):
trigger without the parameter: `gh workflow run "helm.<ServiceName>.deploy.yml"`
and warn: "Helm workflow deploys to all environments. Per-environment control
requires updating the reference repo template."

Wait for completion. If failed: offer retry. Mark "helm-<env>" as completed.

### Step 9 - Environment progression

Based on the user input argument:

- `dev` (default): Deploy to dev only. After success, ask:
  "Dev deployed successfully. Deploy to QA (tst)? (Yes/No)"
  If Yes: repeat Step 8 for tst.
  If No: display summary and STOP.

- `tst`: Deploy to dev first (if not already deployed to dev). Then deploy to tst.
  The agent MUST verify dev is deployed before proceeding to tst.
  If dev deployment status cannot be determined: deploy to dev first.

- `all`: Deploy to dev, then automatically to tst (no prompt between environments).

Environment ordering is STRICT: dev MUST complete fully before tst begins.

### Step 10 - Display summary

```
DEPLOY SUMMARY:
  Service: <ServiceName>
  Repository: <owner>/<repo>
  PR Merge: Merged PR #<number> / Already merged
  Build: Completed (run #<id>)
  Dev:
    Infrastructure: Completed/Skipped (run #<id>)
    KeyVault: DATABASE_URL updated/skipped
    Helm Deploy: Completed/Skipped (run #<id>)
  QA (tst):
    Infrastructure: Completed/Skipped (run #<id>)
    KeyVault: DATABASE_URL updated/skipped
    Helm Deploy: Completed/Skipped (run #<id>)

Service is live. Check environment URLs in GitHub Actions run output.
```

**Telemetry**: Run: `polaris telemetry record deploy --feature <slug> --phase complete --agent claude`

