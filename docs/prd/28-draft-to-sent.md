# PRD: Draft-to-sent as a correction source and outcome measure

Issue: https://github.com/ChiefStarKid/kainosis/issues/28 · Stage: Later · Labels: roadmap, km, data-handling

## Problem
`km` learns only from corrections stated in chat. Most of an expert's style is shown by editing drafts, not by stating it.

## Goal
Learn from how the owner edits Claude's drafts, and use shrinking edits as an outcome measure.

## Non-goals
- Writing a style rule without the owner's yes.
- Publishing the owner's own style rules or phrase checkers; those stay private.

## Requirements
1. Compare each draft Claude produced with what the owner sent or committed.
2. Sort each change the way `km` sorts candidates: style rule, one-off context, fact fix.
3. Roll repeated patterns up into a style rule with its examples linked under it.
4. Every lesson needs the owner's yes (the sent text arrives through a tool, so owner-words-only applies).
5. Report the edit size over time as an outcome measure (with #25).

## Data handling
Reads sent items or commits to compare with drafts. Needs a CHANGELOG 'Data handling' note and a PRIVACY.md update, and must be opt-in.

## Risks and open questions
- Reading sent mail widens what the plugin touches; opt-in and clearly disclosed.
- Edits that reflect a changed mind, not a style rule, would be mistaken for patterns.

## Dependencies
#10 (owner words only), #25 (outcome measure).

## Done when
The comparison runs opt-in on one artefact type, every lesson is confirmed by the owner, and the edit-size trend is reported.
