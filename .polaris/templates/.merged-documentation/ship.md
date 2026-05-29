---
description: Review, accept, and merge a completed feature.
---
## Model Guidance

This command does implementation work. Use **claude-sonnet-4-6** for this session.

Execution against a defined plan - this is where call volume lives and where savings compound.

---


# /polaris.ship - Ship Feature

**Version**: 2026.3.0+
**Purpose**: Composite command that chains the review, acceptance, and merge workflow for a completed feature.

## User Input

**Telemetry**: Run: `polaris telemetry record ship --feature <slug> --phase start --agent {{AGENT_NAME}}`


```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Workflow

### Step 1: Review (`/polaris.review`)

Review all completed work packages:
- For each WP in the feature, run the structured review process
- Check code quality, test coverage, and acceptance criteria
- Move reviewed WPs to `for_review` lane: `polaris agent tasks move-task <WP_ID> --to for_review`

**On review issues**: If a WP fails review:
- List the specific issues found
- Ask the user whether to fix now or skip and continue reviewing other WPs
- If fixing: apply fixes, re-run review for that WP
- If skipping: note the WP as needing rework and continue

### Step 2: Accept (`/polaris.accept`)

Validate feature completeness:
- Verify all WPs have passed review (or are explicitly deferred)
- Run acceptance validation against the feature spec
- Check that all success criteria and acceptance scenarios are met
- Generate acceptance results

**On acceptance failure**: Report blockers and suggest remediation steps.

### Step 3: Merge (`/polaris.merge`)

Merge the accepted feature:
- Run preflight validation (clean worktrees, target branch up to date)
- Merge all WPs in dependency order to the target branch
- Clean up worktrees after successful merge
- Report merge results

**On merge conflicts**: Report the conflicting files and WPs, then ask the user how to proceed.

### Step 4: Clean Up Generated Files

After merge, guide the user on which files to commit vs gitignore:

**Commit these** (shared team artifacts):
- `polaris-specs/` (all files) - feature specs, tasks, plans
- `.polaris/config.yaml`, `.polaris/metadata.yaml`, `.polaris/AGENTS.md`
- `.polaris/memory/` - shared project knowledge including constitution
- `.polaris/missions/`, `.polaris/scripts/`, `.polaris/skills/`
- `.polaris/workspaces/` - WP state for team visibility
- `.polaris/reports/*.pdf` - quality certificates and release notes

**Gitignore these** (runtime state - do NOT commit):
- `.polaris/.dashboard` - runtime dashboard state
- `.polaris/telemetry/` - telemetry data
- `.polaris/autopilot-state.json` and `.polaris/autopilot-state.json.bak`
- `.polaris/merge-state.json` - transient merge state

If the user has untracked `.polaris/` files, check against this table and advise accordingly.

### Step 5: Work Item Write-back

If the feature's `meta.json` contains a work item link:
- **ADO** (`ado_work_item`): Post comment via ADO REST API using `AZURE_DEVOPS_PAT`:
  POST `{org_url}/{project}/_apis/wit/workitems/{id}/comments?api-version=7.0-preview.3`
- **GitHub** (`github_issue`): Post comment via gh CLI:
  `gh issue comment <number> --repo <repo> --body "<message>"`
- **Jira** (`jira_issue`): Post comment via Jira REST API using `JIRA_API_TOKEN` and `JIRA_EMAIL`:
  POST `{jira_url}/rest/api/3/issue/{key}/comment`

Comment text: "Completed via Aptean Polaris. Spec: {slug}. Branch: {branch}. WPs: {done}/{total} done."

If credentials missing or API fails: warn once and continue (never blocks).

### Step 6: Estimation Comparison Report

If the feature's `meta.json` contains an `estimation` field:
1. Extract timeline milestones from git commit history (first spec commit to merge)
2. Calculate actual elapsed time (wall-clock hours, not command execution time)
3. Generate `comparison.md` in the feature's `polaris-specs/` directory with:
   - Baseline estimate vs actual elapsed time
   - Difference (absolute hours and percentage)
   - Timeline of key milestones
4. Include a one-line comparison summary in the ship output (e.g., "Baseline: 24h, Actual: 5.2h, -78%")
5. If estimation data is missing: skip silently

### Step 7: Summary

Display a summary of what was shipped:
- Feature name and slug
- Number of WPs merged
- Target branch
- Any deferred issues or skipped WPs
- Cleanup status (worktrees removed)
- Reminder about untracked files (if any) with commit vs gitignore guidance

## Cross-Platform Notes

All commands used here are Polaris CLI commands or git operations that work on Windows, macOS, and Linux. No shell-specific commands are used.


**Telemetry**: Run: `polaris telemetry record ship --feature <slug> --phase complete --agent {{AGENT_NAME}}`
