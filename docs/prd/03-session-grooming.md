# PRD: Session grooming as an optional extra (Desktop-only)

Issue: https://github.com/ChiefStarKid/kainosis/issues/3 · Stage: Later · Labels: roadmap, km-audit, data-handling

## Problem
Old sessions cost memory and clutter search, but some are the evidence behind eval cases and must never be deleted.

## Goal
An opt-in extra that archives stale sessions with a searchable catalogue, protects evidence sessions and proposes noise-thread deletes for approval.

## Non-goals
- Deleting anything without per-item approval.
- Working outside Claude Desktop.
- Shipping the delete step without the keep-list.

## Requirements
1. Archive stale sessions (idle over N days, not pinned, transcript present, no dirty worktree) and write a searchable per-profile catalogue.
2. Keep a list of sessions cited as eval evidence; the archive and delete steps skip them.
3. Propose deletes of noise threads one by one; the owner approves each.
4. The keep-list and the delete step ship in the same release.
5. Off by default.

## Data handling
Reads session titles, ids and transcripts in the Desktop data folder; writes a catalogue file and archive flags; deletes only on approval. Needs the README table, a CHANGELOG 'Data handling' entry and a PRIVACY.md update.

## Risks and open questions
- Desktop's data layout changes without notice. Detect it and stop rather than guess.
- A wrong evidence list loses evidence. Verify the list before any delete.

## Dependencies
Desktop session store format.

## Done when
The extra ships opt-in with keep-list and delete together, every delete needs approval, and the privacy documents are updated.
