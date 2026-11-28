# PRD: km lean auto: the gate must run, and the run must prove it

Issue: https://github.com/ChiefStarKid/kainosis/issues/39 · Stage: Next · Labels: roadmap, km

## Problem
`km lean auto` relies on the gate (`km_auto_gate.py`) to decide which edits may be written without a question. The instruction to gate the edits is prose. In the first live run on 0.4.0 the session read the gate's instructions and source, did not run it, decided by itself that the candidate would be held, wrote the note by hand, and reported "Gate: it held the note". No digest or revert command existed, and the report read as if the gate had run.

## Goal
In `lean auto` the gate always runs, a run that skipped it cannot reach `SAFE TO COMPACT`, and the report states only what the gate printed.

## Non-goals
- Making `lean auto` apply more edits. It applies only edits sourced from the owner's own words (#10, #23).
- Triggering `/compact`. A message from one session to another arrives as a peer note, not a command (tested once, declined).

## Requirements
1. In `lean auto` the gate runs on every candidate edit and writes its digest file to the OS temp dir.
2. `km_verdict_check.py` takes the digest path for a `lean auto` run and refuses `SAFE TO COMPACT` when it is missing, unreadable, or does not list the edits the run wrote.
3. The "Gate:" line of the report is copied from the gate's output.
4. `docs/auto-km-lean.md` states the limit: where the facts come from Claude's own work, `lean auto` behaves like a normal lean; auto applies only to edits sourced from the owner's words.
5. Tests: a `lean auto` ledger with no digest is refused; a digest that omits a written edit is refused; a held edit appears as held in the digest.

## Data handling
No change to what the plugin reads, writes or sends. The digest is the existing temp-dir file.

## Dependencies
#23 (gate), #19 (verdict check), #37 (scripting). Touches `skills/km/SKILL.md` (small), so it follows the live test of the current text.

## Done when
A `lean auto` run that skips the gate cannot reach `SAFE TO COMPACT`; the report quotes the gate; the limit is documented; the tests pass in CI. Until then, #23 stays In progress and the 0.4.1 notes list this as a known problem.
