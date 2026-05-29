---
description: Run E2E tests for work packages with automatic lane transitions (doing -> testing -> for_review/doing).
---


# /polaris.runtests - Run Tests with Auto Lane Transitions

## Model Guidance

Use **claude-sonnet-4-6** for this session. Test execution is mechanical tool-call work - Sonnet handles this well.

## Tool Preferences

1. `Read` / `Grep` / `Glob` - local files (always prefer)
2. `WebFetch` - public URLs, text only
3. Headless browser - dynamic/auth-gated pages (~82% fewer tokens than screenshot tools)
4. Screenshot browser - last resort only; ~10x more tokens than WebFetch, deprioritised in all skills
5. PDFs - extract as text (not images); ~90% token reduction vs. image path. Applies to all implementation skills automatically.

## Output Style

One-line summary per test file run: `<file> -> PASS/FAIL`. After all tests: totals + lane outcome. No per-test narration. Do NOT use extended thinking.

---

## Location Pre-flight (WP mode)

For WP-specific tests: `pwd` must contain `.worktrees/` and branch must NOT be `main`. For `--all` mode: main repo is acceptable.

**Telemetry**: Run: `polaris telemetry record runtests --feature <slug> --phase start --agent claude --wp <WP_ID>`

## Test Modes

| Mode | What it runs | Runner | When to use |
|------|-------------|--------|-------------|
| **Project tests** (default) | Unit/integration via detected framework | `run_tests.py` | After implementation, before review |
| **E2E browser tests** | Browser-based tests from `.spec.js` | `agent-browser` or `playwright` | After project tests pass, for UI |

## Lane Transition Flow

```
doing -> testing -> for_review   (tests pass)
doing -> testing -> doing        (tests fail)
```

## Usage

```bash
polaris runtests                     # Project tests (default)
polaris runtests --wp WP01           # Specific WP
polaris runtests --validate-plan     # Also validate test plan coverage
polaris runtests --mode e2e          # E2E browser tests
polaris runtests --mode e2e --runner playwright
polaris runtests --feature 001-slug  # Specific feature
polaris runtests --all               # Regression - all features, no lane changes
```

## Project Test Suite (Default Mode)

Detects framework from config files: `pyproject.toml` -> pytest, `package.json` -> npm test, `Cargo.toml` -> cargo test, `go.mod` -> go test. Runs via `.polaris/scripts/tasks/run_tests.py`, parses JSON results, transitions lanes.

Direct execution:
```bash
python .polaris/scripts/tasks/run_tests.py --project-root . --wp WP01 --json
python .polaris/scripts/tasks/run_tests.py --project-root . --validate-plan polaris-specs/<slug>/test-plan.md --json
```

Test plan validation: extracts `test_*` names from test-plan.md, scans source for matching definitions, reports coverage. Gate: `>= 80%`.

## E2E Browser Tests (`--mode e2e`)

| Runner | Description |
|--------|-------------|
| `agent-browser` | Parses `.spec.js` comments, drives `npx agent-browser` (default) |
| `playwright` | `npx playwright test` |

Falls back to the other runner if the default is unavailable.

Test files in `polaris-specs/{feature}/tests/e2e/WP##-{slug}.spec.js`.

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--mode` | `project` | `project` or `e2e` |
| `--runner` | `agent-browser` | E2E runner (e2e mode only) |
| `--feature` | auto | Feature slug |
| `--wp` | all eligible | Specific WP |
| `--validate-plan` | false | Validate test plan coverage |
| `--all` | false | Regression mode (no lane changes) |
| `--headed/--headless` | headless | Browser visibility (e2e only) |

## Failure Classification

Load `@references/runtests-failure-classification.md` for the full classification table, auto-retry workflow, and programmatic usage.

## Mutation Testing

Runs automatically after tests pass as a quality gate. Load `@references/runtests-mutation-testing.md` for full details on how mutations are generated, scored, and when the gate fails.

## Troubleshooting

- **"No test framework detected"**: ensure `pyproject.toml`, `package.json`, `Cargo.toml`, or `go.mod` exists at project root
- **"No test files found" (E2E)**: run `/polaris.tasks` first to generate test skeletons
- **"run_tests.py not found"**: run `polaris upgrade` to deploy it, or check `.polaris/scripts/tasks/`
- **"agent-browser not available"**: `npm install -g @anthropic-ai/agent-browser` or use `--runner playwright`
- **"playwright not available"**: `npm init playwright@latest` or use `--runner agent-browser`


**Telemetry**: Run: `polaris telemetry record runtests --feature <slug> --phase complete --agent claude --wp <WP_ID>`
