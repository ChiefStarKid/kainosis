# PRD: Load receipt: check the always-loaded context arrived whole

Issue: https://github.com/ChiefStarKid/kainosis/issues/8 · Stage: v0.2 · Labels: roadmap, km-audit

Idea from [Link](https://github.com/gowtham0992/link) by gowtham0992.

## Problem
If the index is cut short at load time, rules silently stop applying and the audit may read that as the model not needing them.

## Goal
Each audited session carries a receipt saying whether the always-loaded context arrived whole.

## Non-goals
- Repairing a truncated load.
- Reading more transcript text than triage already reads.

## Requirements
1. Define what 'whole' means: the index's final line and expected hub count appear in the session.
2. `km-audit` triage records a receipt per session it checks.
3. Sessions with a truncated load are excluded from retirement evidence and listed in the report.
4. Document the check in `docs/evals.md`.

## Data handling
Reads the same transcripts triage already reads, so no new data. Mention it in the audit's description of what it reads.

## Risks and open questions
- Index format changes break the 'whole' test. Keep it to a simple marker.

## Dependencies
None.

## Done when
`km-audit` reports a receipt per session and excludes truncated sessions from retirement evidence.
