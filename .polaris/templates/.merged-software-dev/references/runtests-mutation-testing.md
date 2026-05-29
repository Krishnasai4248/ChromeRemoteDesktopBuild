# Runtests Mutation Testing (Quality Gate)

Runs automatically after all tests pass, before a WP moves to `for_review`.

## How it works

1. Identify files changed in this WP via `git diff`
2. For each changed file, generate 3-5 targeted mutations:
   - Negate a conditional (`if x > 0` becomes `if x <= 0`)
   - Remove a function call or return statement
   - Change a boundary value (`>=` to `>`)
   - Swap a string literal or constant
3. For each mutation, run only the tests relevant to that file
4. Report **killed** (tests caught) vs **survived** (tests missed) mutants
5. If survival rate > 30%, add targeted tests to kill surviving mutants, then re-run

## Output

```
Mutation Testing Results
------------------------
Files mutated:    3
Mutations tested: 12
Killed:           10 (83%)
Survived:          2 (17%)

Surviving mutants:
  - auth_service.py:45 - changed >= to > (boundary check)
  - order_model.py:112 - removed validation call (missing negative test)

Verdict: PASS (survival rate 17% < 30% threshold)
```

## Threshold

Configurable in `.polaris/config.yaml`:
```yaml
testing:
  mutation_survival_threshold: 30  # max % surviving mutants allowed
```

Default: 30%. Set to 0 for strictest mode (all mutations caught). Set to 100 to disable.
