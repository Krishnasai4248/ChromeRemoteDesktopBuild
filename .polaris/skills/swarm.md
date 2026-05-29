# Polaris Swarm & Memory Guardrail

This guardrail adds swarm orchestration and persistent cross-session memory to every
polaris command. All sections are **additive** - they run **before and after** the
normal command workflow. They never replace or override existing command instructions.

---

## Section 0: Command Router

**WHEN**: At the very start of every polaris command invocation, before Section 1.

Identify the active command and look it up in the routing table below. Set two variables:
- `SWARM_CLASS`: The resolved class (A / B / C / D)
- `PRIMARY_ROLE`: The primary agent type for dispatch (Class A/C only; `-` for Class B and D)

If the command is not found in the table, default to **Class A** with
`PRIMARY_ROLE = architect` and log:
`[polaris-swarm] Unknown command - defaulting to Class A.`

### Routing Table

| Command | Class | Primary Role |
|---------|-------|-------------|
| `/polaris.specify` | A | architect |
| `/polaris.clarify` | A | architect |
| `/polaris.plan` | A | architect |
| `/polaris.tasks` | A | architect |
| `/polaris.restructure` | A | architect |
| `/polaris.constitution` | A | architect |
| `/polaris.research` | A | researcher |
| `/polaris.analyze` | A | analyst |
| `/polaris.assess` | A | analyst |
| `/polaris.standards` | A | reviewer |
| `/polaris.devops` | A | coder |
| `/polaris.integrate` | A | coder |
| `/polaris.newapp` | A | coder |
| `/polaris.newmcp` | A | coder |
| `/polaris.scaffold` | A | coder |
| `/polaris.healthcheck` | A | coder |
| `/polaris.migrate` | A | coder |
| `/polaris.skill` | A | coder |
| `/polaris.implement` | B | - |
| `/polaris.review` | C | reviewer |
| `/polaris.accept` | C | reviewer |
| `/polaris.checklist` | C | reviewer |
| `/polaris.merge` | D | - |
| `/polaris.onboard` | D | - |
| `/polaris.runtests` | D | - |
| `/polaris.status` | D | - |
| `/polaris.dashboard` | D | - |

### Class D Passthrough

If `SWARM_CLASS == D`:

1. Print: `[polaris-swarm] Passthrough - no swarm for this command.`
2. Proceed to Section 2 (memory recall) - run normally.
3. Execute the command's normal workflow immediately.
4. **Skip** Sections 3, 4, 5, 6 (swarm init and all dispatch sections).
5. Run Section 7 (memory write) and Section 8 (telemetry) as normal.
   Use `"mode": "single-agent"` and `"agents_used": 1` in telemetry.

For Class A, B, and C: proceed to Section 1.

---

## Section 1: Health Check

**WHEN**: Before any polaris command begins work. Run this first.

```bash
npx @claude-flow/cli@latest doctor 2>&1 | grep -q "✓" && echo "SWARM_AVAILABLE" || echo "SWARM_UNAVAILABLE"
```

- **SWARM_AVAILABLE** → set `SWARM_ENABLED=true`. Print: `[polaris-swarm] Swarm enabled.` Proceed to Section 2, then Section 3, then the normal command workflow.
- **SWARM_UNAVAILABLE** → enter **Fallback Mode** (below) and skip Sections 3-5.

### Fallback Mode (swarm unavailable)

1. Print: `[polaris-swarm] ⚠ Swarm unavailable - running in single-agent mode.`
2. Attempt Section 2 (memory recall) - if memory also fails, skip it silently and print:
   `[polaris-memory] ⚠ Memory recall skipped.`
3. Execute the command's normal workflow as a single agent - output is format-identical to swarm mode.
4. Write Section 8 telemetry with `"mode": "fallback"` and `"agents_used": 1`.

The command **must never fail** because swarm infrastructure is unavailable.

---

## Section 2: Memory Recall (Command Start)

**WHEN**: Immediately after Section 1 passes. Run **before** any creative work begins.

Search both namespaces (run both queries):

```bash
# Feature-scoped: prior decisions for this feature
npx @claude-flow/cli@latest memory search \
  --query "decisions and context relevant to the current command" \
  --namespace "<feature-slug>" --limit 5

# Global: cross-feature architectural patterns
npx @claude-flow/cli@latest memory search \
  --query "architectural patterns and principles relevant to this work" \
  --namespace "global" --limit 3
```

Replace `<feature-slug>` with the active feature's directory name
(e.g., `001-polaris-swarm-multi-agent-memory`).

**Using recalled context**:
- Incorporate recalled decisions into working context before producing output.
- If a recalled entry conflicts with the current spec: surface the conflict to the
  developer, then treat the **most recent entry** as authoritative.
- Feature namespace takes priority over global namespace on any conflict.
- If memory is unavailable: print `[polaris-memory] ⚠ Memory recall skipped.` and continue.

---

## Section 3: Swarm Initialization

**WHEN**: After Section 2, if SWARM_AVAILABLE.

```bash
# For /polaris.implement (WP-level parallelism - up to 8 agents):
npx @claude-flow/cli@latest swarm init \
  --topology hierarchical --max-agents 8 --strategy specialized

# For all other commands (specialist swarm - up to 4 agents):
npx @claude-flow/cli@latest swarm init \
  --topology hierarchical --max-agents 4 --strategy specialized
```

