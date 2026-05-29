# Autopilot State Persistence Schema

State file: `.polaris/autopilot-state.json`

```json
{
  "feature_slug": "<slug>",
  "current_stage": "build.implement",
  "wp_order": ["WP01", "WP02"],
  "completed_wps": ["WP01"],
  "failed_wps": {},
  "current_wp": "WP02",
  "current_attempt": 1,
  "max_attempts": 3,
  "mode": "standard|quick",
  "on_failure": "skip-and-continue",
  "started_at": "<ISO>",
  "updated_at": "<ISO>",
  "build": {
    "test_plan": {"status": "complete|pending|skipped"}
  },
  "ship": {
    "test_execution": {
      "status": "passed|failed|skipped",
      "passed": 0, "failed": 0, "total": 0, "coverage_percent": 0
    }
  }
}
```

- **Resume**: `/polaris.autopilot --resume`
- **Abort**: `/polaris.autopilot --abort`
- State updated atomically after every stage transition.
