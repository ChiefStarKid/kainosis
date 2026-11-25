# PRD: Beginner path: three levels and a Start here guide

Issue: https://github.com/ChiefStarKid/kainosis/issues/27 · Stage: Later · Labels: roadmap, docs

## Problem
The framework is written for people already deep in knowledge work. A newcomer meets rules, evals, probes and tags before they get any benefit.

## Goal
A newcomer gets value in five minutes and meets the rest only when they outgrow it.

## Non-goals
- Writing the README. The wording belongs to the README owner; this issue fixes the level definitions.

## Requirements
1. Level 1: `km lean` only, on defaults (no scope file, no evals, no probes). The promise is notes that survive `/compact`.
2. Level 2: full `km`, once there are a few dozen notes; corrections start becoming eval cases.
3. Level 3: `km-audit`: probes and retiring rules.
4. Optional beginner mode: accepts the recommended options and hides the tags, only if the #23 hit rate shows it is safe.
5. A 'Start here' and a 'When you outgrow it' split for the README owner to place.

## Data handling
None.

## Risks and open questions
- A beginner mode that hides tags could hide what is being saved; gate it on the #23 data.

## Dependencies
#23 (hit rate).

## Done when
The three levels are defined in the docs and the README owner has what they need for the split.
