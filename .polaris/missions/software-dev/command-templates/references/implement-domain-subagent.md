# Implement: Domain Expert and Subagent Protocols

## Domain Expert Check

Read the WP frontmatter `domain` field. If present:
1. Look for prompt at `.polaris/skills/superpowers/<domain>.md`; fall back to `src/specify_cli/superpowers/prompts/<domain>.md`
2. If found: read it. This is your domain expertise for the WP - follow its quality checklist, avoid its listed pitfalls, meet its output expectations.
3. If not found: proceed normally.

Domain expertise applies to ALL work on this WP, including any subagents spawned.

## Subagent Check

Read WP frontmatter. **If `subagents: true`:**

1. Read `subagent_groups` - each entry has `tasks` (subtask numbers) and optional `superpower`.
2. For each group, spawn one subagent (Agent tool) with:
   - **Superpower context**: read `.polaris/skills/superpowers/<superpower>.md` or `src/specify_cli/superpowers/prompts/<superpower>.md`; prepend as "## Domain Expert Role". Skip if not found.
   - Feature context: first 30 lines of `polaris-specs/<feature>/spec.md`
   - Plan context: only sections relevant to this group's subtasks
   - Assigned subtasks: copied in full detail
   - Permitted files: explicit list derived from subtask descriptions
   - Hard constraint: "Do not read or modify any file not in your permitted files list."
   - Output format: "(1) list of files modified, (2) one-sentence summary per subtask."
   - Depth constraint: "You are a subagent. Do NOT use the Agent tool. Use only Read, Write, Edit, Bash, Glob, Grep."
3. Launch all subagents simultaneously.
4. Wait for ALL to complete.
5. Resolve file conflicts: read all conflicting versions, produce merged result, log warning.
6. Commit all subagent work as a single consolidated commit.

**If `subagents: true` is NOT present:** proceed with normal sequential implementation.
