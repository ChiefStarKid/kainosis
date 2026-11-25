# PRD: Graph granularity: research, then typed links and validity fields

Issue: https://github.com/ChiefStarKid/kainosis/issues/29 · Stage: Later · Labels: roadmap, graph

## Problem
Links only say 'related'. A note cannot say it replaces or conflicts with another, when a fact was true, or where it came from. Retrieval tests reuse the target note's own words, so a miss on a reworded request would go unseen.

## Goal
Measure first, then add the smallest fields that fix what the measurement shows, with Markdown in git as the source of truth.

## Non-goals
- A separate graph database: it adds a server and breaks the privacy and beginner cases.
- Automatic link-writing or note-rewriting (it would break owner-words-only and git review).
- Entity pages.

## Requirements
1. Fix 1: add pure-paraphrase queries to the retrieval set, run the never-run cases, fix the case that points at a deleted note, and measure how often current search misses.
2. Fix 2: typed links `supersedes` and `contradicts`, written by `km` close-out with the owner's yes.
3. Fix 3: `as_of` and `valid_until` on project and status notes, plus a lint for expiring wording with no `as_of`.
4. Fix 4: a `source:` field on reference and project notes, shared with #17, plus a lint for figures or dates with no source.
5. Fix 5: a description-overlap lint, merged with the contradiction lint (with #7).
6. Fix 6: a duplicate-merge count recorded per audit.
7. Fix 7: size caps on the `MEMORY.md` index and on each hub (with #20).
8. Fix 8: a SQLite index generated from the Markdown, built only after fixes 2 to 4 exist and produce data to query.

## Data handling
Fixes 2 to 5 add frontmatter fields the plugin writes at close-out with the owner's yes; fix 8 would write a local generated file kept out of git. Each ships with a CHANGELOG 'Data handling' note.

## Risks and open questions
- If paraphrase misses persist after the descriptions are fixed, the next step is local embeddings, not a database.
- The figures behind the plan come from one owner's graph.

## Dependencies
#25, #17, #7, #20.

## Done when
Fix 1's measurement is published; each later fix ships only if the measurement or a lint shows the gap.
