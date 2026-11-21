# Scope rule file

Optional. Set its path in the plugin's `scope_rule_file` option. Both skills read it once per run and apply it to every candidate. Use it when one person keeps separate Claude Code profiles (say, work and personal, each with its own config dir) and each profile's memory must stay in its lane.

Plain markdown. Say, in short bullets:
- **What this profile covers**, and how to tell from the session whether the work was in scope.
- **What never gets a discard proposal** (files owned by another profile or team).
- **How out-of-scope facts are recorded**, if at all (e.g. abstracted, no client names or figures).
- **Where work for another profile goes** (e.g. a brief in a notes folder plus a one-line prompt to open there).
- **Push policy** for the memory repo: whether `km` pushes after committing, and to which branch.
- **MEMORY.md byte target**, if not the default 17,000.

Example:

```markdown
# Scope: personal profile
- In scope: side projects, learning notes, home admin. A session that only touched the employer's systems is out of scope: record nothing but cases.
- Never propose discarding files named `work_*` (owned by the work profile's runs).
- Employer facts that surface here go into the relevant project note abstracted: no customer names, no figures.
- Work that needs real employer data: write a brief to `~/notes/handover/` and give me a one-line prompt for the work profile.
- Push: after commit, push to branch `personal`; never `main`.
- MEMORY.md target: 15,000 bytes.
```

Keep it short: the skills read the whole file every run.
