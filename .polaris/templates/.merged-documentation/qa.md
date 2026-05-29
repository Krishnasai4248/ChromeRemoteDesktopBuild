---
description: Generate E2E tests from an Azure DevOps work item for QA engineers.
---
## Model Guidance

This command does planning work. Use **claude-opus-4-6** for this session.

Deep reasoning, synthesis, and decision-making here propagate to all downstream work. Opus-level reasoning is insurance, not indulgence.

If you are currently on Sonnet: switch to Opus before proceeding (`/model claude-opus-4-6`).

---


# /polaris.qa - E2E Test Generation from ADO Work Item

**Version**: 2026.3.4+
**Purpose**: QA-driven E2E test suite generation from ADO work items. Developer does not need Polaris.

## User Input

**Telemetry**: Run: `polaris telemetry record qa --feature <slug> --phase start --agent {{AGENT_NAME}}`

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Work Item ID Parsing

Parse work item ID from arguments. Supported formats:
- Numeric: `12345`
- Hash prefix: `#12345`
- AB prefix: `AB#12345`
- Full ADO URL: `https://dev.azure.com/{org}/{project}/_workitems/edit/12345`

Extract numeric ID. If none provided, ask:
> "Provide a work item ID. Formats: `12345`, `AB#12345`, or ADO URL."

End with `WAITING_FOR_QA_INPUT`.

## Prerequisites

### Token Pre-flight

Check `.polaris/memory/constitution.md` for configured issue tracker.

**ADO**: Verify `AZURE_DEVOPS_PAT` env var exists. Read org/project from `.polaris/config.yaml` under `ado:` or from env vars `AZURE_DEVOPS_ORG`, `AZURE_DEVOPS_PROJECT`.

If missing: show actionable error with setup instructions. End with `WAITING_FOR_QA_INPUT`.

### QA Configuration

Read `.polaris/config.yaml` for optional `qa:` section:

```yaml
qa:
  base_url: "https://staging.example.com"
  auth:
    env_username: "QA_USERNAME"
    env_password: "QA_PASSWORD"
    login_path: "/login"
```

Store values for use in discovery and generation. All optional.

## Fetch Work Item

Call ADO REST API:

```bash
python -c "
import json, os, sys, urllib.request, urllib.error, base64
pat = os.environ['AZURE_DEVOPS_PAT']
org_url = '{ORG_URL}'
project = '{PROJECT}'
wid = {WORK_ITEM_ID}
url = f'{org_url}/{project}/_apis/wit/workitems/{wid}?$expand=relations&api-version=7.0'
auth = base64.b64encode(f':{pat}'.encode()).decode()
req = urllib.request.Request(url, headers={'Authorization': f'Basic {auth}'})
try:
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    fields = data.get('fields', {})
    relations = data.get('relations', []) or []
    children = [r['url'].split('/')[-1] for r in relations
                if r.get('rel') == 'System.LinkTypes.Hierarchy-Forward' and r.get('url')]
    print(json.dumps({
        'id': data['id'],
        'title': fields.get('System.Title', ''),
        'type': fields.get('System.WorkItemType', ''),
        'state': fields.get('System.State', ''),
        'description': fields.get('System.Description', ''),
        'repro_steps': fields.get('Microsoft.VSTS.TCM.ReproSteps', ''),
        'acceptance_criteria': fields.get('Microsoft.VSTS.Common.AcceptanceCriteria', ''),
        'children': children
    }, indent=2))
except urllib.error.HTTPError as e:
    print(json.dumps({'error': f'HTTP {e.code}: {e.reason}'}), file=sys.stderr)
    sys.exit(1)
"
```

**Error handling**: 404 - wrong ID/project. 401/403 - bad PAT. Network - connectivity issue.

### Hierarchy Traversal

If work item has children (from relations):
1. Fetch each child work item using same API pattern
2. Aggregate acceptance criteria from parent + all children
3. Group by child for test scenario organization
4. Skip failed child fetches (warn, continue)

