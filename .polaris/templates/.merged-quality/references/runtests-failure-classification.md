# Runtests Failure Classification

## Classification Categories

| Category | Pattern Matches | Action |
|----------|----------------|--------|
| **environment** | `connection refused`, `port in use`, `ModuleNotFoundError`, `FileNotFoundError`, `PermissionError`, `command not found`, `ECONNREFUSED`, `EADDRINUSE` | Auto-retry once after 2s delay |
| **flaky** | Test passes on retry after initial failure | Tag with retry count, mark resolved |
| **stale-selector** | `element not found`, `no such element`, `waiting for selector`, `locator` | Flag for self-healing; do not retry |
| **genuine** | All other failures, or consistent failure on retry | Report with full error details |

## Auto-Retry Workflow

1. On first failure, classify error against patterns above.
2. If **environment**: wait 2s, retry once.
3. All other failures: retry once to detect flakiness.
4. Passes on retry: reclassify as **flaky** (`resolved=True`).
5. Fails again: keep original classification (`resolved=False`).
6. **stale-selector**: skip retry, flag for self-healing.

## Classification Summary Output

```
Failure Classification Summary
-------------------------------
genuine (2):     test_calculate_total, test_validate_input
environment (1): test_api_connection  [retried, still failing]
flaky (1):       test_race_condition  [resolved on retry]
stale-selector (0): (none)
```

## Programmatic Usage

```python
from specify_cli.testing.failure_classifier import classify_failure, should_retry, get_retry_delay

classification = classify_failure("test_api", "ConnectionRefusedError: ...")
if should_retry(classification):
    delay = get_retry_delay(classification)
    # wait delay seconds, then re-run
```
