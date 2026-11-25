# PRD: Compaction starts lean: PreCompact hook runs a lean pass

Issue: https://github.com/ChiefStarKid/kainosis/issues/24 · Stage: Later · Labels: roadmap, km, hooks, data-handling

## Problem
A skill cannot start `/compact`, and automatic compaction saves nothing to memory. The owner must remember to run `km lean` first.

## Goal
Even automatic compaction saves something: a PreCompact hook runs a headless lean pass and returns the Keep list.

## Non-goals
- Running without opt-in and disclosure.
- Writing anything the #23 gate would hold.

## Requirements
1. A feasibility spike on three things before any build: headless `claude -p` auth inside Desktop, the hook timeout delaying compaction, and two sessions compacting at once.
2. If feasible: the hook reads `transcript_path`, runs the lean pass under the #23 gate, writes only what the gate passes, and returns the Keep list as compaction instructions.
3. A lock file so two compactions never write memory at once.
4. Opt-in, with the data handling disclosed.

## Data handling
Reads the session transcript and writes memory files from a hook. Needs a CHANGELOG 'Data handling' note and a PRIVACY.md update, and must be opt-in.

## Risks and open questions
- The directory policy on memory and cross-session behaviour (1.G) gets harder.
- A slow hook delays compaction.
- The headless auth route may not exist inside Desktop.

## Dependencies
#6 (PreCompact hook, done), #23 (the gate).

## Done when
The spike's result is written up; if feasible, the hook ships opt-in with a lock file and disclosure, and a bare `/compact` saves and keeps what a lean run would.
