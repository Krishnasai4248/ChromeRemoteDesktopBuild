# Specify Amend Workflow

Full amend workflow for `--amend` mode. See missions version for complete step-by-step procedure.

Key steps:
1. Detect target feature (`polaris agent feature list-in-progress --json`)
2. Check amendment ambiguity; ask 1-3 targeted questions if needed
3. Propose affected spec sections and plan artifacts; confirm before writing
4. Apply cascade: update spec sections, plan artifacts, regenerate pending WPs
5. Post-amendment regression review on non-updated sections
6. Record amendment (`polaris agent feature record-amendment ...`) and commit

STOP after Step 4 summary. Do not continue to Discovery Gate.
