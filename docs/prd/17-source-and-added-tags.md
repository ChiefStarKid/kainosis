# PRD: Source and added tags per memory node

Issue: https://github.com/ChiefStarKid/kainosis/issues/17 · Stage: Later · Labels: roadmap, km, graph, data-handling

## Problem
A memory node does not say where it came from or when. After the fact, the owner-words-only rule (#10) cannot be audited, and the audit has no age signal.

## Goal
`km` records a small source and date for every new or updated node.

## Non-goals
- Back-filling older nodes.
- Storing transcript text; only a reference.

## Requirements
1. Define a `source` and `added` entry in `docs/schema.md`: for example 'owner turn, session <id>' or 'approved tool result: <source>', plus the date.
2. `km` writes it for every new or updated node.
3. Keep it small: state the byte cost per node; prefer one frontmatter line.
4. `km_graph_check.py` accepts the field; the example graph shows one.

## Data handling
Stores a session reference in memory files, which changes what the plugin writes. Needs a CHANGELOG 'Data handling' entry and a PRIVACY.md update in the same release.

## Risks and open questions
- Always-loaded bytes grow with every node. Measure before shipping and keep the field optional on hubs.

## Dependencies
Complements #10 (owner words only) and #12 (supersedes). Idea from Devin (Cognition).

## Done when
Schema, `km`, checker and example graph use the field, the byte cost is stated, and PRIVACY.md and the CHANGELOG say a session reference is stored.
