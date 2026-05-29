# Ship - ACR Flow Detail

Full ACR (Azure Container Apps) deployment procedure for `/polaris.ship`.

## Step 2A.0 - Pre-flight

- `gh auth status` - stop if not authenticated
- `az account show` - stop if not authenticated
- `gh repo view --json defaultBranchRef --jq .defaultBranchRef.name` -> `<default-branch>`

## Step 2A.0b - Branch and uncommitted changes

- `git branch --show-current` -> `<current-branch>`
- `git status --porcelain` - if dirty: `git add -A && git commit -m "chore: prepare for deployment"`
- Set `ON_DEFAULT=true` if `<current-branch>` == `<default-branch>`, else `false`

## Step 2A.1 - Detect state

- `gh api repos/{owner}/{repo}/contents/.github/workflows/scaffold.yml --jq .name 2>/dev/null`
- Found -> **REDEPLOY** (skip to 2A.6). Not found -> **FIRST_TIME**.

## Step 2A.2 - Clone template (FIRST_TIME)

Clone path: `python -c "import tempfile,os; print(os.path.join(tempfile.gettempdir(),'polaris-ship-clone'))"`

Pre-clone cleanup: `python -c "import shutil,pathlib,sys; p=pathlib.Path(sys.argv[1]); (shutil.rmtree(p) if p.exists() else None)" "$CLONE_DIR"`

Clone: `git clone --depth 1 --filter=blob:none https://github.com/Shared-Technology-Group/simple-app-template "$CLONE_DIR"`

Verify required paths exist: `.github/workflows/scaffold.yml`, `deploy-all.yml`, `deploy-infra.yml`, `deploy-container.yml`, `deploy-migrations.yml`, `Dockerfile`, `docker-entrypoint.sh`, `.dockerignore`, `.gitignore`, `Manifest/MainManifest.yml`, `infra/main.bicep`, `nginx/nginx.conf`, `scripts/PrepareForDeployment.ps1`, `scripts/scaffold.sh`, `docs`, `README.md`, `CLAUDE.md`.

If any missing: STOP and report. If auth error on clone: STOP and ask user to run `gh auth login`.

## Step 2A.3 - Detect backend/frontend (FIRST_TIME)

1. Use `./backend/` and `./frontend/` if both exist.
2. Otherwise scan top-level dirs (exclude `.git .github .polaris node_modules dist build infra nginx scripts docs Manifest apps helm migrations alembic`). Classify by `package.json` deps: backend = express/fastify/nest/koa/hapi; frontend = react/vite/next/vue/svelte or vite.config.*/next.config.*.
3. If ambiguous, ask user for paths.
4. Confirm with user before continuing.

## Step 2A.4 - Gather metadata (FIRST_TIME)

Ask for: `app_code` (lowercase alpha, 2-12 chars, not "simpleapp", regex `^[a-z][a-z0-9]{1,11}$`), `app_name`, `description`.

## Step 2A.5 - Restructure repo (FIRST_TIME)

1. `python -c "from pathlib import Path; Path('apps').mkdir(exist_ok=True)"`
2. `python -c "import shutil; shutil.move('<backend>', 'apps/backend')"`
3. `python -c "import shutil; shutil.move('<frontend>', 'apps/frontend')"`
4. Copy clone into repo, skipping `.git/`, `apps/`, `docs/`, `README.md`, `CLAUDE.md` (preserve user docs).
5. Delete clone dir.
6. Verify: `.github/workflows/scaffold.yml`, `deploy-all.yml`, `Dockerfile`, `apps/backend/`, `apps/frontend/` all exist.

## Step 2A.5b - Replace simpleapp references (FIRST_TIME)

Replace `simpleapp` with `<app_code>` in: `nginx/nginx.conf`, `Dockerfile`, `docker-entrypoint.sh`, `infra/main.bicep`, `.github/workflows/deploy-container.yml`, `.github/workflows/deploy-all.yml`, `Manifest/MainManifest.yml`.

Also update `Manifest/MainManifest.yml`: set `name`, `description`, repo `url`, deployment name.

Verify with `git grep -n "simpleapp" -- nginx/ Dockerfile docker-entrypoint.sh infra/main.bicep .github/workflows/deploy-container.yml .github/workflows/deploy-all.yml Manifest/MainManifest.yml || echo "OK"`. STOP if any matches remain.

## Step 2A.5c - Patch scaffold.sh (FIRST_TIME)

Add existence guard in `scripts/scaffold.sh` `patch()` function before `open(path)`:
```python
if not os.path.exists(path):
    print(f"  skip missing: {path}")
    return
```
Verify: `git grep -n "skip missing:" -- scripts/scaffold.sh` must return one match.

## Step 2A.5d - Detect DB and prune if absent (FIRST_TIME)

Detect: check `apps/backend/prisma/schema.prisma`, `package.json` for prisma/typeorm/pg/etc, `alembic.ini`, `manage.py`, `migrations/` dir.

If no DB detected:
1. Strip `product.infrastructure.databases` and `DATABASE_URL` config entries from `Manifest/MainManifest.yml`.
2. Gate `migrate` job in `deploy-container.yml`: add `if: hashFiles('apps/backend/prisma/schema.prisma') != ''`.
3. Gate `deploy` job: add `if: ${{ !cancelled() && needs.build.result == 'success' && needs.migrate.result != 'failure' }}`.
4. Verify with `git grep`: `databases:[]`, no `DATABASE_URL`, one `schema.prisma` hit, one `needs.build.result` hit.