If no children: proceed with single work item.

## Auto-Amend Detection

Scan `polaris-specs/` for directories matching `qa-{id}-*`.

**If found** (amend mode):
1. Re-fetch ADO work item (criteria may have changed)
2. Read existing `spec.md`, diff current ADO criteria against it
3. For each criterion that changed: re-run the Testability Classification step and update the corresponding row in `test-plan.md`
4. For each affected `.e2e.js` file:
   - Check `git status` to determine whether the file has been manually edited since last generation
   - If edited AND criteria changed: present per-file choice (keep manual / accept regenerated / merge)
   - If unedited: regenerate silently
5. Update spec.md, regenerate affected tests
6. Append amendment entry to meta.json
7. Stage and commit all changes:
   ```bash
   git add polaris-specs/qa-{id}-{kebab-title}/
   git commit -m "test(qa): amend E2E suite for ADO#{id} - {N} scenarios modified"
   ```
8. Post ADO comment: "E2E tests updated. {N} scenarios modified, {M} unchanged."
9. Skip to Summary.

**If not found**: continue with creation flow.

## QA Discovery

Scale questions to work item richness (2-4 questions):

1. **Base URL**: Target environment URL. Suggest from `qa.base_url` config if available.
2. **Auth**: Does app require login? Roles to test? Credentials via env vars (default: `QA_USERNAME`, `QA_PASSWORD`).
3. **Test data**: Specific records, users, or states needed?
4. **Existing tests**: Any tests to avoid duplicating?

If acceptance criteria are detailed: minimize to 1-2 confirmations.

Present all questions as numbered list. End with `WAITING_FOR_QA_INPUT`.

### Criteria Gap-Fill (Non-skippable)

If acceptance criteria are sparse or missing:
1. Infer likely criteria from title, description, and work item type
2. Present suggested criteria as numbered list
3. QA confirms, adjusts, or adds
4. Record enriched criteria (attributed as "QA-enriched, not from ADO")

This step is a core part of the QA value proposition.

## Generate Artifacts

### Create Feature Directory

Build the slug: `qa-{id}-{kebab-title}`. If the total length exceeds 50 characters, truncate the kebab-title portion (not the id) until the full slug is 50 characters or fewer. Never truncate mid-word if avoidable - drop whole words from the end.

```bash
polaris agent feature create-feature "qa-{id}-{truncated-kebab-title}" --json
```

Parse: feature_dir, target_branch from command output.

### meta.json

Write to `{feature_dir}/meta.json`:

```json
{
  "slug": "qa-{id}-{kebab-title}",
  "friendly_name": "QA: {title}",
  "mission": "qa-testing",
  "ado_work_item": {"id": {id}, "type": "{type}", "title": "{title}", "url": "{ORG_URL}/{PROJECT}/_workitems/edit/{id}"},
  "created_at": "<ISO timestamp>",
  "target_branch": "<output of: git rev-parse --abbrev-ref HEAD>",
  "vcs": "git",
  "qa_discovery": {
    "base_url": "<from discovery>",
    "auth_required": false,
    "roles": [],
    "test_data": "<notes>"
  }
}
```

### spec.md (Testability-Focused)

Write `{feature_dir}/spec.md` with:
- Overview: what is being tested, ADO work item link
- Acceptance Criteria: from ADO + QA enrichments (with source attribution)
- Test Scenarios: derived from criteria, grouped by theme
- Auth Requirements: if applicable
- Data Prerequisites: test data needs
- Out of Scope: what this test suite does NOT cover

### test-plan.md

Write `{feature_dir}/test-plan.md`:
- Scenario table: ID, description, type (happy/error/edge), priority, testability (automatable/partially-automatable/not-automatable)
- Data requirements per scenario
- Auth matrix (roles x scenarios)

