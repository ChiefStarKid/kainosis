# PRD: Last-used report per memory file and skill (report only)

Issue: https://github.com/ChiefStarKid/kainosis/issues/18 · Stage: Later · Labels: roadmap, km-audit

## Problem
`km-audit` flags files as `idle` but does not show how much each memory file or skill is actually used.

## Goal
An audit report of reads per memory file, skill invocations and the last-used date, from transcripts the audit already scans.

## Non-goals
- Using the numbers as a reason to retire anything.
- Reading any new data source.

## Requirements
1. Count reads per memory file, skill invocations and last-used date from the transcripts triage already scans.
2. Label the numbers as informational wherever they appear: they never justify retirement.
3. Keep the existing evidence rule: retire only on probe and transcript evidence that the model no longer needs the rule.
4. Test with a synthetic fixture: a used file, an unused file and a rare critical rule that stays.
5. Document the report and the rule in `docs/evals.md`.

## Data handling
Reads the same transcripts triage already reads; the counts appear in the local audit report only. No change.

## Risks and open questions
- A report invites misuse as a delete list. The labelling and the fixture for a rare critical rule are the guard.

## Dependencies
Benefits from #8. Idea from Devin (Cognition), whose Dreaming step deletes notes no session used; the Kainosis plugin deliberately does not.

## Done when
`km-audit` reports reads, invocations and last-used date, labels them informational, never uses them as a retirement reason, and a test proves a rare critical rule stays.
