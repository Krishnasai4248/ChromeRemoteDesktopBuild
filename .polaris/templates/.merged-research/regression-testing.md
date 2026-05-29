---
description: Run automated Web UI regression tests against any web application using agent-browser with live element discovery, test script generation, and HTML reporting.
---

## User Input

**Telemetry**: Run: `polaris telemetry record regression-testing --feature <slug> --phase start --agent {{AGENT_NAME}} --wp <WP_ID>`


```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Perform automated Web UI regression testing against a live web application. Uses `agent-browser` to discover all interactive elements on the page, generates bash test scripts from that discovery, executes them, and produces a detailed HTML report. Every test run starts 100% fresh from live discovery - no prior knowledge of the application is used.

**This command is application-agnostic** - it works on any web app accessible via URL, with or without authentication.

## MANDATORY - Fresh Discovery Only

The `ralph/` folder may contain test scripts, screenshots, reports, and data from a PREVIOUSLY tested application. **You MUST completely ignore all of it.** Specifically:
- **DO NOT read, reference, copy, or reuse** any `.sh` files in `ralph/tests/` - they contain element refs, URLs, test cases, and app-specific logic from an old application that has NOTHING to do with the current one.
- **DO NOT use** any URLs, element refs (`@eNN`), app names, page titles, or test descriptions found in existing files.
- **DELETE all old `.sh` scripts** in `ralph/tests/` (except the templates you generate fresh) before writing new ones.
- **The only things to keep** from the folder structure are: the directory layout (`tests/`, `test-results/`, `screenshots/`) and this instruction set.
- Every test run starts **100% fresh from live discovery**. You generate everything new based on what `agent-browser snapshot -i` returns for the user's URL. No exceptions.

## How agent-browser Works

### Execution Environment
All commands execute via WSL:
```bash
wsl -e bash -c "export PATH=/home/ym1/.local/node_modules/.bin:/usr/bin:/bin && export DISPLAY=:0 && <command>"
```

### Core Commands
| Command | Purpose |
|---------|---------|
| `agent-browser open '<URL>'` | Open a URL |
| `agent-browser --headers '{"Authorization": "Bearer <TOKEN>"}' open '<URL>'` | Open URL with auth headers |
| `agent-browser snapshot -i` | List all interactive elements with refs (e.g., `[ref=e1]`) |
| `agent-browser click '@e1'` | Click element by ref |
| `agent-browser fill '@e1' 'text'` | Clear input and type text |
| `agent-browser get url` | Get current page URL |
| `agent-browser get value '@e1'` | Get value of an input element |
| `agent-browser screenshot /mnt/c/path/file.png --full` | Full-page screenshot (**must use `/mnt/c/` paths**) |
| `agent-browser close` | Close the browser |

### Element Refs
- `snapshot -i` returns elements like: `button "Submit" [ref=e42]`
- Refs are session-specific - always snapshot before interacting
- Refs change after page navigation or DOM updates - re-snapshot after every action
- NEVER assume ref numbers - always discover them fresh

## Execution Steps

### Phase 1: Gather Info

1. Ask user for the **URL** to test
2. Ask for **authentication** method:
   - **Bearer token** - user pastes JWT in chat
   - **Basic auth** - user provides username/password in chat
   - **None** - public page
3. Do NOT assume any URL, token, or app details from memory or prior conversations

### Phase 2: Discovery

1. Open the URL with appropriate auth headers via WSL:
   ```bash
   wsl -e bash -c "export PATH=/home/ym1/.local/node_modules/.bin:/usr/bin:/bin && export DISPLAY=:0 && agent-browser --headers '{\"Authorization\": \"Bearer <TOKEN>\"}' open '<URL>'"
   ```
2. Wait 5 seconds for the page to load fully
3. Run `snapshot -i` to discover ALL interactive elements:
   ```bash
   wsl -e bash -c "export PATH=/home/ym1/.local/node_modules/.bin:/usr/bin:/bin && export DISPLAY=:0 && agent-browser snapshot -i"
   ```
4. Take a full-page screenshot to `ralph/screenshots/`:
   ```bash
   wsl -e bash -c "export PATH=/home/ym1/.local/node_modules/.bin:/usr/bin:/bin && export DISPLAY=:0 && agent-browser screenshot /mnt/c/Users/ym1/polaris/ralph/screenshots/discovery-screenshot.png --full"
   ```
5. Categorize discovered elements by function (navigation, forms, buttons, inputs, dropdowns, tables, etc.)
6. Report to user: page title, element count, categories, screenshot

### Phase 3: Test Script Generation

Based ONLY on what was discovered in Phase 2, generate these files in `ralph/tests/`:

**First, delete all old scripts:**
Remove all `.sh` files in `ralph/tests/` except those you are about to generate fresh.

**`config.sh`** - Fresh for every application:
```bash
#!/bin/bash
# Shared config - generated for: <PAGE_TITLE>
URL="<USER_PROVIDED_URL>"
TIMESTAMP=${TIMESTAMP:-$(date +%Y%m%d_%H%M%S)}
RESULTS_DIR="test-results/uat-$TIMESTAMP"