Note: testability column is filled in during the Testability Classification step below. Write the table rows initially, then update the testability column once classification is complete. Do not leave testability blank in the final file.

### Testability Classification (Required Before Writing Any Test)

For EVERY acceptance criterion or scenario, classify it before writing code:

| Class | Definition | Output |
|-------|-----------|--------|
| **automatable** | A browser action produces a verifiable, specific UI change | Write a real test with assertions that would fail if the feature broke |
| **partially-automatable** | Some aspects are verifiable in the browser, some are not | Write a test for the verifiable parts; add a `test.skip` for the parts that cannot be checked |
| **not-automatable** | No observable browser state can confirm or deny the criterion | Write `test.skip('{criterion}', () => { /* reason */ })` - do NOT write a hollow passing test |

**Not-automatable examples** - any criterion matching these MUST become `test.skip`, never a hollow passing test:
- Internal AI reasoning quality ("the agent understood the intent")
- Email, SMS, or webhook delivery
- Backend-only state that has no UI representation
- PDF / file contents that require download and parsing
- Cryptographic or security internals
- Race conditions or timing guarantees
- Audit log entries not surfaced in the UI
- Third-party service side effects

**The hollow-test rule**: if you cannot write an assertion that would FAIL when the feature is broken, the test must be `test.skip`. A test that always passes regardless of app state is worse than no test - it creates false confidence.

### Work Packages + .e2e.js Files

Group scenarios into WPs (by theme: happy path, error handling, edge cases, etc.).

For each WP, create:
1. `{feature_dir}/tasks/WP##-{group}.md` with frontmatter (work_package_id, lane: planned, ado_criteria)
2. `{feature_dir}/tests/e2e/WP##-{group}.e2e.js` with complete Playwright tests

**.e2e.js format**:

Every generated test MUST either contain real assertions that can fail, or be explicitly skipped with a reason. Never write a test body that always passes.

**Standard (synchronous) test pattern:**

```javascript
import { test, expect } from '@playwright/test';

test.describe('WP01: {group}', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(process.env.BASE_URL + '{path}');
    // CONDITIONAL: include the block below only if auth_required is true from QA discovery.
    // Remove entirely if the application does not require login.
    // await page.fill('[data-testid="username"]', process.env.QA_USERNAME);
    // await page.fill('[data-testid="password"]', process.env.QA_PASSWORD);
    // await page.click('[data-testid="login-btn"]');
    // await expect(page).toHaveURL(/dashboard/);
  });

  test('{scenario description}', async ({ page }) => {
    await page.click('[data-testid="{trigger-element}"]');
    await page.fill('[data-testid="{input-field}"]', '{test value}');
    await page.click('[data-testid="{submit-button}"]');
    // Assert the SPECIFIC expected outcome from the AC - not just that an element exists
    await expect(page.locator('[data-testid="{result-element}"]')).toContainText('{exact expected text from AC}');
    await expect(page.locator('[data-testid="{error-banner}"]')).not.toBeVisible();
  });

  // Example: criterion that cannot be verified in the browser
  test.skip('email confirmation is sent to the user', () => {
    // Not automatable via browser: email delivery cannot be observed in the UI.
    // Verify manually or via email API integration test.
  });
});
```

**Async-agent / AI response pattern - REQUIRED for all AI agent and Coworker interactions**

You MUST use this pattern for every test step that:
- Submits a prompt or task to any agent or Coworker component
- Waits for agent output, summary, status chip, or result to render
- Asserts the content or state of an agent response

**Prohibited alternatives** (these produce false-positive Passed results and are forbidden):
- A bare `await page.waitForTimeout(N)` as the sole wait for an agent response
- Asserting a response element without first waiting for the agent to reach a terminal state
- Using the standard synchronous test pattern for any scenario that involves an agent response

