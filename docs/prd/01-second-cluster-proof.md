# PRD: Prove the rules-separation method on a second cluster

Issue: https://github.com/ChiefStarKid/kainosis/issues/1 · Stage: Later · Labels: roadmap, km-audit, docs

## Problem
v0.1 results come from one rule cluster on one profile. It is unknown whether tagging by basis, probing and retiring generalises or only fitted that cluster.

## Goal
A second cluster of a different kind goes through the full method, with before/after numbers published next to the first.

## Non-goals
- Changing the method to fit the second cluster's results.
- Claiming statistical proof; this is a second data point.

## Requirements
1. Pick a second cluster that differs in kind from the first (different tool family or domain).
2. Tag every rule with a `basis`; probe the `compensation` rules on at least two models.
3. Retire what probes and transcripts show is no longer needed; record rule count, always-loaded bytes and pass rates before and after.
4. Write the result in `docs/` and update 'Results so far' in the README.

## Data handling
None. Uses existing probe and audit behaviour.

## Risks and open questions
- The second cluster may have too few compensation rules to be informative. Choose it by rule count first.

## Dependencies
None.

## Done when
A second cluster's numbers are published in `docs/` beside the first and the README results section is updated.
