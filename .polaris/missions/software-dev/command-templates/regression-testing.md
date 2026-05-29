# Regression Testing

Run the project's existing regression test suite and handle failures intelligently.

## Steps

**Telemetry**: Run: `polaris telemetry record regression-testing --feature <slug> --phase start --agent {{AGENT_NAME}} --wp <WP_ID>`


1. **Discover test files** using `git ls-files` or the agent's search tools.
   Look for files matching common patterns: `*.spec.js`, `*.spec.ts`,
   `*_test.py`, `test_*.py`, `*.test.js`, `*.test.ts`.

2. **Execute the test suite** with the project's configured runner
   (e.g., `pytest`, `npx playwright test`, `npm test`).

3. **Classify failures** into categories:
   - **environment** -- missing dependency, network timeout, port conflict
   - **flaky** -- passes on retry (retry up to 2 times)
   - **stale-selector** -- element not found / selector mismatch
   - **genuine** -- real logic or assertion failure

4. **Report results** in a summary table with pass/fail/skip counts and
   failure classifications.

## Self-Healing Element Re-discovery

When a test fails because an element cannot be found (stale-selector category),
attempt automatic re-discovery **before** marking the test as failed.

### Procedure

1. **Detect selector failure**: look for errors like "Element not found",
   "No element matches selector", "Timeout waiting for selector", or
   similar messages from Playwright / Selenium / Cypress.

2. **Gather page context**: inspect the current page to collect a list of
   candidate elements with their tag, id, class, text content, attributes,
   parent tag, and sibling tags.

3. **Attempt fuzzy matching** using three signals:
   - **Text content** (40% weight) -- compare the text of the original
     element with candidate elements using fuzzy string matching.
   - **Attribute similarity** (30% weight) -- compare id, class, name,
     and data-* attributes using Jaccard similarity.
   - **DOM proximity** (30% weight) -- compare parent/sibling structure
     to find elements in the same DOM neighbourhood.

4. **Evaluate confidence**: compute the weighted confidence score.
   - **>= 80%**: accept the new selector, update the test script
     automatically, and re-run the failing test.
   - **< 80%**: classify as a genuine failure and route to human review.
     Do NOT auto-update the script.

5. **Log all healing actions** to `.polaris/self-healing/<feature-slug>.jsonl`,
   recording the test name, original selector, new selector, confidence,
   match method, element context, and whether the script was updated.

6. **Create a backup** of the test file (`.spec.js.bak`) before making
   any automatic selector updates.

### Reporting Healed Selectors

At the end of the test run, include a **Self-Healing Summary** section that
lists every selector that was automatically repaired:

| Test | Original Selector | New Selector | Confidence | Method |
|----## Model Guidance

This command does implementation work. Use **claude-sonnet-4-6** for this session.

Execution against a defined plan - this is where call volume lives and where savings compound.

---

--|-------------------|--------------|------------|--------|
| ... | ... | ... | ... | ... |

If any selectors were below the 80% threshold, list them separately under
**Selectors Requiring Human Review** so the developer can investigate.


**Telemetry**: Run: `polaris telemetry record regression-testing --feature <slug> --phase complete --agent {{AGENT_NAME}} --wp <WP_ID>`
