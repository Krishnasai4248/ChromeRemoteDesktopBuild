---
description: Migrate legacy (.kittify) or external spec directories into the current Polaris format.
---

## Model Guidance

This command does planning work. Use **claude-opus-4-6** for this session.

Deep reasoning, synthesis, and decision-making here propagate to all downstream work. Opus-level reasoning is insurance, not indulgence.

If you are currently on Sonnet: switch to Opus before proceeding (`/model claude-opus-4-6`).

---


# /polaris.migrate - Migrate Specs into Polaris Format

**Version**: 0.16.0+
**Purpose**: Migrate legacy or external spec directories into the current Polaris format (`polaris-specs/`).

---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

---

## When to Use

Use this command when:
- A project still has `.kittify/` or `kitty-specs/` directories from an older Polaris version
- You want to import specs from an external directory into a Polaris project
- You are onboarding a project that has specs in a non-standard location

---

## Workflow

### Auto-detect Legacy Format (most common)

When the project has `.kittify/` or `kitty-specs/` directories:

```bash
# Preview what will happen
polaris migrate --dry-run

# Apply the migration
polaris migrate

# Skip confirmation
polaris migrate --force
```

### Import from External Directory

When specs live outside the project:

```bash
# Preview import
polaris migrate --source /path/to/specs --dry-run

# Import with custom mission type
polaris migrate --source /path/to/specs --mission software-dev

# Import targeting a specific branch
polaris migrate --source /path/to/specs --target-branch develop
```

---

## What the Command Does

1. **Detect** - Identifies the source format (legacy `.kittify/`, external, or already-polaris)
2. **Enumerate** - Finds all feature directories and their artifacts (spec.md, plan.md, tasks/)
3. **Plan** - Generates a migration plan showing what will be moved/copied
4. **Confirm** - Prompts for confirmation (skip with `--force` or `--dry-run`)
5. **Migrate infrastructure** - [legacy only] Renames `.kittify/` to `.polaris/` and `kitty-specs/` to `polaris-specs/`
6. **Migrate specs** - Moves (legacy) or copies (external) features into `polaris-specs/`, creates `meta.json`, fixes WP frontmatter
7. **Validate** - Verifies all migrated specs have required artifacts and valid metadata
8. **Report** - Shows kanban lane distribution summary

---

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--source PATH` | - | External spec directory to import from |
| `--source-format STR` | auto | Format hint: `legacy`, `generic` |
| `--mission STR` | `software-dev` | Mission type for migrated specs |
| `--target-branch STR` | current branch | Target branch for features |
| `--dry-run` | `false` | Preview changes without applying |
| `--force` | `false` | Skip confirmation prompts |
| `--include-tests` | `false` | Also migrate test files to modern frameworks |

---

## Key Behaviors

- **Idempotent**: Safe to run multiple times. Skips features that already exist, preserves existing `meta.json`, and only fixes frontmatter that is missing required fields.
- **Auto-numbering**: Features without a `NNN-` prefix are assigned the next available number in `polaris-specs/`.
- **Legacy uses move**: In-place rename preserves git history.
- **External uses copy**: Source directory is preserved unchanged.
- **No branching**: Works on the current branch.

---

## Post-Migration Verification

After running the migration, verify everything is correct:

```bash
# Confirm features appear in kanban
polaris agent tasks status

# Validate WP metadata consistency
polaris validate-tasks --all