if [ -z "${BEARER_TOKEN:-}" ]; then
    echo "Error: BEARER_TOKEN not set. Export it before running."
    exit 1
fi
AUTH_HEADER='{"Authorization": "Bearer '"$BEARER_TOKEN"'"}'

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'

export TOTAL_TESTS=${TOTAL_TESTS:-0}
export PASSED_TESTS=${PASSED_TESTS:-0}
export FAILED_TESTS=${FAILED_TESTS:-0}
export SKIPPED_TESTS=${SKIPPED_TESTS:-0}
export SUITE_MODE=${SUITE_MODE:-0}

log_info()  { echo -e "${YELLOW}[INFO]${NC} $1"; }
log_pass()  {
    echo -e "${GREEN}[PASS]${NC} $1"
    PASSED_TESTS=$((PASSED_TESTS+1)); TOTAL_TESTS=$((TOTAL_TESTS+1))
    export PASSED_TESTS TOTAL_TESTS
    echo "PASS: $1" >> "$RESULTS_DIR/test-results.log"
}
log_fail()  {
    echo -e "${RED}[FAIL]${NC} $1"
    FAILED_TESTS=$((FAILED_TESTS+1)); TOTAL_TESTS=$((TOTAL_TESTS+1))
    export FAILED_TESTS TOTAL_TESTS
    echo "FAIL: $1" >> "$RESULTS_DIR/test-results.log"
    TC_ID=$(echo "$1" | grep -o 'TC-[0-9]\+' | head -1)
    if [ -n "$TC_ID" ]; then
        echo "  Capturing failure evidence..."
        agent-browser screenshot "$RESULTS_DIR/failure-$TC_ID.png" --full 2>/dev/null
        agent-browser snapshot -i > "$RESULTS_DIR/failure-$TC_ID-snapshot.txt" 2>/dev/null
    fi
}
log_skip()  {
    echo -e "${YELLOW}[SKIP]${NC} $1"
    SKIPPED_TESTS=$((SKIPPED_TESTS+1)); TOTAL_TESTS=$((TOTAL_TESTS+1))
    export SKIPPED_TESTS TOTAL_TESTS
    echo "SKIP: $1" >> "$RESULTS_DIR/test-results.log"
}

standalone_setup() {
    if [ "$SUITE_MODE" != "1" ]; then
        mkdir -p "$RESULTS_DIR"; touch "$RESULTS_DIR/test-results.log"
        agent-browser close > /dev/null 2>&1 || true
        log_info "Opening application (standalone mode)..."
        agent-browser --headers "$AUTH_HEADER" open "$URL"
        sleep 5
    fi
}
standalone_teardown() {
    if [ "$SUITE_MODE" != "1" ]; then
        echo ""
        log_info "Total: $TOTAL_TESTS | Passed: $PASSED_TESTS | Failed: $FAILED_TESTS | Skipped: $SKIPPED_TESTS"
        agent-browser close > /dev/null 2>&1 || true
    fi
}
```

**`run-all-tests.sh`** - Orchestrator:
```bash
#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh" "$@"
export SUITE_MODE=1
mkdir -p "$RESULTS_DIR"
touch "$RESULTS_DIR/test-results.log"

