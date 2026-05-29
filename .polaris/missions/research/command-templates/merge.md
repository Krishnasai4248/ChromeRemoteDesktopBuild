---
description: Merge a completed feature into the main branch and clean up worktree
---

## User Input

**Telemetry**: Run: `polaris telemetry record merge --feature <slug> --phase start --agent {{AGENT_NAME}}`


```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Location Pre-flight (CRITICAL)

You MUST be in a feature worktree, NOT the main repository.

```bash
python -c "
from specify_cli.guards import validate_worktree_location
result = validate_worktree_location()
if not result.is_valid:
    print(result.format_error())
    raise SystemExit(1)
print('Location verified:', result.branch_name)
"
```

If validation fails, navigate to a WP worktree first: `cd .worktrees/<feature>-WP01`

**Exception**: From main, use `polaris merge --feature <slug>`.

**Path reference rule:** Provide absolute or project-root-relative paths. Never refer to a folder by name alone.

## Prerequisites

1. Feature passed `/polaris.accept`
2. All WPs in `done` lane
3. Clean working directory
4. On feature branch (or in its worktree)

## Research Integrity Check

Before merging, validate citations:

```bash
python -c "
from pathlib import Path
from specify_cli.validators.research import validate_citations, validate_source_register
feature_dir = Path('polaris-specs/$FEATURE_SLUG')
for name, fn in [('evidence-log.csv', validate_citations), ('source-register.csv', validate_source_register)]:
    f = feature_dir / 'research' / name
    if f.exists():
        r = fn(f)
        if r.has_errors: print(f'ERROR: {name} has errors'); exit(1)
print('Citations validated')
"
```

## What This Command Does

1. Detect feature branch and worktree status
2. Run pre-flight validation across all worktrees and target branch
3. Determine merge order from WP dependencies
4. Forecast conflicts in `--dry-run` mode
5. Switch to target branch (default: `main`)
6. Update target (`git pull --ff-only`)
7. Merge using chosen strategy, auto-resolve status file conflicts
8. Optionally push, remove worktrees, delete branches

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--strategy` | `merge`, `squash`, or `rebase` | `merge` |
| `--keep-branch` | Keep feature branch after merge | delete |
| `--keep-worktree` | Keep worktree after merge | remove |
| `--push` | Push to origin after merge | no push |
| `--target` | Target branch | `main` |
| `--dry-run` | Preview without executing | off |
| `--feature` | Feature slug (when on main) | none |
| `--resume` | Resume interrupted merge | off |

## Strategies

- **merge** (default): Merge commit preserving history.
- **squash**: Single commit per feature. Clean linear history.
- **rebase**: Linear history, no merge commits. Requires manual rebase first.

## Workspace-per-WP (0.11.0+)

Each WP has its own worktree under `.worktrees/<feature>-WP##/`. Run `polaris merge` from ANY WP worktree - it auto-detects all WP branches and merges sequentially.

## Error Recovery

- **Already on main**: Navigate to worktree first: `cd .worktrees/<feature-slug>`
- **Uncommitted changes**: Commit or stash before merging
- **Fast-forward failed**: Pull main manually, then retry
- **Merge conflicts**: Resolve files, `git add`, `git commit` (include `Co-Authored-By: Aptean Polaris <polaris@aptean.com>` trailer), then manually clean up worktree/branch

## Typical Flow

```bash
/polaris.accept --mode local
/polaris.merge --push
# specify -> plan -> tasks -> implement -> review -> accept -> merge
```


**Telemetry**: Run: `polaris telemetry record merge --feature <slug> --phase complete --agent {{AGENT_NAME}}`