# Check a specific feature
ls polaris-specs/001-my-feature/
cat polaris-specs/001-my-feature/meta.json
```

---

## Test Framework Migration (`--include-tests`)

When the `--include-tests` flag is present, also scan for test files and convert them
to modern test frameworks. When the flag is absent, skip test migration entirely.

### How It Works

1. **Scan** - Find test files using `git ls-files` with patterns like `**/test_*.py`, `**/*_test.py`, `**/*.spec.js`, `**/*.test.js`
2. **Detect** - Identify the source framework from imports and API usage
3. **Convert** - Apply the conversion rules below, preserving all test names and assertions
4. **Mark** - Add `# REVIEW: converted from <framework>` comments on complex or ambiguous patterns

### Preserving Test Names

All original test names MUST be preserved during conversion. For example, a unittest
method `test_user_login_success` must remain `test_user_login_success` as a standalone
function. Never rename, merge, or drop test functions.

### unittest-to-pytest Conversion Rules (Python)

Apply these rules when migrating Python tests from `unittest.TestCase` to pytest:

| unittest Pattern | pytest Equivalent |
|-----------------|-------------------|
| `class TestFoo(unittest.TestCase):` | Remove class; convert methods to standalone `test_foo_*()` functions |
| `self.assertEqual(a, b)` | `assert a == b` |
| `self.assertTrue(x)` | `assert x` |
| `self.assertFalse(x)` | `assert not x` |
| `self.assertRaises(Exc)` | `with pytest.raises(Exc):` |
| `self.assertIn(a, b)` | `assert a in b` |
| `self.assertIsNone(x)` | `assert x is None` |
| `self.assertIsNotNone(x)` | `assert x is not None` |
| `self.assertAlmostEqual(a, b)` | `assert a == pytest.approx(b)` |
| `setUp(self)` | `@pytest.fixture` (use `autouse=True` if needed); pair with `yield` for tearDown |
| `tearDown(self)` | Combine into the `@pytest.fixture` using `yield` pattern |
| `@unittest.skip("reason")` | `@pytest.mark.skip(reason="reason")` |
| `@unittest.expectedFailure` | `@pytest.mark.xfail` |
| `setUpClass(cls)` / `tearDownClass(cls)` | `@pytest.fixture(scope="module")` with `yield` |

**Complex patterns**: When a conversion is ambiguous (e.g., deeply nested setUp logic,
custom TestCase subclasses, multiple inheritance), add a `# REVIEW: converted from unittest`
comment so a human can verify the result.

**Import changes**: Replace `import unittest` with `import pytest`. Remove
`from unittest import TestCase` if present.

### Jasmine-to-Jest Conversion Rules (JavaScript)

Apply these rules when migrating JavaScript tests from Jasmine to Jest:

| Jasmine Pattern | Jest Equivalent |
|----------------|-----------------|
| `jasmine.createSpy('name')` | `jest.fn()` |
| `jasmine.createSpyObj('name', ['method'])` | Create object manually with `jest.fn()` for each method |
| `spyOn(obj, 'method').and.returnValue(x)` | `jest.spyOn(obj, 'method').mockReturnValue(x)` |
| `spyOn(obj, 'method').and.callThrough()` | `jest.spyOn(obj, 'method')` |
| `spyOn(obj, 'method').and.callFake(fn)` | `jest.spyOn(obj, 'method').mockImplementation(fn)` |
| `jasmine.clock().install()` | `jest.useFakeTimers()` |
| `jasmine.clock().tick(ms)` | `jest.advanceTimersByTime(ms)` |
| `jasmine.clock().uninstall()` | `jest.useRealTimers()` |
| `jasmine.any(Type)` | `expect.any(Type)` |
| `jasmine.objectContaining({})` | `expect.objectContaining({})` |

**Compatible patterns** (no changes needed): `describe`, `it`, `beforeEach`, `afterEach`,
`beforeAll`, `afterAll`, `expect(...).toBe(...)`, `expect(...).toEqual(...)`,
`expect(...).toBeTruthy()`, `expect(...).toBeFalsy()`.

**Custom matchers**: Jasmine custom matchers (`jasmine.addMatchers(...)`) have no direct
Jest equivalent. Add a `// REVIEW: custom matcher needs Jest equivalent` comment and
leave the code in place for manual conversion.

**Import changes**: Remove any `require('jasmine')` imports. Add Jest globals
(`jest`, `expect`) which are available automatically in Jest environments.

---

## Troubleshooting

**"Could not detect a source format to migrate"**
- The project has neither `.kittify/` nor `kitty-specs/` directories
- Use `--source PATH` to import from an external directory

**"Project already uses the Polaris format"**
- The project already has `.polaris/` and `polaris-specs/`
- Use `--source` to import additional specs from elsewhere

**"Both .kittify/ and .polaris/ exist - manual merge required"**
- The legacy infrastructure migration cannot run automatically
- Manually resolve the conflict, then re-run

**"meta.json missing required fields"**
- A migrated feature's `meta.json` is incomplete
- Re-run `polaris migrate` (it will only fix what's missing)

---

## Context

$ARGUMENTS
