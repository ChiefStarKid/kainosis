# PRD: Supersession at write time: a supersedes: field

Issue: https://github.com/ChiefStarKid/kainosis/issues/12 · Stage: v0.2 · Labels: roadmap, km, graph

Idea from [Link](https://github.com/gowtham0992/link) by gowtham0992.

## Problem
The audit's contradiction pass judges every pair that might conflict. A revised fact does not say what it replaced.

## Goal
A revised node names the file it supersedes, so the audit skips pairs already resolved.

## Non-goals
- Auto-deleting the superseded file.
- Back-filling old nodes.

## Requirements
1. `docs/schema.md` defines `supersedes:`.
2. `km` writes it when a close-out revises an existing node.
3. `km-audit` skips pairs a `supersedes:` already resolves.
4. The example graph shows one.

## Data handling
Adds one frontmatter field in memory files. No new data read or sent.

## Risks and open questions
- A wrong `supersedes:` hides a real contradiction. The audit should still list skipped pairs.

## Dependencies
None.

## Done when
Schema, `km`, `km-audit` and the example graph all use `supersedes:`.
