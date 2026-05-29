---
description: Integrate Aptean Intelligent Workflow into your project - trigger workflow instances, handle callbacks, and manage business process automation.
---


## User Input

**Telemetry**: Run: `polaris telemetry record workflow --feature <slug> --phase start --agent claude`


```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Apply the Polaris **workflow** skill to the current project in a single guided flow - entirely inside Claude. This command is equivalent to `/polaris.skill workflow` and follows the same 10-step process.

## ⚠️ CRITICAL - Read This First

**NEVER run `polaris skill apply workflow` or any `polaris skill` terminal command.**

Everything happens here, inside Claude. No terminal commands are needed.

---

## Execution

This command applies the `workflow` skill. Follow the exact same steps as `/polaris.skill` with `workflow` pre-selected as the skill name.

Proceed directly to **Step 2** of the `/polaris.skill` flow (project analysis) - skip the skill selection question in Step 1 since the skill is already known: **`workflow`**.

The workflow skill:
- Connects your app to **Aptean Intelligent Workflow** (business process automation)
- Scaffolds a typed workflow client, webhook callback handler, and API endpoints
- Uses **Aptean IAM** for authentication - if the `iam` skill is not yet applied, note this in the plan
- Asks one config question: **trigger only / webhook only / both**

Follow all steps from the `/polaris.skill` template starting at Step 2, substituting `workflow` for `<skill-name>` throughout.

## Context

$ARGUMENTS


**Telemetry**: Run: `polaris telemetry record workflow --feature <slug> --phase complete --agent claude`