```javascript
import { test, expect } from '@playwright/test';

const AGENT_RESPONSE_TIMEOUT_MS = 30 * 60 * 1000; // 30 minutes - fail as performance issue if exceeded
const POLL_INTERVAL_MS = 5000;

async function waitForAgentResponse(page, completionLocator, failureLocator, options = {}) {
  // Fail immediately if any selector still contains an unreplaced template placeholder such as
  // {response-complete-indicator}. Without this check, the polling loop runs for the full
  // timeout (30 min) per call because the placeholder selector never matches the DOM.
  const placeholderRe = /\{[^}]+\}/;
  if (placeholderRe.test(completionLocator) || placeholderRe.test(failureLocator)) {
    throw new Error(
      `waitForAgentResponse: unreplaced template placeholder detected.\n` +
      `  completionLocator: ${completionLocator}\n` +
      `  failureLocator:    ${failureLocator}\n` +
      `Replace every {placeholder} with the actual data-testid selector from the application before running.`
    );
  }

  const timeout = options.timeout ?? AGENT_RESPONSE_TIMEOUT_MS;
  const interval = options.interval ?? POLL_INTERVAL_MS;
  const deadline = Date.now() + timeout;

  while (Date.now() < deadline) {
    const failed = await page.locator(failureLocator).isVisible().catch(() => false);
    if (failed) {
      throw new Error(`Agent/Coworker reported a failure state - element visible: ${failureLocator}`);
    }
    const done = await page.locator(completionLocator).isVisible().catch(() => false);
    if (done) return;
    await page.waitForTimeout(interval);
  }
  throw new Error(`Agent response not received within ${timeout / 60000} minutes - performance threshold exceeded`);
}

// Call this at the top of any test that uses selectors derived from template placeholders.
// It catches unreplaced {placeholder} values in page.fill / page.click targets early,
// so the test fails in milliseconds instead of timing out after 30 minutes.
function assertNoTemplatePlaceholders(...selectors) {
  const placeholderRe = /\{[^}]+\}/;
  for (const sel of selectors) {
    if (placeholderRe.test(sel)) {
      throw new Error(
        `Unreplaced template placeholder in selector: "${sel}"\n` +
        `Replace the {placeholder} value with the actual data-testid before running.`
      );
    }
  }
}

test.describe('WP0{N}: {group} - AI Agent / Coworker', () => {
  test.setTimeout(AGENT_RESPONSE_TIMEOUT_MS + 60_000); // 1 min buffer over the performance threshold

  test('{scenario description}', async ({ page }) => {
    await page.goto(process.env.BASE_URL + '{path}');

    await page.fill('[data-testid="{prompt-input}"]', '{task input}');
    await page.click('[data-testid="{submit-button}"]');

    // Wait until the agent signals completion or failure.
    // completionLocator: element that appears when the agent succeeds.
    // failureLocator: element that appears when the agent fails (error banner, status chip, retry prompt, etc.)
    await waitForAgentResponse(
      page,
      '[data-testid="{response-complete-indicator}"]',
      '[data-testid="{response-error-indicator}"]'
    );

    // Assert SPECIFIC content from the AC - not just that the container exists or is non-empty.
    // toBeVisible() alone is not sufficient - assert what the response should contain.
    await expect(page.locator('[data-testid="{response-container}"]')).toContainText('{specific keyword or phrase from AC}');
    await expect(page.locator('[data-testid="{error-banner}"]')).not.toBeVisible();
    await expect(page.locator('[data-testid="{status-chip}"]')).toHaveText('{expected status label}');
  });

  // Example: aspect of agent behaviour that cannot be observed in the UI
  test.skip('agent internally selects the optimal tool for the task', () => {
    // Not automatable: internal tool-selection logic is not surfaced in the UI.
    // Covered by unit tests in the agent service layer.
  });
});
```

**Date/time picker pattern** - use the sub-pattern that matches the component type in the application under test:

```javascript
// --- Pattern A: Native <input type="date"> or <input type="time"> ---
// Use fill() to set the value directly on native inputs.
// After fill, read back the input value and assert it matches what was entered.

const targetDate = '2026-06-15'; // ISO format (YYYY-MM-DD) for date inputs
await page.fill('[data-testid="{date-input}"]', targetDate);
// REQUIRED: verify the field accepted the value - some pickers silently reject out-of-range dates
const displayedDate = await page.inputValue('[data-testid="{date-input}"]');
await expect(displayedDate).toBe(targetDate);


// --- Pattern B: Calendar overlay (click-to-open, month/day/year navigation) ---
// Open the picker, navigate to the target month, click the target day, then verify the display.

await page.click('[data-testid="{date-trigger-button}"]');
await expect(page.locator('[data-testid="{calendar-overlay}"]')).toBeVisible();

// Navigate to the correct month if needed (adjust click count for your target date)
await page.click('[data-testid="{calendar-next-month}"]');

// Click the target day cell
await page.click('[data-testid="{calendar-day-cell}"][aria-label="{target-date-aria-label}"]');

// REQUIRED: verify the selected date is displayed in the field/label after picker closes
await expect(page.locator('[data-testid="{date-display-field}"]')).toContainText('{expected-date-display-text}');
// REQUIRED: verify the picker closed
await expect(page.locator('[data-testid="{calendar-overlay}"]')).not.toBeVisible();


// --- Pattern C: Formatted text field (MM/DD/YYYY or HH:MM AM/PM) ---
// Clear the field first, type the formatted value, tab out to trigger validation,
// then verify the displayed value matches the entered value.

await page.fill('[data-testid="{datetime-text-input}"]', '');
await page.type('[data-testid="{datetime-text-input}"]', '{formatted-date-or-time}');
await page.keyboard.press('Tab'); // trigger any blur/validation handlers
// REQUIRED: verify the displayed value matches - some fields reformat on blur
const displayedValue = await page.inputValue('[data-testid="{datetime-text-input}"]');
await expect(displayedValue).toBe('{expected-formatted-value}');
```

**Rules for assertion quality:**
- Assertions must use SPECIFIC expected values from the AC (text, URLs, counts, status labels). Never assert only that an element exists or is visible without also checking its content or state.
- `toBeVisible()` alone is FORBIDDEN as a sole assertion - it passes even if the feature is completely broken, as long as the element is rendered. Always pair it with `toContainText`, `toHaveText`, `toHaveValue`, or `toHaveAttribute`.
- `not.toBeEmpty()` is FORBIDDEN - whitespace or a loading spinner satisfies it. Use `toContainText('{specific string}')` instead.
- Every test that cannot meet these rules MUST be `test.skip` with a one-line reason explaining why it cannot be automated.
- Use `data-testid` selectors by default. Fall back to ARIA roles (`getByRole`) when testid is unavailable.
- For AI-agent/coworker scenarios, always use the async-agent pattern above with `waitForAgentResponse` and `test.setTimeout`.
- **Date/time verification**: After interacting with any date or time picker, you MUST assert the displayed value matches the entered value before the test continues. Checking that the picker closed (`not.toBeVisible()`) or that the field is non-empty is NOT sufficient - some pickers silently reject out-of-range values without displaying an error.
- **Placeholder detection**: Every generated `.e2e.js` file MUST call `assertNoTemplatePlaceholders(...)` at the top of each test body, passing every selector that was derived from a `{placeholder}` in the template. This ensures the test fails in milliseconds - instead of timing out after 30 minutes - when the engineer has not yet replaced the placeholder with a real data-testid. Example:
  ```javascript
  test('{scenario}', async ({ page }) => {
    assertNoTemplatePlaceholders(
      '[data-testid="{prompt-input}"]',
      '[data-testid="{submit-button}"]',
      '[data-testid="{response-complete-indicator}"]',
      '[data-testid="{response-error-indicator}"]',
    );
    // ... rest of the test
  });
  ```
  Remove a selector from the list once you have replaced it with an actual testid.
