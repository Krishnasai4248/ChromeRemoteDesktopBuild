# Review - Multi-Persona Pass Details

Full criteria for the 3 mandatory review passes in `/polaris.review`.

## Pass 1: Security Review

Load expertise from `.polaris/skills/superpowers/security-reviewer.md` (project) or `src/specify_cli/superpowers/prompts/security-reviewer.md` (builtin). Use its focus areas, checklist, and pitfalls.

Mindset: Application Security Engineer. Review ALL changed code for:

1. **Injection** - SQL injection, XSS, command injection, path traversal
2. **Auth** - Missing auth checks, privilege escalation, broken access control
3. **Secrets** - Hardcoded API keys, tokens, passwords, connection strings
4. **Input validation** - Missing/insufficient validation at system boundaries
5. **Data exposure** - Sensitive data in logs, error messages, API responses, comments

Per finding: file, line, vulnerability type, severity (Critical/High/Medium/Low), fix.

**Pass 1 Verdict: PASS or FAIL** (FAIL if any Critical or High)

---

## Pass 2: Performance Review

Load from `.polaris/skills/superpowers/perf-engineer.md` or builtin. Use its criteria.

Mindset: Performance Engineer. Review ALL changed code for:

1. **DB patterns** - N+1 queries, missing indexes, unbounded SELECT
2. **Algorithm** - O(n^2) or worse, nested iterations over large collections
3. **Resources** - Unclosed connections/streams/handles, missing cleanup in error paths
4. **Caching** - Missing cache for expensive repeated ops, no invalidation strategy
5. **Memory** - Growing collections, event listeners not removed, large object retention

Per finding: file, line, issue type, impact (High/Medium/Low), fix.

**Pass 2 Verdict: PASS or FAIL** (FAIL if any High impact)

---

## Pass 3: Standard Code Review

Load from `.polaris/skills/superpowers/standard-reviewer.md` or builtin. Use its criteria.

Review ALL changed code for:

1. **Style** - Consistent naming, formatting, project conventions
2. **Test coverage** - New/changed code has tests, edge cases covered
3. **Error handling** - Happy path AND error paths, meaningful messages
4. **Documentation** - Changed public APIs documented, non-obvious logic commented
5. **Backward compat** - No breaking changes to public interfaces without migration path

Per finding: file, line, issue type, fix.

**Pass 3 Verdict: PASS or FAIL** (FAIL if tests missing for new code or breaking changes undocumented)

---

## Review Summary Table

Output after all 3 passes:

```
## Review Summary

| Pass | Verdict | Required | Blocking |
|------|---------|----------|----------|
| Security | PASS/FAIL | yes/no | yes/no |
| Performance | PASS/FAIL | yes/no | yes/no |
| Standard | PASS/FAIL | yes/no | yes/no |

**Overall: APPROVED / REJECTED**
```

- **APPROVED**: all required passes are PASS
- **REJECTED**: any required pass is FAIL -> list items to fix per pass under "### Items to Fix"
