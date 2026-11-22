# PRD: More graph checkers and schema clean-ups

Issue: https://github.com/ChiefStarKid/kainosis/issues/7 · Stage: Later · Labels: roadmap, graph, km

## Problem
Several checks are still manual and some warnings are false: older rules lack a `Trigger:` line, hubs are asked for a **Why:** they do not need, and the compaction path-bytes cap is uncalibrated.

## Goal
Fewer manual checks and fewer false warnings in close-out and audit.

## Non-goals
- Changing the hub-and-spoke model.
- Adding dependencies beyond the Python standard library.

## Requirements
1. Four more checker scripts alongside `km_graph_check.py` (stdlib only; each named and scoped in its own issue before building).
2. A `Trigger:` backfill pass for older rules.
3. Exempt hubs from the Why requirement in the checker and `docs/schema.md`.
4. Calibrate the compaction path-bytes cap against real graphs.

## Data handling
Checkers read memory files and write nothing, so no change.

## Risks and open questions
- Scope creep. Split each item into its own issue before building.

## Dependencies
None.

## Done when
Each item is shipped or split into its own issue, the schema doc matches, and the example graph still checks clean.
