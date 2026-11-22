# PRD: Published error rates for each check

Issue: https://github.com/ChiefStarKid/kainosis/issues/9 · Stage: Later · Labels: roadmap, km-audit, probe

Idea from [Link](https://github.com/gowtham0992/link) by gowtham0992.

## Problem
Verdicts are only as trustworthy as their error rates. v0.1 saw a rule pass its probes while transcripts showed it broken in 614 of 1,073 shell calls.

## Goal
Each audit run reports how often its checks were wrong.

## Non-goals
- Changing any verdict logic.
- Publishing individual transcripts.

## Requirements
1. Count retire-candidates later found still needed.
2. Count probe verdicts that transcripts contradict; keep this as a standing metric in `runs.md`.
3. Count triage correction hits that were false.
4. Define each count in `docs/evals.md`.

## Data handling
Counts only, written to `runs.md` inside the memory dir. No new data leaves the machine.

## Risks and open questions
- Small samples make rates noisy. Report the denominator with every rate.

## Dependencies
Benefits from #8.

## Done when
`runs.md` carries each error rate per audit run and `docs/evals.md` defines how each is counted.
