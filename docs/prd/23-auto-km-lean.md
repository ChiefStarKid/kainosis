# PRD: Auto km lean: safe unattended mode gated by objective checks

Issue: https://github.com/ChiefStarKid/kainosis/issues/23 · Stage: In progress (first slice in 0.4.0) · Labels: roadmap, km, data-handling

## Problem
`km lean` needs the owner at the keyboard. An unattended mode is only acceptable if its safety comes from objective checks, not from the model's own confidence.

## Goal
`km lean auto` writes the edits that pass objective checks without a question, holds everything else for the owner, and leaves one revert command per edit.

## Non-goals
- Writing anything the owner has not opted into for that run.
- Editing `MEMORY.md`, deleting, moving or superseding notes automatically.
- Pushing. A run never pushes.

## Requirements
1. Only create, append, insert a How-to-apply or Precedent line, or fix a one-line fact backed by a read-only check; every other kind is held.
2. Stored retrieval queries must still reach the same notes afterwards; no file becomes unreachable, no new dead link, no link removed. With no stored queries, inserts and fact fixes are held.
3. Frontmatter of an existing file stays byte-identical; `MEMORY.md` is never touched.
4. Always held: rule files about sending, deleting or publishing, weakening wording, text that did not come from the owner's own words, and edits over 1,500 characters.
5. Each run writes a digest: what was applied (one revert command each), what is held and why, options not recommended, warnings, and a prepared commit that is printed, not run.
6. The opt-in is the word `auto` in the command, needed every run.

## Data handling
Writes memory files without the owner present, only on `km lean auto` or an explicit `--opt-in`. Listed in the CHANGELOG 'Data handling' note and PRIVACY.md for 0.4.0. No network, no git, no push.

## Risks and open questions
- No live run yet: the hit rate needs a few real close-outs.
- The sending and weakening checks are word lists and are not airtight; the reachability and frontmatter gates do not depend on them.
- The `source` label on an edit is set by whatever builds the edit list, so owner-words-only rests on that step.

## Dependencies
#19 (verdict), #30 and #37 (skill size). Feeds #24.

## Done when
The gate, digest and `km lean auto` ship opt-in (done in 0.4.0); a few live runs are recorded with their hit rate on the issue; held and applied counts are reported honestly.