Consensus model: `raft`. The coordinator holds authoritative state.

---

## Section 4: Command-Level Specialist Dispatch

**APPLIES TO**: All **Class A** and **Class C** commands (see Section 0 routing table).

**NOT USED BY**: Class B (`/polaris.implement`) - uses Section 5 instead.
Class D commands - use passthrough (Section 0).

**WHEN**: After Section 3, for the commands listed above.

Spawn 3 specialist sub-agents in **ONE Task tool message** (all parallel - do not split
across multiple messages):

| Role | Agent Type | Responsibility |
|------|-----------|----------------|
| Researcher | `researcher` | Query memory (Section 2 results), gather prior artifacts, surface relevant prior decisions |
| Primary | `PRIMARY_ROLE` (from Section 0 routing table) | Produce the main output artifact (spec.md, plan.md, tasks.md, review findings, etc.) |
| Reviewer | `reviewer` | Validate output against spec FRs, prior decisions, and template requirements |

**Collecting results** (wait - do NOT poll mid-way):
1. Wait for all 3 agents to complete.
2. Coordinator synthesises their outputs into the final artifact (see Section 6).
3. If a specialist fails: complete using remaining agents; note the missing specialist
   in the artifact's Assumptions section.

---

## Section 5: WP-Level Parallel Dispatch

**APPLIES TO**: `/polaris.implement` ONLY

**WHEN**: After Section 3.

### Step A - Parse Dependency Graph

Read all `polaris-specs/<feature>/tasks/WP*.md` files.
Extract `depends_on` from each file's YAML front matter:

```yaml
---
wp: WP02
lane: planned
depends_on: [WP01]   # absent or [] = independent
---
```

Build a directed graph: WP → depends_on edges.

### Step B - Detect Circular Dependencies

Run a topological sort over the graph. On cycle detected:

```
[polaris-swarm] ❌ Circular dependency: <cycle>. Falling back to sequential.
```

Fall back to sequential single-agent execution for all WPs in the feature.

### Step C - Dispatch Independent WPs

All WPs with empty or absent `depends_on` → dispatch **simultaneously** in **ONE
Task tool message**. Example:

```
[SINGLE MESSAGE - all three in parallel]
Agent A: polaris implement WP01
Agent B: polaris implement WP03
Agent C: polaris implement WP05
```

**Never call the Task tool multiple times for different WPs - always one message.**

### Step D - Dispatch Dependent WPs

Monitor lane status. When a WP transitions to `for_review` or `done`:
- Check if any queued WP's full `depends_on` list is now satisfied.
- If yes: dispatch that WP immediately.
- If active agent count would exceed `maxAgents` (8): queue and dispatch when a slot frees.

### Step E - Handle WP Agent Failure

If a WP agent fails mid-execution:
- Revert that WP's lane to `planned`.
- Print: `[polaris-swarm] ⚠ WP## agent failed - reverted to planned.`
- All other WP agents continue unaffected.

---

## Section 6: Result Synthesis & Conflict Resolution

**WHEN**: After all sub-agents (Section 4) or WP agents (Section 5) complete.

**For command-level swarms (Section 4)**:
- Coordinator merges researcher context + primary artifact + reviewer feedback into
  the final output artifact.
- Conflict resolution: most-recent specialist output wins; the losing output is logged
  in the artifact's Assumptions section.
- The final artifact **must be format-identical** to what single-agent execution produces.
  No new sections, no extra headings - same structure, richer content.

**For WP-level swarms (Section 5)**:
- Each WP agent writes independently to its own worktree. No synthesis needed.
- Coordinator reports completion status to the developer.

---

## Section 7: Memory Write (Command End)

**WHEN**: After the final output artifact is written to disk.

Write key decisions to the feature namespace:

```bash
npx @claude-flow/cli@latest memory store \
  --key "<feature-slug>/<command>/decisions" \
  --value "<2-5 sentence summary of key decisions made this session>" \
  --namespace "<feature-slug>" \
  --tags "<command>,decisions,<YYYY-MM-DD>"
```

If a general architectural pattern was discovered this session, promote it to global:

```bash
npx @claude-flow/cli@latest memory store \
  --key "global/patterns/<domain>" \
  --value "<pattern description>" \
  --namespace "global"
```

### Memory Key Schema

| Scope | Key pattern | Example |
|-------|-------------|---------|
| Feature-scoped | `<slug>/<command>/<artifact>` | `001-my-feature/plan/architecture` |
| Global patterns | `global/patterns/<domain>` | `global/patterns/auth` |

**Rules**:
- Always use the feature slug as the namespace for feature entries.
- Always use `global` as the namespace for cross-feature patterns.
- Search both namespaces at Section 2 (command start).
- Write to feature namespace at Section 7 (command end).
- At `/polaris.merge`: all feature-scoped entries become `status=archived`; global entries persist.

---

## Section 8: Telemetry

**WHEN**: At command completion - both swarm mode and fallback mode.

Append one JSON line to `~/.polaris/telemetry/events.jsonl`:

```json
{
  "event": "swarm_command_complete",
  "command": "<command-name>",
  "feature": "<feature-slug>",
  "mode": "swarm",
  "agents_used": <count>,
  "timestamp": "<ISO 8601 UTC>"
}
```

Use `"mode": "fallback"` and `"agents_used": 1` when running in single-agent fallback mode.

---

*End of Polaris Swarm & Memory Guardrail*
