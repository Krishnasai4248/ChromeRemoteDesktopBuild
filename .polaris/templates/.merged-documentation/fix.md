---
description: Fix a bug from an Azure DevOps work item with full traceability, kanban progress tracking, and status write-back.
---
## Model Guidance

This command does planning work. Use **claude-opus-4-6** for this session.

Deep reasoning, synthesis, and decision-making here propagate to all downstream work. Opus-level reasoning is insurance, not indulgence.

If you are currently on Sonnet: switch to Opus before proceeding (`/model claude-opus-4-6`).

---


# /polaris.fix - Bug Fix from Azure DevOps Work Item

**Version**: 2026.3.0+
**Purpose**: Fix a bug sourced from Azure DevOps, with full traceability through polaris-specs.

## User Input

**Telemetry**: Run: `polaris telemetry record fix --feature <slug> --phase start --agent {{AGENT_NAME}}`


```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Quick Mode

If user passes `--quick` or arguments contain "quick":
1. Parse the bug ID from arguments (same formats as below)
2. Fetch the ADO/Jira work item details (title, description, repro steps, acceptance criteria)
3. If the work item has sufficient detail (title + description or repro steps): skip extended discovery and proceed directly to implementation using work item fields as the specification source
4. If the work item is missing key fields (no description AND no repro steps): fall back to normal discovery flow
5. All other phases (implementation, testing, kanban tracking, write-back) run normally

## Bug ID Parsing

Parse the bug ID from arguments. Supported formats:
- Numeric: `12345`
- Hash prefix: `#12345`
- AB prefix: `AB#12345`
- Full ADO URL: `https://dev.azure.com/{org}/{project}/_workitems/edit/12345`

Extract the numeric work item ID from any of these formats.

If no bug ID is provided, ask the user:
> "Please provide a bug ID. Accepted formats: `12345`, `#12345`, `AB#12345`, or a full Azure DevOps URL."

End with `WAITING_FOR_FIX_INPUT` and wait for a response.

## Failure Awareness (only if memory file exists)

Skip this section entirely if `.polaris/memory/failures-summary.md` does not exist.

If the file exists, check it for the error signature you're investigating before debugging. If a known fix exists, apply it first. After resolving a new bug, record the fix:
```bash
polaris memory resolve-failure --signature <first-8-chars> --resolution "<what fixed it>"
```

If the bug required an architectural decision and `decisions-summary.md` exists (or this is the first such decision worth keeping), also record:
```bash
polaris memory record-decision --context "<bug context>" --decision "<approach chosen>" --rationale "<why>" --tags bugfix --tags <area>
```

---

## Prerequisites

### Issue Tracker Token Pre-flight

Before fetching work items, validate that the required credentials are present. Check `.polaris/memory/constitution.md` for the configured issue tracker.

**Azure DevOps**: Requires `AZURE_DEVOPS_PAT` environment variable with **Work Items (Read)** scope.

```python
python -c "import os, sys; pat=os.environ.get('AZURE_DEVOPS_PAT','').strip(); sys.exit(0) if pat else (print('AZURE_DEVOPS_PAT not set. Create a PAT at https://dev.azure.com with Work Items (Read) scope:\n  export AZURE_DEVOPS_PAT=your-token-here'), sys.exit(1))"
```

**Jira**: Requires `JIRA_API_TOKEN` and `JIRA_EMAIL` environment variables, plus Jira URL from constitution.

```python
python -c "import os, sys; t=os.environ.get('JIRA_API_TOKEN','').strip(); e=os.environ.get('JIRA_EMAIL','').strip(); sys.exit(0) if (t and e) else (print('Jira credentials missing. Set both:\n  export JIRA_API_TOKEN=your-api-token\n  export JIRA_EMAIL=your-email@company.com\nGenerate token at: https://id.atlassian.net/manage-profile/security/api-tokens'), sys.exit(1))"
```

If the token check fails, print the guidance above, end with `WAITING_FOR_FIX_INPUT`, and wait.

### Issue Tracker Configuration

Read `.polaris/memory/constitution.md` and look for the issue tracker section:
- **Azure DevOps**: `## Azure DevOps` section with Organization URL and Default Project
- **Jira**: `## Jira` section with Base URL (e.g., `https://myorg.atlassian.net`) and Default Project Key

If the issue tracker section is missing from the constitution:
> "Issue tracker configuration not found in `.polaris/memory/constitution.md`.
>
> Please either:
> - Run `/polaris.setup` (or `/polaris.constitution`) to add issue tracker config
> - Or provide the details now (ADO: org URL + project name; Jira: base URL + project key)"

End with `WAITING_FOR_FIX_INPUT` and wait.

## Workflow

### Step 1: Fetch Work Item from Azure DevOps

Call the ADO REST API:

```bash
python -c "
import json, os, sys, urllib.request, base64
pat = os.environ['AZURE_DEVOPS_PAT']
org_url = '{ORG_URL}'
project = '{PROJECT}'
work_item_id = {WORK_ITEM_ID}
url = f'{org_url}/{project}/_apis/wit/workitems/{work_item_id}?api-version=7.0'
auth = base64.b64encode(f':{pat}'.encode()).decode()
req = urllib.request.Request(url, headers={'Authorization': f'Basic {auth}'})
try:
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    fields = data.get('fields', {})
    print(json.dumps({
        'id': data['id'],
        'title': fields.get('System.Title', ''),
        'type': fields.get('System.WorkItemType', ''),
        'state': fields.get('System.State', ''),
        'description': fields.get('System.Description', ''),
        'repro_steps': fields.get('Microsoft.VSTS.TCM.ReproSteps', ''),
        'acceptance_criteria': fields.get('Microsoft.VSTS.Common.AcceptanceCriteria', ''),
        'assigned_to': fields.get('System.AssignedTo', {}).get('displayName', ''),
        'area_path': fields.get('System.AreaPath', ''),
        'iteration_path': fields.get('System.IterationPath', ''),
        'severity': fields.get('Microsoft.VSTS.Common.Severity', ''),
        'priority': fields.get('Microsoft.VSTS.Common.Priority', 0)
    }, indent=2))
except urllib.error.HTTPError as e:
    print(json.dumps({'error': f'HTTP {e.code}: {e.reason}', 'url': url}), file=sys.stderr)
    sys.exit(1)
"
```

**Error handling**:
- **404**: "Work item {id} not found in {project}. Verify the ID and project name."
- **401/403**: "Authentication failed. Check your AZURE_DEVOPS_PAT token."
- **Network error**: "Cannot reach Azure DevOps. Check your network connection."

**Non-Bug work item type**: If the work item type is not "Bug", warn:
> "Work item {id} is a '{type}', not a Bug. Proceeding anyway - the fix workflow works for any work item type."

### Step 2: Create Branch

Capture the base branch first (used as `target_branch` in meta.json):

```bash
git branch --show-current
```

Store the output as `{base_branch}` (e.g., `main`).

Then create and switch to the fix branch:

```bash
git checkout -b fix/{id}-{kebab-title}
```

Verify branch: run `git branch --show-current`. Must show `fix/{id}-{kebab-title}`, NOT `main`/`master`. If still on main/master: STOP - branch creation failed. Do not proceed until confirmed on the fix branch.

### Step 3: Create Mini Polaris-Specs Entry

Now on the fix branch, create a polaris-specs entry for traceability:

```bash
polaris agent feature create-feature "fix-{id}-{kebab-title}" --json
```

Where `{kebab-title}` is the work item title converted to kebab-case (max 50 chars, truncated at word boundary).

Parse the JSON output for `feature` and `feature_dir`.

Create `spec.md` in the feature directory with the bug details:

```markdown
# Fix: {title}

**Source**: Azure DevOps Work Item [AB#{id}]({org_url}/{project}/_workitems/edit/{id})
**Type**: {type}
**Severity**: {severity}
**Priority**: {priority}
**State**: {state}

## Description

{description from ADO}

## Reproduction Steps

{repro_steps from ADO, or "Not provided" if empty}

## Acceptance Criteria

{acceptance_criteria from ADO, or "Bug is resolved and verified" if empty}

## Scope

- Fix the reported bug
- Add or update tests to prevent regression
- No unrelated changes
```

Create a single-WP `tasks.md`:

```markdown
# Tasks: fix-{id}-{kebab-title}

## Work Packages

### WP01 - Fix Bug AB#{id}

Fix the reported bug, add regression tests, verify the fix.
```

Create `meta.json` using `{base_branch}` captured before the branch switch:

```json
{
  "feature_number": "<number>",
  "slug": "fix-{id}-{kebab-title}",
  "friendly_name": "Fix: {title}",
  "mission": "software-dev",
  "source_description": "Azure DevOps Bug AB#{id}: {title}",
  "created_at": "<ISO timestamp>",
  "target_branch": "{base_branch}",
  "vcs": "git",
  "ado_work_item": {
    "id": {id},
    "type": "{type}",
    "url": "{org_url}/{project}/_workitems/edit/{id}"
  }
}
```

### Step 3.5: Update Work Item Status

Update the ADO work item to "Active" to signal investigation has started:

```bash
python -c "
import json, os, sys, urllib.request, base64
pat = os.environ['AZURE_DEVOPS_PAT']
org_url = '{ORG_URL}'
project = '{PROJECT}'
work_item_id = {WORK_ITEM_ID}
url = f'{org_url}/{project}/_apis/wit/workitems/{work_item_id}?api-version=7.0'
auth = base64.b64encode(f':{pat}'.encode()).decode()
patch = json.dumps([
    {'op': 'add', 'path': '/fields/System.State', 'value': 'Active'},
    {'op': 'add', 'path': '/fields/System.History', 'value': 'Polaris fix workflow started. Branch: fix/{id}-{kebab-title}'}
]).encode()
req = urllib.request.Request(url, data=patch, method='PATCH',
    headers={'Authorization': f'Basic {auth}', 'Content-Type': 'application/json-patch+json'})
try:
    resp = urllib.request.urlopen(req)
    print('Work item updated to Active')
except Exception as e:
    print(f'Warning: Could not update work item: {e}', file=sys.stderr)
"
```

If the update fails (permissions, network), log a warning but continue - the fix itself is more important than the status update.

### Step 4: Implement Fix

1. **Locate relevant code**: Use the bug description, repro steps, and area path to find the relevant files
2. **Understand the bug**: Read the code, understand the root cause
3. **Implement the fix**: Make minimal, focused changes to fix the bug
4. **Write/update tests**: Add regression tests that would have caught this bug

### Step 5: Run Tests

```bash
python .polaris/scripts/tasks/run_tests.py --project-root . --json
```

Parse JSON output. If tests fail:
- Read the `output` field for failure details
- Fix the failing tests or the code causing failures
- Re-run tests (max 3 retry attempts)

If tests pass, proceed.

### Step 6: Commit

```bash
git add <changed-files>
git commit -m "fix: {title} (AB#{id})"
```

The commit message references the ADO work item for traceability.

### Step 7: Post-Fix Regression

Check for cascading breakage:

- Feature context (slug from branch or arguments):
  `polaris runtests --feature <slug>`
- Standalone fix (no feature context):
  `python .polaris/scripts/tasks/run_tests.py --project-root . --json`
- If tests fail, fix breakage before completing.

### Step 8: Show Progress

Display the current fix progress:

```bash
polaris agent tasks status --feature fix-{id}-{kebab-title}
```

### Step 9: Move to Review

```bash
polaris agent tasks move-task WP01 --to testing --feature fix-{id}-{kebab-title}
polaris agent tasks move-task WP01 --to for_review --feature fix-{id}-{kebab-title}
```

### Step 10: Update Work Item - Fix Complete

Update the ADO work item with fix details:

```bash
python -c "
import json, os, sys, urllib.request, base64
pat = os.environ.get('AZURE_DEVOPS_PAT', '')
if not pat:
    print('Skipping ADO update: AZURE_DEVOPS_PAT not set')
    sys.exit(0)
org_url = '{ORG_URL}'
project = '{PROJECT}'
work_item_id = {WORK_ITEM_ID}
url = f'{org_url}/{project}/_apis/wit/workitems/{work_item_id}?api-version=7.0'
auth = base64.b64encode(f':{pat}'.encode()).decode()
patch = json.dumps([
    {'op': 'add', 'path': '/fields/System.State', 'value': 'Resolved'},
    {'op': 'add', 'path': '/fields/System.History',
     'value': 'Fix implemented and tests passing. Branch: fix/{id}-{kebab-title}. Awaiting review.'}
]).encode()
req = urllib.request.Request(url, data=patch, method='PATCH',
    headers={'Authorization': f'Basic {auth}', 'Content-Type': 'application/json-patch+json'})
try:
    resp = urllib.request.urlopen(req)
    print('Work item updated to Resolved')
except Exception as e:
    print(f'Warning: Could not update work item: {e}', file=sys.stderr)
"
```

### Step 11: Summary

Display a summary:

```
Bug Fix Complete: AB#{id} - {title}
  Branch:  fix/{id}-{kebab-title}
  Files:   {count} files changed
  Tests:   {passed}/{total} passed
  Commit:  {short-hash} fix: {title} (AB#{id})

Next steps:
  1. Push the branch: git push -u origin fix/{id}-{kebab-title}
  2. Create a PR: gh pr create --title "fix: {title} (AB#{id})"
  3. Or use /polaris.ship to review, accept, and merge
```

**Files to commit vs gitignore**: If untracked `.polaris/` files exist after the fix:
- **Commit**: polaris-specs/ entries, .polaris/config.yaml, .polaris/memory/, .polaris/workspaces/
- **Gitignore**: .polaris/.dashboard, .polaris/telemetry/, .polaris/autopilot-state.json

## Cross-Platform Notes

All commands used here are Polaris CLI commands, Python one-liners, or git operations that work on Windows, macOS, and Linux. No shell-specific commands are used.


**Telemetry**: Run: `polaris telemetry record fix --feature <slug> --phase complete --agent {{AGENT_NAME}}`