log_info "========================================"
log_info "  UAT Test Suite"
log_info "  URL: $URL"
log_info "  Results: $RESULTS_DIR"
log_info "========================================"

agent-browser close > /dev/null 2>&1 || true
log_info "Opening application..."
agent-browser --headers "$AUTH_HEADER" open "$URL"
sleep 5
agent-browser snapshot -i > "$RESULTS_DIR/initial-snapshot.txt" 2>/dev/null
agent-browser screenshot "$RESULTS_DIR/initial-page.png" --full 2>/dev/null

SCRIPT_COUNT=0
for script in "$SCRIPT_DIR"/[0-9][0-9]-*.sh; do
    if [ -f "$script" ]; then
        echo ""
        log_info "Running: $(basename "$script")"
        source "$script"
        SCRIPT_COUNT=$((SCRIPT_COUNT + 1))
    fi
done

agent-browser close > /dev/null 2>&1 || true

echo ""
log_info "========================================"
log_info "  COMPLETE"
log_info "  Scripts: $SCRIPT_COUNT | Tests: $TOTAL_TESTS"
echo -e "  ${GREEN}Passed: $PASSED_TESTS${NC}"
echo -e "  ${RED}Failed: $FAILED_TESTS${NC}"
log_info "========================================"

[ "$FAILED_TESTS" -gt 0 ] && exit 1 || exit 0
```

**Feature test scripts** - One per discovered feature area, named `NN-feature-name.sh`:
```bash
#!/bin/bash
# Feature: <Name> Tests (TC-XXX to TC-YYY)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh" "$@"
standalone_setup

log_info "=== <Feature Name> Tests ==="
SNAPSHOT=$(agent-browser snapshot -i 2>/dev/null)

# TC-XXX: <What is being verified>
if echo "$SNAPSHOT" | grep -q "@eNN"; then
    log_pass "TC-XXX: <Description>"
else
    log_fail "TC-XXX: <Description>"
fi

# For click tests: click, wait, re-snapshot, verify
# agent-browser click '@eNN' 2>/dev/null
# sleep 2
# SNAPSHOT=$(agent-browser snapshot -i 2>/dev/null)
# if echo "$SNAPSHOT" | grep -qi "expected text"; then ...

standalone_teardown
```

**Test types to generate based on what you discover:**
- **Visibility** - element exists in snapshot (`grep -q "@eNN"`)
- **Label match** - element text matches (`grep "@eNN" | grep -qi "expected"`)
- **Click + verify** - click, sleep 2s, re-snapshot, verify new state
- **Form input** - `agent-browser fill '@eNN' 'text'`, then verify
- **Navigation** - click nav element, check URL or page content changed, return
- **Dropdown** - click trigger, verify options appear in new snapshot
- **State** - check `[disabled]`, `[selected]`, `[pressed]` in snapshot output
- **Empty state** - navigate to empty views, verify placeholder text

### Phase 4: Execution

1. Delete any old test scripts in `ralph/tests/` that are from previous applications
2. Write the newly generated `config.sh`, `run-all-tests.sh`, and `NN-*.sh` scripts
3. Run via WSL:
   ```bash
   wsl -e bash -c "export PATH=/home/ym1/.local/node_modules/.bin:/usr/bin:/bin && export DISPLAY=:0 && export BEARER_TOKEN='<TOKEN>' && cd /mnt/c/Users/ym1/polaris/ralph && bash tests/run-all-tests.sh"
   ```
4. Timeout: 10 minutes max (600000ms)
5. Capture full output

### Phase 5: HTML Report

After EVERY test run, generate `ralph/test-results/ralph-report.html` using the Code Eye Portal Design System (dark theme `#0f172a`, teal accent `#1E6978`).

