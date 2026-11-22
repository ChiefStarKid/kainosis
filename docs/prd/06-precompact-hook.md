# PRD: Opt-in example PreCompact hook for km lean

Issue: https://github.com/ChiefStarKid/kainosis/issues/6 · Stage: On hold · Labels: roadmap, hooks, km, data-handling

## Problem
`km lean` ends with a paste-ready `/compact Keep:` line. Pasting it is the one manual step left. Claude Code cannot start a compaction from a skill or hook (upstream: anthropics/claude-code#19877).

## Goal
A hook that returns `km lean`'s Keep list as compaction instructions, so a bare `/compact` carries it.

## Non-goals
- Starting a compaction automatically.
- Enabling the hook by default.
- Dropping the paste-ready line; it stays either way.

## Requirements
1. `km lean` writes the Keep text to `<temp dir>/claude/km-keep.txt` only when the owner has said in the session that they run the hook.
2. The hook reads that file and returns it as compaction instructions.
3. Passes one real `/compact` test with the Keep list visibly carried through.
4. Ships as an opt-in example, not registered by the plugin.

## Data handling
Writes one file to the temp dir and adds a hook example. Needs a 0.1.1 version bump, a CHANGELOG 'Data handling' entry and a PRIVACY.md update.

## Risks and open questions
- A stale keep file could feed a later auto-compaction. That is why the skill writes it only on the owner's statement.

## Dependencies
A real `/compact` test. Draft change exists in history; restore with `git revert 2e4e62b`.

## Done when
One real `/compact` test passes, the hook ships opt-in, and the 0.1.1 release steps are done.
