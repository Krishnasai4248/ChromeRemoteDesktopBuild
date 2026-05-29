# Specify Amend Workflow

Full amend workflow for `--amend` mode. Loaded on demand by specify.md.

## Extract Inputs from $ARGUMENTS

- Amendment text: quoted string immediately after `--amend`
- Feature override: value of `--feature <slug>` if present
- Skip confirm: `--yes` flag means skip confirm/adjust and ambiguity steps

## Step 1 - Detect Target Feature (skip if `--feature <slug>` provided)

```bash
polaris agent feature list-in-progress --json
```

Parse `features` array:
- 0 features: print "No in-progress features found." and STOP
- 1 feature: confirm with user (y/n)
- 2+ features: print numbered list, ask which to amend

Set `FEATURE_SLUG` and `FEATURE_DIR`.

**Check if all WPs are done:** If `wp_summary.planned + wp_summary.doing == 0`, warn that amendment is a historical record only (`WP_REGEN_ENABLED=false`).

## Step 1.5 - Detect Amendment Ambiguity (skip if `--yes`)

Ambiguous when ANY: references entities without naming them, spans domains without specifying scope, uses removal language without specifying what, contains comparison without reference point.

Unambiguous when ALL: named entities explicitly referenced, action and target clear, no reasonable alternative interpretation.

If ambiguous: generate 1-3 targeted questions (scope/entities/boundaries only, not implementation). End with `WAITING_FOR_AMEND_CLARIFICATION`. After answers, proceed to Step 2.

If unambiguous: proceed directly to Step 2.

## Step 2 - Propose Affected Sections

Read `FEATURE_DIR/spec.md` fully. Identify impacted spec sections (User Scenarios, Success Criteria, Functional Requirements, Key Entities, Out of Scope) and plan artifacts (data-model.md, contracts/, plan.md, quickstart.md, research.md).

Multi-concern: apply inference independently per concern, union the affected sections. False-positive suppression: only include artifacts clearly affected; narrower is better.

Identify pending WPs (planned/doing) and locked WPs (done/for_review).

Present to user (no files written until confirmation):
```
Proposed amendment to: <slug>
Amendment: "<text>"
Spec sections to update: <list>
Plan artifacts to regenerate: <list or "none">
WPs to regenerate (<N> pending): <list>
WPs protected (<M> locked): <list>
Confirm? (y / section names to adjust / n to cancel)
```

If `--yes`: skip prompt, proceed as if "y". Wait for response. Max 2 adjustment rounds.

## Step 3 - Apply Cascade (writes begin here)

**3a.** Rewrite ONLY confirmed spec sections. Preserve all others verbatim.

**3b.** Update plan artifacts only if relevant (data-model.md, contracts/, plan.md, quickstart.md).

**3c.** Regenerate pending WPs (skip if `WP_REGEN_ENABLED=false`): rewrite Objective, Subtasks, DoD only; preserve frontmatter; add `amend_history` entry with `amendment_id: "TBD"`.

**3d.** Net-new scope: if amendment introduces requirements no pending WP can absorb, create `FEATURE_DIR/tasks/WP<NN>-<slug>.md` and update tasks.md WP Summary table.

**3e.** Post-amendment regression review: re-read full updated spec.md. Check non-updated sections for orphaned entity references, scope boundary conflicts, invalidated success criteria, orphaned edge cases.
- No issues: print "Regression review: No regressions detected."
- Issues found: print report with options (a) auto-fix, (b) proceed anyway, (c) cancel. If `--yes`: default to (a).

**3f.** Record amendment:
```bash
polaris agent feature record-amendment --feature <slug> --text "<text>" --affected-sections "<s1>,<s2>" --wps-regenerated "<WP04>" --wps-locked "<WP01>" --wps-created "<WPN>" --plan-files "<data-model.md>" --json
```
Update any `amendment_id: "TBD"` entries with the actual ID.

**3g.** Commit:
```bash
git add polaris-specs/<slug>/
git commit -m "amend(<feature-number>): <first 60 chars of amendment text>"
```

## Step 4 - Print Summary

```
Amendment applied: <amendment_id>
  Feature: <slug>
  Spec sections updated: <list>
  Plan artifacts updated: <list or "none">
  WPs regenerated: <list or "none">
  WPs protected (locked): <list>
  WPs created: <list or "none">

Run /polaris.autopilot to continue implementing pending WPs.
```

STOP. Do not continue to Discovery Gate or planning phases.
