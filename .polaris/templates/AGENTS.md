# Agent Rules for Polaris Projects

**⚠️ CRITICAL**: All AI agents working in this project must follow these rules.

These rules apply to **all commands** (specify, plan, research, tasks, implement, review, merge, etc.).

---

## 1. Path Reference Rule

**When you mention directories or files, provide either the absolute path or a path relative to the project root.**

✅ **CORRECT**:
- `polaris-specs/001-feature/tasks/WP01.md`
- `/Users/robert/Code/myproject/polaris-specs/001-feature/spec.md`
- `tasks/WP01.md` (relative to feature directory)

❌ **WRONG**:
- "the tasks folder" (which one? where?)
- "WP01.md" (in which lane? which feature?)
- "the spec" (which feature's spec?)

**Why**: Clarity and precision prevent errors. Never refer to a folder by name alone.

---

## 2. UTF-8 Encoding and ASCII Punctuation Rule (MANDATORY)

**NEVER use em dashes, smart quotes, or non-ASCII punctuation.** See CLAUDE.md for the full rule. The pre-commit hook blocks violations.

Use `polaris validate-encoding --feature <id> --fix` to auto-repair encoding issues.

---

## 3. Context Management Rule

**Build the context you need, then maintain it intelligently.**

- Session start (0 tokens): You have zero context. Read plan.md, tasks.md, relevant artifacts.  
- Mid-session (you already read them): Use your judgment-don't re-read everything unless necessary.  
- Never skip relevant information; do skip redundant re-reads to save tokens.  
- Rely on the steps in the command you are executing.

---

## 4. Work Quality Rule

**Produce secure, tested, documented work.**

- Follow the plan and constitution requirements.  
- Prefer existing patterns over invention.  
- Treat security warnings as fatal-fix or escalate.  
- Run all required tests before claiming work is complete.  
- Be transparent: state what you did, what you didn't, and why.

---

## 5. Git Discipline Rule

**Keep commits clean and auditable.**

- Commit only meaningful units of work.
- Write descriptive commit messages (imperative mood).
- Do not rewrite history of shared branches.
- Keep feature branches up to date with main via merge or rebase as appropriate.
- Never commit secrets, tokens, or credentials.

---

## 6. Git and Branch Protection

**NEVER bypass git hooks.** If a pre-commit hook blocks your commit, read the error and fix the issue. Never use `--no-verify`. Only humans may bypass for hotfixes.

**NEVER commit source code to main/master.** Use feature branches. Planning artifacts (`polaris-specs/`, `.polaris/`, `docs/`) are allowed on protected branches.

**Agent directories (`.claude/`, `.codex/`, etc.) are committed in customer projects** (they contain command templates, not credentials). Polaris adds them to `.gitignore` only in the Polaris source repo itself.

---

### Quick Reference

- 📁 **Paths**: Always specify exact locations.  
- 🔤 **Encoding**: UTF-8 only. Run the validator when unsure.  
- 🧠 **Context**: Read what you need; don't forget what you already learned.  
- ✅ **Quality**: Follow secure, tested, documented practices.  
- 📝 **Git**: Commit cleanly with clear messages.