## Step 2A.5e - Adopt Labs environment configuration (FIRST_TIME)

Overlay `infra/environments/Labs/{dev,tst,prd-a}.json` onto the root env files so all deploy workflows (`deploy-infra.yml`, `deploy-container.yml`, `deploy-migrations.yml`) target the Labs subscription, then remove the unused `Labs/` and `ApteanOneSubscription/` folders.

Pre-check (STOP if missing): `python -c "import pathlib,sys; p=pathlib.Path('infra/environments/Labs'); sys.exit(0 if p.is_dir() and any(p.glob('*.json')) else 1)"`. Failure means the cloned template predates the Labs/ folder. Report to user and ask them to update simple-app-template upstream before retrying.

Overlay and clean up:
`python -c "import shutil,pathlib; e=pathlib.Path('infra/environments'); l=e/'Labs'; o=e/'ApteanOneSubscription'; [shutil.copy2(f, e/f.name) for f in l.iterdir() if f.suffix=='.json']; shutil.rmtree(l); o.exists() and shutil.rmtree(o)"`

Verify (STOP on any failure, do not commit a partial state). The files are not yet staged, so use direct file reads rather than `git grep`:
1. `python -c "import pathlib,sys; t=pathlib.Path('infra/environments/dev.json').read_text(encoding='utf-8'); sys.exit(0 if 'rg-eastus2-rnd-labs' in t else 1)"` (dev.json overlaid).
2. `python -c "import pathlib,sys; t=pathlib.Path('infra/environments/tst.json').read_text(encoding='utf-8'); sys.exit(0 if 'rg-eastus2-rnd-labs' in t else 1)"` (tst.json overlaid).
3. Folders gone and root files intact: `python -c "import pathlib,sys; e=pathlib.Path('infra/environments'); sys.exit(0 if all((e/n).exists() for n in ('dev.json','tst.json','prd-a.json')) and not (e/'Labs').exists() and not (e/'ApteanOneSubscription').exists() else 1)"`.

Notes to surface to user:
- Prerequisite: the `AZURE_CREDENTIAL_AUTOMATION` service principal must have Contributor (or equivalent) RBAC on `rg-eastus2-rnd-labs` in subscription `1280894a-27b3-42ad-9cd7-ef71d1cd663f`. If a downstream deploy step returns 403, request access from Labs platform owners (this step cannot grant RBAC).
- `Labs/prd-a.json` is currently incomplete upstream (carries GWC values plus `TODO-REPLACE-WITH-SHARED-KV-NAME` and `TODO-REPLACE-WITH-SHARED-APPCONFIG-NAME` placeholders). Shipping to `dev` and `tst` is safe; `prd-a` will fail until the upstream file is fixed.

## Step 2A.6 - Commit and push (FIRST_TIME)

`git add -A && git commit -m "scaffold: adopt simple-app template"`

ON_DEFAULT=true: `git push origin <default-branch>` (STOP if rejected - do not force-push).
ON_DEFAULT=false: push branch, create PR via `gh pr create`, WAIT for user to confirm merge, then `git checkout <default-branch> && git pull`.

## Step 2A.6b - Pipeline failure auto-fix loop

Max 3 attempts per pipeline. On failure:
1. `gh run view <run-id> --log-failed > run-<run-id>.log 2>&1`
2. `gh run view <run-id> --json jobs,conclusion,displayTitle`
3. Classify failure:
   - **File/Manifest content**: fix file, commit, push, re-trigger
   - **Missing secret/variable** or **RBAC/permission** or **Missing Azure resource**: STOP with instructions, do not retry
   - **Transient** (429/timeout/network): wait 30s, re-trigger, do not edit files
   - **Unknown**: STOP with failing step, last 30 log lines, run URL
4. If attempt > 3: STOP with all attempt URLs, last fix applied, root cause recommendation.
5. Delete log files after use.

## Step 2A.7 - Trigger Scaffold New App (FIRST_TIME)

`gh workflow run scaffold.yml -f app_code=<app_code> -f app_name="<app_name>" -f description="<description>"`

Poll run ID (wait 5s): `gh run list --workflow scaffold.yml --limit 1 --json databaseId --jq ".[0].databaseId"`

Watch: `gh run watch <run-id>`. On failure: enter 2A.6b loop.

After success: `git pull origin <default-branch>`

## Step 2A.8 - Re-deploy prep (REDEPLOY)

Run `powershell -ExecutionPolicy Bypass -File scripts/PrepareForDeployment.ps1` (Windows) or `pwsh scripts/PrepareForDeployment.ps1` (macOS/Linux).

If no changes: skip commit. If changes: commit and push (same ON_DEFAULT branch/PR logic as 2A.6).

## Step 2A.9 - Trigger Deploy All

`gh workflow run deploy-all.yml -f environment=dev`

Poll run ID, watch, enter 2A.6b loop on failure.

## Step 2A.10 - Environment progression

- `dev` (default): after dev, ask user "Deploy to QA (tst)? (Yes/No)"
- `tst`: after dev, auto-proceed to tst
- `all`: after dev, auto-proceed to tst

Dev MUST complete before tst.

## Step 2A.11 - Summary

AppCentral URL map: dev -> `appcentral.dev.apteancloud.dev/<app_code>/`, tst -> `appcentral.qa.apteancloud.dev/<app_code>/`, prod -> `appcentral.aptean.com/<app_code>/`. For unknown envs, print "see GitHub Actions run summary".

Print SHIP SUMMARY with: repo, default branch, mode, app_code, scaffold run, per-env deploy run + public URL.