- **Await enforcement**: Every Playwright API call that returns a Promise MUST be `await`ed. Missing `await` causes the call to appear to run but its result is never checked, producing false-positive Passed results. The following calls must never appear in generated test code without `await`:
  - `page.click()`, `page.fill()`, `page.goto()`, `page.type()`, `page.keyboard.press()`, `page.inputValue()`
  - `page.waitForTimeout()`
  - `waitForAgentResponse()`
  - All `expect(...).toXxx()` assertion calls
- **Intermediate step verification**: Every action with a side effect (click, fill, navigation, selection) MUST be followed by a verification that the action took effect before the next step begins. Acceptable verifications: a URL change assertion, a visibility assertion on a newly appeared element, or a value/text assertion on the interacted element. Example:
  ```javascript
  await page.click('[data-testid="submit-btn"]');
  // REQUIRED: verify the result before continuing - do not proceed if this fails
  await expect(page.locator('[data-testid="confirmation-panel"]')).toBeVisible();
  await expect(page.locator('[data-testid="confirmation-message"]')).toContainText('{expected text}');
  ```
  A test that proceeds past a failed intermediate step will report Passed even though subsequent steps never executed correctly.

**Before writing the .e2e.js file**, produce a brief classification table in your response:

```
Scenario                              | Class                | Assertion type / skip reason
--------------------------------------|----------------------|------------------------------
User sees confirmation message        | automatable          | toContainText('Order confirmed')
Email sent to user                    | not-automatable      | email delivery not visible in UI
Agent returns relevant answer         | partially-automatable| toContainText(keyword); skip internal ranking
```

This makes coverage gaps visible to the QA engineer before they run the suite.

CRITICAL: Never write actual credential values. Always use `process.env.{VAR_NAME}`.

### Gitignore Check

Check whether `.gitignore` in the repo root contains an entry covering `.env` files.

If the entry is missing:
1. Append `.env` and `.env.*` to `.gitignore`
2. Stage the change: `git add .gitignore`
3. Note: this change will be included in the commit step below

If `.gitignore` does not exist, warn the QA engineer to create one before committing credentials. Do not block the rest of the flow.

## ADO Write-back

Post comment on work item via ADO REST API:
"E2E test suite created by QA via Polaris. {N} test scenarios across {M} work packages. Spec: polaris-specs/qa-{id}-{title}/"

Non-blocking: warn on failure, continue.

## Commit

```bash
git add polaris-specs/qa-{id}-{kebab-title}/
git add .gitignore
git commit -m "test(qa): generate E2E test suite for ADO#{id} - {title}"
```

Note: `git add .gitignore` is harmless if `.gitignore` was not modified.

## Summary

Display:

```
E2E Test Suite Generated: AB#{id} - {title}
  Artifacts: spec.md, test-plan.md, {N} WPs, {M} .e2e.js files
  Scenarios: {total} ({happy} happy, {error} error, {edge} edge, {skipped} skipped/not-automatable)
  Location:  polaris-specs/qa-{id}-{kebab-title}/

Next steps:
  1. Review generated tests in polaris-specs/qa-{id}-{kebab-title}/tests/e2e/
  2. Review skipped tests - each has a comment explaining why it cannot be automated
  3. Run /polaris.runtests to execute the automatable tests
  4. Push and create PR when satisfied
```

**Files to commit vs gitignore**: If untracked `.polaris/` files exist:
- **Commit**: polaris-specs/ entries, .polaris/config.yaml, .polaris/memory/
- **Gitignore**: .polaris/.dashboard, .polaris/telemetry/, .polaris/autopilot-state.json

## Cross-Platform Notes

All commands used here are Polaris CLI commands, Python one-liners, or git operations that work on Windows, macOS, and Linux. No shell-specific commands are used.

**Telemetry**: Run: `polaris telemetry record qa --feature <slug> --phase complete --agent {{AGENT_NAME}}`
