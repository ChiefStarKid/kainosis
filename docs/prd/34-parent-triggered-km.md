# PRD: Parent-triggered km verdict and lean, with a readable result

Issue: https://github.com/ChiefStarKid/kainosis/issues/34 · Stage: Next · Labels: roadmap

## Problem
`km` can only be started by the owner typing it in the session being closed. Closing out a group of related sessions means opening each one. Three limits showed up while closing out sessions that had been started from a parent session:
1. A session that has loaded the km skill cannot reload it ("Skill already loaded; instructions unchanged"), so a long-lived session runs old text after the plugin moves on.
2. Candidates and cases come only from the owner's own turns. A session whose task came from another session has none, so a full `km` collapses to a verdict-only run: SAFE, nothing written.
3. Nothing lets a parent request a close-out, a lean offload or a verdict, and nothing writes the result where the parent, or a tool that archives only SAFE sessions, can read it.

A fourth hazard was found in the live tests: when the memory folder sits inside a larger git repo, Step 8's `git add -- .` stages every uncommitted memory file, including another session's unfinished work. Parallel or parent-triggered runs make it worse.

## Goal
A parent can request `km verdict` (and `km lean`) of a child and read a short, checkable result from a file, without the parent ever becoming a source of rules, and without the owner losing the Q&A.

## Non-goals
- Auto-confirming candidates or bypassing the owner's Q&A. The gate from #23 stays the model for what may apply without a question.
- Letting a parent's message supply rules, cases or candidates (owner-words-only, #10, stays).
- Reading other sessions' history. The child reads only its own conversation.
- Sending messages between sessions. That is the host's job; the plugin defines what a child does when asked.

## Requirements
1. **`km verdict` mode.** Runs the verdict-only path (loose-ends sweep, graph check, verdict) with no Q&A and no memory writes. It accepts `--report <file>`.
2. **Result file.** Written to the path the caller gives, never to the memory folder. Content: verdict (`SAFE`, `NOT SAFE` or `SAFE TO COMPACT`), blockers with the action that clears each, counts (candidates, cases, files written), session id, date, and the plugin version and `SKILL.md` size the session loaded. Slugs and file names only; no transcript text.
3. **Checkable.** A script validates the file's shape and that the verdict follows from the blockers (extends `km_verdict_check.py`). The file is a claim, not proof: a reader treats a missing or invalid file as NOT SAFE.
4. **`km lean` by request.** A parent may request it. Candidates still come only from the child's own owner turns; with none, the run reports "no owner turns" and falls back to verdict-only. The Q&A stays with the owner; a parent request never confirms anything.
5. **Reload limit.** The child reports which version and size of `SKILL.md` it loaded. The docs say that a trigger sent to a long-lived session may run old text, and that a parent comparing the reported version with the current one starts a fresh session when they differ.
6. **Commit staging.** Step 8 stages only the paths the run wrote; `km_close.py` prints them. This applies to every run, not only triggered ones.
7. **Tests.** A child with no owner turns produces no candidates; the trigger text never appears as a candidate's source; the result-file check rejects a SAFE verdict with open blockers; a run in a memory folder with unrelated uncommitted files commits only its own paths.

## Data handling
Writes one small result file to a caller-chosen path outside the memory folder. It holds a verdict, blockers, counts and the version loaded, with slugs and file names but no transcript text. It reads nothing from other sessions. Needs a CHANGELOG 'Data handling' note and a PRIVACY.md sentence at release.

## Risks and open questions
- Overlap with #13 (root-led close-out): that issue has leaves propose and a root write once; this one is the trigger and the readable result. Decide whether `km verdict` is the leaf side of #13 or stays separate.
- A parent could be wrong to trust the file: a child can misreport. Mitigation is requirement 3 and the NOT SAFE default.
- Where the result file lives by default, and who reads it (a parent session, a grooming tool). The plugin names the format; the caller names the path.

## Dependencies
#19 (verdict check), #23 (gate model), #13 (root-led close-out), #30 (skill size, merged).

## Done when
A parent can request a verdict from a child and read the result from a file; a trigger never writes a rule or a case by itself; the reload limit is documented with how a stale skill is detected; Step 8 stages named paths only; the tests above pass in CI.
