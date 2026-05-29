# Tasks Subagent Eligibility

Loaded on demand when evaluating WPs for parallel subagent execution.

## Eligibility Criteria (ALL must be true)

1. WP has 5 or more subtasks total
2. At least 3 subtasks are verifiably independent (different files, no sequential dependency)
3. Each independent subtask is substantial (not a trivial 1-2 line change)
4. You can partition independent subtasks into groups with ZERO file overlap between groups

If ALL four criteria met, add to WP frontmatter:

```yaml
subagents: true
subagent_groups:
  - tasks: [1, 2]
    superpower: "database-expert"
  - tasks: [3, 4]
    superpower: "api-design"
  - tasks: [5, 6]
```

Each entry has `tasks` (subtask T-numbers) and optional `superpower` (domain expert name).

## Superpower Assignment

Available built-in superpowers:
- `database-expert` - Database migrations, schema design, query optimization
- `api-design` - REST/GraphQL API design, OpenAPI specs, auth patterns
- `frontend-craft` - React/Vue components, CSS, accessibility
- `backend-logic` - Business logic, service layer, data processing
- `testing-specialist` - Test strategy, fixtures, mocking, coverage
- `devops-infra` - CI/CD pipelines, Docker, Helm, infrastructure
- `documentation` - API docs, user guides, architecture docs

Rules:
- Assign if the majority of a group's subtasks belong to one domain
- Omit if no clear majority (run as generic subagent)
- Never force-assign; when in doubt, leave it out

## Safety Rules (non-negotiable)

- When in doubt, do NOT set `subagents: true`. Safety over speed.
- If you cannot guarantee zero file overlap, do NOT flag the WP.
- Unflagged WPs execute sequentially - no penalty for not flagging.