**Required sections:**
1. **Header** - App name (from page title), URL, auth method, date, `agent-browser v0.9.1`
2. **Verdict banner** - Color-coded:
   - `verdict-perfect` green: 95%+ pass rate
   - `verdict-good` green: 80-94%
   - `verdict-warn` yellow: 60-79%
   - `verdict-bad` red: below 60%
3. **Executive summary** - One paragraph with key numbers
4. **Stats cards** (4 top + 4 bottom):
   - Top: Total tests, passed, failed, pass rate
   - Bottom: Total checks, checks passed, checks failed, elements discovered
5. **Progress bar** - Visual pass rate with color
6. **How to read legend** - Explains PASS/FAIL icons and score meaning
7. **Failed tests quick view** - Red card per failed test listing which checks failed
8. **Full results table** - Grouped by feature:
   - Feature header row with pass score (e.g., "3/4")
   - Each test: number, name, individual checks with pass/fail markers, element refs, PASS/FAIL badge
9. **Discovered elements** - Collapsible `<details>` per category with count badges
10. **Screenshots** - Clickable with fullscreen overlay (`openOverlay` JS function)
11. **Footer** - Timestamp, framework, URL, auth method, element count

**ALWAYS open the report after generation:**
```bash
start "" "c:\Users\ym1\polaris\ralph\test-results\ralph-report.html"
```

## Output Location

- Generated test scripts go to: `ralph/tests/`
- Test results, logs, screenshots go to: `ralph/test-results/`
- Before generating, delete any old scripts in `ralph/tests/` (except `run-all-tests.sh` and `config.sh` if reusable)

## Critical Rules

1. **ZERO prior knowledge** - NEVER reference any previously tested application. No hardcoded URLs, element refs, app names, or test data from past sessions or from existing files in `ralph/tests/`.
2. **Discover everything fresh** - All scripts generated from live `snapshot -i` output only. Never reuse old scripts.
3. **Delete before generate** - Remove old test scripts from `ralph/tests/` before writing new ones for a different application.
4. **Token in chat only** - Always ask user to paste their token. NEVER read from `.env` or any file. NEVER store tokens to disk.
5. **WSL paths** - Screenshots MUST use `/mnt/c/Users/...` paths inside WSL. Never `c:\` or `/c/`.
6. **Re-snapshot after every action** - Refs change after clicks/navigation/DOM updates.
7. **Sleep after actions** - Wait 2-3 seconds after clicks/navigation before snapshotting.
8. **Failure evidence** - Every `log_fail` auto-captures screenshot + snapshot.
9. **Report every run** - Generate and open HTML report after EVERY execution. No exceptions.
10. **Close browser** - Always `agent-browser close` when done.
11. **Generic names** - Test names describe what the element does ("Submit button is visible"), not app-specific terms.
12. **One script per feature** - Group related elements into logical scripts (navigation, forms, tables, etc.).
13. **Standalone + suite** - Each script works alone OR inside `run-all-tests.sh` via the `SUITE_MODE` flag.

## Operating Principles

- **Application-agnostic**: Works on any web app - no assumptions about framework, tech stack, or UI library.
- **Evidence-based**: Every test cites specific element refs discovered from live snapshots.
- **Non-destructive to app state**: Read-only tests by default (visibility, label checks). Form submissions and writes only when explicitly requested by user.
- **Cross-platform execution**: Uses WSL + agent-browser (works on Windows with WSL2).
- **Failure forensics**: Every failure captures screenshot + DOM snapshot for debugging.
- **Scalable**: Works from 10-element simple pages to 500+ element complex dashboards.

## Context

{ARGS}


**Telemetry**: Run: `polaris telemetry record regression-testing --feature <slug> --phase complete --agent {{AGENT_NAME}} --wp <WP_ID>`
