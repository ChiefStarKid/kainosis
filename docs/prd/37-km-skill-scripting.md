# PRD: km skill: script the deterministic checks, fix lean load and the case check contract

Issue: https://github.com/ChiefStarKid/kainosis/issues/37 · Stage: Next · Labels: roadmap, km

## Problem
A review of the km skill after #30 found that a lean run loaded far more than intended, the case `check` instructions contradicted `km_close.py`, and nothing ran the verdict check script. More of the skill is mechanical and can move into scripts.

## Goal
The skill carries judgement; scripts carry the mechanical checks; a lean run loads only what it uses.

## Non-goals
- Moving safety rules out of the skill: owner-words-only, never SAFE on an unverified claim, weak-evidence delete stay in SKILL.md.
- Splitting the skill per mode.

## Requirements
1. Steps 1 and 2 (done, in 0.4.0): the case `check` contract matches the script; the verdict script runs at Step 9; a lean run no longer reads the verdict doc.
2. Step 3: `scripts/km_lint.py`, report-only, the mechanical parts of Behaviours D, E, G and H.
3. Step 4: a commit-and-output script run last: stages only the paths the run wrote, refuses `.`, prints the hash and the closing block; push stays in the skill.
4. Step 5: the remaining full-only stubs move into `docs/km-full.md`; the zero-candidate rule lives in one place.
5. Step 6: a `GRAPH` preflight mode replacing three Error handling rows.
6. `SKILL.md` stays under 18,000 bytes committed and a lean run's always-loaded bytes are measured and stated.

## Data handling
No new data read or written beyond what `km` already does; the commit script runs `git` locally. Each script ships with its tests and a Data handling note if that changes.

## Risks and open questions
- A moved step is skipped silently if its pointer is skipped; each pointer says when to read it.
- The commit script reopens the #30 decision to keep the commit in the skill: ordering, scope-file push rules and failure visibility in Step 9 must still hold.
- Whether an invoked skill body survives `/compact` is unverified.

## Dependencies
#30 (merged), #38 (steps 1-2, merged).

## Done when
Steps 3 to 6 are merged with tests, a fresh-session live lean and full run pass, `SKILL.md` stays under 18,000 B, and the lean load is measured.
