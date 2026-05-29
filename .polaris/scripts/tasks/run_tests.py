"""Polaris test runner - deterministic test execution for autopilot pipeline.

Detects test frameworks, executes tests, parses results, and validates test plans.
Uses ONLY Python stdlib (no external dependencies).

Usage:
    python run_tests.py --project-root <path> --json
    python run_tests.py --project-root <path> --wp WP01 --json
    python run_tests.py --project-root <path> --validate-plan test-plan.md --json
    python run_tests.py --project-root <path> --feature 001-my-feature --json
    python run_tests.py --project-root <path> --changed-only --json
    python run_tests.py --project-root <path> --changed-only --diff-base origin/main --json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path


# Directories to skip when searching for test files
SKIP_DIRS = {
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".git",
    ".hg",
    ".svn",
    "dist",
    "build",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    ".eggs",
}


def detect_test_framework(project_root: str) -> tuple[str, str]:
    """Detect which test framework a project uses by scanning config files.

    Returns:
        Tuple of (framework_name, command_string).
        framework_name is one of: "pytest", "npm", "cargo", "go", "none", "unknown".
        - "none": No test framework AND no test files found (legitimate no-tests case)
        - "unknown": Test files exist but framework couldn't be determined
    """
    root = Path(project_root)

    # Priority order: Python first (most common polaris use case)
    if (root / "pyproject.toml").exists() or (root / "setup.py").exists() or (root / "setup.cfg").exists():
        return ("pytest", "python -m pytest")

    if (root / "package.json").exists():
        return ("npm", "npm test")

    if (root / "Cargo.toml").exists():
        return ("cargo", "cargo test")

    if (root / "go.mod").exists():
        return ("go", "go test ./...")

    # No config files found - check for test files directly
    # This handles cases where tests exist but no package manifest
    has_python_tests = _has_test_files(root, "test_*.py", "*_test.py")
    has_js_tests = _has_test_files(root, "*.test.js", "*.spec.js", "*.e2e.js", "*.test.ts", "*.spec.ts")
    has_rust_tests = _has_test_files(root, "**/tests/*.rs")
    has_go_tests = _has_test_files(root, "*_test.go")

    if has_python_tests:
        return ("pytest", "python -m pytest")
    if has_js_tests:
        # No package.json but has JS tests - try npx jest or vitest
        if (root / "jest.config.js").exists() or (root / "jest.config.json").exists():
            return ("jest", "npx jest")
        if (root / "vitest.config.js").exists() or (root / "vitest.config.ts").exists():
            return ("vitest", "npx vitest run")
        return ("jest", "npx jest")  # Default to jest for JS tests
    if has_rust_tests:
        return ("cargo", "cargo test")
    if has_go_tests:
        return ("go", "go test ./...")

    # No test framework AND no test files - this is a "none" case, not "unknown"
    return ("none", "")


def _has_test_files(root: Path, *patterns: str) -> bool:
    """Check if any test files matching the patterns exist in the project."""
    for pattern in patterns:
        for test_file in root.rglob(pattern):
            # Skip common non-test directories
            if any(part in SKIP_DIRS for part in test_file.parts):
                continue
            if test_file.is_file():
                return True
    return False


def map_to_test_files(changed_files: list[str], project_root: str) -> list[str]:
    """Map changed source files to their corresponding test file paths.

    For each changed file, attempts to find a corresponding test file by:
    - Replacing leading "src/" with "tests/"
    - Prepending "test_" to the filename

    Only returns paths that actually exist on disk.

    Args:
        changed_files: List of changed file paths (relative to project root).
        project_root: Path to the project directory.

    Returns:
        Deduplicated list of existing test file paths (relative to project root).
    """
    test_files: list[str] = []
    seen: set[str] = set()

    for filepath in changed_files:
        if not filepath.endswith(".py"):
            continue

        parts = filepath.replace("\\", "/").split("/")

        # Replace leading "src/" with "tests/" and prepend "test_" to filename
        if len(parts) >= 2 and parts[0] == "src":
            test_parts = ["tests"] + parts[1:-1] + ["test_" + parts[-1]]
            candidate = "/".join(test_parts)
            full_path = os.path.join(project_root, candidate)
            if os.path.exists(full_path) and candidate not in seen:
                test_files.append(candidate)
                seen.add(candidate)

    return test_files


def get_changed_test_files(
    project_root: str, diff_base: str | None = None
) -> tuple[list[str], str]:
    """Get test files affected by changes since a given base ref.

    If diff_base is None, auto-detects by running ``git merge-base main HEAD``.
    Falls back to ``HEAD~1`` if merge-base fails.

    Args:
        project_root: Path to the project directory.
        diff_base: Git ref to diff against (e.g., "origin/main", a SHA). Auto-detected if None.

    Returns:
        Tuple of (list of test file paths relative to project root, base_ref used).
    """
    base_ref = diff_base

    # Auto-detect base ref if not provided
    if base_ref is None:
        try:
            merge_base_result = subprocess.run(
                ["git", "merge-base", "main", "HEAD"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=project_root,
            )
            if merge_base_result.returncode == 0 and merge_base_result.stdout.strip():
                base_ref = merge_base_result.stdout.strip()
            else:
                base_ref = "HEAD~1"
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            base_ref = "HEAD~1"

    # Get changed files between base_ref and HEAD
    try:
        diff_result = subprocess.run(
            ["git", "diff", "--name-only", base_ref, "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=project_root,
        )
        if diff_result.returncode != 0:
            return ([], base_ref)
        changed_files = [
            f.strip() for f in diff_result.stdout.strip().splitlines() if f.strip()
        ]
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ([], base_ref)

    # Filter to .py files only
    py_files = [f for f in changed_files if f.endswith(".py")]

    # Map source files to test files
    mapped_tests = map_to_test_files(py_files, project_root)

    # Also include directly changed files that match test patterns
    direct_tests: list[str] = []
    for filepath in py_files:
        basename = filepath.replace("\\", "/").split("/")[-1]
        if basename.startswith("test_") or basename.endswith("_test.py"):
            full_path = os.path.join(project_root, filepath)
            if os.path.exists(full_path):
                direct_tests.append(filepath)

    # Combine and deduplicate
    all_tests: list[str] = []
    seen: set[str] = set()
    for t in mapped_tests + direct_tests:
        normalized = t.replace("\\", "/")
        if normalized not in seen:
            all_tests.append(normalized)
            seen.add(normalized)

    return (all_tests, base_ref)


def parse_pytest_output(output: str) -> dict:
    """Extract pass/fail/skip/error counts from pytest output."""
    passed = 0
    failed = 0
    skipped = 0
    errors = 0

    m = re.search(r"(\d+) passed", output)
    if m:
        passed = int(m.group(1))

    m = re.search(r"(\d+) failed", output)
    if m:
        failed = int(m.group(1))

    m = re.search(r"(\d+) skipped", output)
    if m:
        skipped = int(m.group(1))

    m = re.search(r"(\d+) error", output)
    if m:
        errors = int(m.group(1))

    total = passed + failed + skipped + errors
    return {"passed": passed, "failed": failed, "skipped": skipped, "errors": errors, "total": total}


def parse_npm_output(output: str) -> dict:
    """Extract pass/fail counts from npm test output (Jest or Mocha)."""
    passed = 0
    failed = 0
    skipped = 0
    errors = 0

    # Try Jest format: "Tests: X failed, Y passed, Z total"
    m = re.search(r"Tests:\s+(?:(\d+) failed,\s*)?(?:(\d+) skipped,\s*)?(?:(\d+) passed,\s*)?(\d+) total", output)
    if m:
        failed = int(m.group(1) or 0)
        skipped = int(m.group(2) or 0)
        passed = int(m.group(3) or 0)
        total = int(m.group(4))
        return {"passed": passed, "failed": failed, "skipped": skipped, "errors": errors, "total": total}

    # Try Mocha format
    m_passing = re.search(r"(\d+) passing", output)
    m_failing = re.search(r"(\d+) failing", output)
    m_pending = re.search(r"(\d+) pending", output)
    if m_passing:
        passed = int(m_passing.group(1))
    if m_failing:
        failed = int(m_failing.group(1))
    if m_pending:
        skipped = int(m_pending.group(1))

    total = passed + failed + skipped + errors
    return {"passed": passed, "failed": failed, "skipped": skipped, "errors": errors, "total": total}


def parse_cargo_output(output: str) -> dict:
    """Extract pass/fail/ignored counts from cargo test output."""
    passed = 0
    failed = 0
    skipped = 0
    errors = 0

    m = re.search(r"test result: (?:ok|FAILED)\.\s+(\d+) passed;\s+(\d+) failed;\s+(\d+) ignored", output)
    if m:
        passed = int(m.group(1))
        failed = int(m.group(2))
        skipped = int(m.group(3))  # "ignored" maps to "skipped"

    total = passed + failed + skipped + errors
    return {"passed": passed, "failed": failed, "skipped": skipped, "errors": errors, "total": total}


def parse_go_output(output: str) -> dict:
    """Extract pass/fail counts from go test output."""
    passed = 0
    failed = 0
    skipped = 0
    errors = 0

    # Count individual test results
    passed = len(re.findall(r"--- PASS:", output))
    failed = len(re.findall(r"--- FAIL:", output))
    skipped = len(re.findall(r"--- SKIP:", output))

    total = passed + failed + skipped + errors
    return {"passed": passed, "failed": failed, "skipped": skipped, "errors": errors, "total": total}


def parse_output(framework: str, output: str) -> dict:
    """Route to the correct parser based on framework name."""
    parsers = {
        "pytest": parse_pytest_output,
        "npm": parse_npm_output,
        "cargo": parse_cargo_output,
        "go": parse_go_output,
    }
    parser = parsers.get(framework)
    if parser:
        return parser(output)
    return {"passed": 0, "failed": 0, "skipped": 0, "errors": 0, "total": 0}


def find_wp_test_paths(project_root: str, wp_id: str) -> list[str]:
    """Find test files or directories associated with a work package ID.

    Searches for test files whose path or name contains the WP ID (case-insensitive).
    This is more reliable than pytest -k which matches test function names.

    Args:
        project_root: Path to the project directory.
        wp_id: Work package ID, e.g. "WP01".

    Returns:
        List of relative paths to matching test files (empty if none found).
    """
    root = Path(project_root)
    wp_lower = wp_id.lower()
    matches: list[str] = []

    for py_file in root.rglob("test_*.py"):
        if any(part in SKIP_DIRS for part in py_file.parts):
            continue
        rel = py_file.relative_to(root)
        if wp_lower in str(rel).lower():
            matches.append(str(rel))

    return sorted(matches)


def run_tests(
    project_root: str,
    wp_id: str | None = None,
    timeout: int = 300,
    changed_only: bool = False,
    diff_base: str | None = None,
    feature: str | None = None,
) -> dict:
    """Execute tests and return structured results.

    Args:
        project_root: Path to the project directory.
        wp_id: Optional work package ID to filter tests. Uses path-based matching
            first (test files whose path contains the WP ID), then falls back to
            pytest -k if no matching files are found.
        timeout: Maximum seconds to wait for test execution.
        changed_only: If True, only run tests for changed files.
        diff_base: Git ref to diff against when changed_only is True.
        feature: Optional feature slug. If provided, runs only tests in
            tests/<slug>/ directory. Falls back to full suite if not found.

    Returns:
        Dict with framework, command, exit_code, counts, output, and success.
    """
    framework, command = detect_test_framework(project_root)

    if framework == "none":
        # No tests exist - this is a valid state, not a failure
        # Autopilot can proceed with manual verification
        return {
            "framework": "none",
            "command": "",
            "exit_code": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "total": 0,
            "duration_seconds": 0.0,
            "output": "",
            "success": True,
            "no_tests": True,
            "message": "No test files found. Manual verification recommended.",
        }

    if framework == "unknown":
        # Tests might exist but we couldn't determine the framework
        return {
            "framework": "unknown",
            "command": "",
            "exit_code": -1,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "total": 0,
            "duration_seconds": 0.0,
            "output": "",
            "success": False,
            "error": "Test files detected but framework could not be determined. Specify framework manually.",
        }

    # Scoping: if --changed-only, resolve test files to run
    scoped = False
    scoped_files: list[str] = []
    used_diff_base: str | None = None

    if changed_only:
        scoped_files, used_diff_base = get_changed_test_files(project_root, diff_base)
        if scoped_files:
            scoped = True
            # Append the scoped test file paths to the command
            command = command + " " + " ".join(scoped_files)
        # If no scoped files found, fall back to full suite (scoped stays False)

    # If --feature is provided, scope to tests/<slug>/ directory if it exists.
    if feature and not scoped:
        feature_test_dir = Path(project_root) / "tests" / feature
        if feature_test_dir.is_dir():
            feature_rel = str(feature_test_dir.relative_to(Path(project_root)))
            if framework == "pytest":
                command = f"{command} {feature_rel}"
            elif framework in ("npm", "jest", "vitest"):
                command = f"{command} -- --testPathPattern {feature}"
            # For cargo/go, no standard directory scoping - fall through to full suite

    # If wp_id is provided and framework is pytest, filter to this WP's tests.
    # Prefer path-based matching (more reliable than -k which matches function names).
    if wp_id and framework == "pytest":
        wp_paths = find_wp_test_paths(project_root, wp_id)
        if wp_paths:
            command = f"{command} {' '.join(wp_paths)}"
        else:
            # Fallback: -k filter (works if tests are named with WP ID)
            command = f"{command} -k {wp_id}"

    start = time.time()
    try:
        result = subprocess.run(
            command.split(),
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=project_root,
        )
        duration = time.time() - start
        combined_output = (result.stdout or "") + (result.stderr or "")
        counts = parse_output(framework, combined_output)

        report = {
            "framework": framework,
            "command": command,
            "exit_code": result.returncode,
            "passed": counts["passed"],
            "failed": counts["failed"],
            "skipped": counts["skipped"],
            "errors": counts["errors"],
            "total": counts["total"],
            "duration_seconds": round(duration, 2),
            "output": combined_output,
            "success": result.returncode == 0,
        }

        if changed_only:
            report["scoped"] = scoped
            report["scoped_files"] = scoped_files
            report["diff_base"] = used_diff_base

        return report
    except subprocess.TimeoutExpired:
        duration = time.time() - start
        report = {
            "framework": framework,
            "command": command,
            "exit_code": -1,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "total": 0,
            "duration_seconds": round(duration, 2),
            "output": "",
            "success": False,
            "error": f"Test execution timed out after {timeout}s",
        }
        if changed_only:
            report["scoped"] = scoped
            report["scoped_files"] = scoped_files
            report["diff_base"] = used_diff_base
        return report
    except FileNotFoundError:
        report = {
            "framework": framework,
            "command": command,
            "exit_code": -1,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "total": 0,
            "duration_seconds": 0.0,
            "output": "",
            "success": False,
            "error": f"Test command not found: {command}",
        }
        if changed_only:
            report["scoped"] = scoped
            report["scoped_files"] = scoped_files
            report["diff_base"] = used_diff_base
        return report


def validate_test_plan(project_root: str, test_plan_path: str) -> dict:
    """Compare planned test names against actual test functions in source.

    Args:
        project_root: Path to the project directory.
        test_plan_path: Path to the test plan markdown file.

    Returns:
        Dict with planned, found, missing lists and coverage_percent.
    """
    plan_path = Path(test_plan_path)
    if not plan_path.exists():
        return {"error": f"Test plan not found: {test_plan_path}"}

    plan_content = plan_path.read_text(encoding="utf-8", errors="replace")

    # Extract test names from markdown
    # Match patterns like: - test_something, - [ ] test_something, ### test_something, **test_something**
    test_name_pattern = re.compile(
        r"(?:^[-*]\s*(?:\[.\]\s*)?|^#{1,4}\s*\*{0,2})(test_\w+)",
        re.MULTILINE,
    )
    planned = list(set(test_name_pattern.findall(plan_content)))
    planned.sort()

    if not planned:
        return {"planned": [], "found": [], "missing": [], "coverage_percent": 0}

    # Search source files for test function definitions
    root = Path(project_root)
    found_test_names: set[str] = set()

    for py_file in root.rglob("*.py"):
        # Skip common non-test directories
        if any(part in SKIP_DIRS for part in py_file.parts):
            continue
        try:
            content = py_file.read_text(encoding="utf-8", errors="replace")
            for match in re.finditer(r"def (test_\w+)", content):
                found_test_names.add(match.group(1))
        except (OSError, PermissionError):
            continue

    found = sorted([t for t in planned if t in found_test_names])
    missing = sorted([t for t in planned if t not in found_test_names])
    coverage_pct = round(len(found) / len(planned) * 100, 1) if planned else 0

    return {
        "planned": planned,
        "found": found,
        "missing": missing,
        "coverage_percent": coverage_pct,
    }


def main() -> None:
    """CLI entry point for the test runner."""
    parser = argparse.ArgumentParser(description="Polaris test runner")
    parser.add_argument("--project-root", required=True, help="Path to project root")
    parser.add_argument("--wp", default=None, help="Filter tests by work package ID")
    parser.add_argument("--feature", default=None,
                        help="Run only tests in tests/<slug>/ directory. Falls back to full suite if not found.")
    parser.add_argument("--validate-plan", default=None, help="Path to test-plan.md")
    parser.add_argument("--no-run", action="store_true", dest="no_run",
                        help="Skip test execution — only validate the test plan (requires --validate-plan)")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Output as JSON")
    parser.add_argument("--timeout", type=int, default=300, help="Test timeout in seconds")
    parser.add_argument(
        "--changed-only",
        action="store_true",
        default=False,
        help="Only run tests for files changed since diff-base",
    )
    parser.add_argument(
        "--diff-base",
        default=None,
        help="Git ref to diff against (default: auto-detect via merge-base)",
    )
    args = parser.parse_args()

    if args.no_run and not args.validate_plan:
        print("Error: --no-run requires --validate-plan", file=sys.stderr)
        sys.exit(1)

    if args.no_run:
        # Skip test execution - only run plan validation
        result = {"success": True, "framework": "skipped", "command": "", "exit_code": 0,
                  "passed": 0, "failed": 0, "skipped": 0, "errors": 0, "total": 0,
                  "duration_seconds": 0.0, "output": ""}
    else:
        result = run_tests(
            args.project_root,
            wp_id=args.wp,
            timeout=args.timeout,
            changed_only=args.changed_only,
            diff_base=args.diff_base,
            feature=args.feature,
        )

    if args.validate_plan:
        validation = validate_test_plan(args.project_root, args.validate_plan)
        result["validation"] = validation

    if args.json_output:
        print(json.dumps(result, indent=2))
    else:
        # Human-readable output
        print(f"Framework: {result.get('framework', 'unknown')}")
        print(f"Command:   {result.get('command', 'N/A')}")
        if result.get("error"):
            print(f"Error:     {result['error']}")
        elif result.get("no_tests"):
            print("Result:    NO TESTS FOUND")
            print(f"Message:   {result.get('message', 'Manual verification recommended.')}")
        else:
            print(f"Result:    {'PASSED' if result.get('success') else 'FAILED'}")
            print(f"Passed:    {result.get('passed', 0)}")
            print(f"Failed:    {result.get('failed', 0)}")
            print(f"Skipped:   {result.get('skipped', 0)}")
            print(f"Errors:    {result.get('errors', 0)}")
            print(f"Total:     {result.get('total', 0)}")
            print(f"Duration:  {result.get('duration_seconds', 0)}s")

        if "validation" in result:
            v = result["validation"]
            if "error" in v:
                print(f"\nValidation Error: {v['error']}")
            else:
                print("\nTest Plan Validation:")
                print(f"  Planned:  {len(v.get('planned', []))}")
                print(f"  Found:    {len(v.get('found', []))}")
                print(f"  Missing:  {len(v.get('missing', []))}")
                print(f"  Coverage: {v.get('coverage_percent', 0)}%")

    # Exit 0 for success OR no_tests (allow pipeline to proceed)
    # Exit 1 only for actual test failures
    sys.exit(0 if result.get("success") or result.get("no_tests") else 1)


if __name__ == "__main__":
    main()
