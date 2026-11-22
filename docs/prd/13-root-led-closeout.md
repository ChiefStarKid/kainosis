# PRD: Root-led close-out for multi-session work

Issue: https://github.com/ChiefStarKid/kainosis/issues/13 · Stage: Later · Labels: roadmap, km, data-handling

## Problem
With several sessions running, each closes out alone with a partial view: stale whole-file rewrites overwrite newer memory, lessons are captured twice, sessions share one git index and a commit sweeps up another's work, and corrections are lost when a session is archived without a close-out.

## Goal
Each session proposes; one root session merges and writes once.

## Non-goals
- Reading other sessions' history by default.
- Letting a leaf session write memory.

## Requirements
1. `km propose` runs in a leaf before it ends or compacts and writes a structured proposal file (candidates, cases with model and session id, evidence) and no memory.
2. Root `km` collects proposals from its linked sessions, removes duplicates, resolves conflicts, asks the owner once, then makes a single write and a single commit.
3. Fallback: a targeted transcript read for leaves that ended without proposing.
4. Fallback: with no root, solo close-out under an edit-never-rewrite rule plus a lock file in the memory dir.
5. Cross-session reading is opt-in and off by default.

## Data handling
Reads other sessions' chat history, which Anthropic's directory policy 1.G covers. Needs the README table, CHANGELOG 'Data handling' and PRIVACY.md, and should be raised in the directory correspondence.

## Risks and open questions
- A leaf that never proposes loses its corrections unless the fallback runs.
- Pilot results are pending; the design may change.

## Dependencies
Manual pilot results; directory reply.

## Done when
`km propose` and root merge work, both fallbacks work, and cross-session reading is opt-in and documented.
