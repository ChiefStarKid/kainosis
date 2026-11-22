# PRD: Full evolution history in docs/evolution.md

Issue: https://github.com/ChiefStarKid/kainosis/issues/2 · Stage: Later · Labels: roadmap, docs

## Problem
v0.1 ships a short dated list. A reader cannot see why each design choice exists or what it replaced.

## Goal
Each design choice has a date, the constraint or failure behind it and the alternative it replaced.

## Non-goals
- Rewriting the README argument.
- Documenting private project history.

## Requirements
1. List every design choice the README names (hub-and-spoke, basis tags, pointer sources, retirement, probe-vs-transcript rule).
2. For each: date, trigger, decision, what it replaced.
3. Strip anything private before publishing; link only to public sources.
4. Link the page from the README.

## Data handling
None.

## Risks and open questions
- Source notes may hold private context. Scrub before publishing.

## Dependencies
None.

## Done when
`docs/evolution.md` covers every choice the README names, each dated with a reason, and the README links to it.
