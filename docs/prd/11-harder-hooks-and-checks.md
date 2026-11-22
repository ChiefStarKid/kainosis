# PRD: Harder hooks and checks: match commands as the shell runs them

Issue: https://github.com/ChiefStarKid/kainosis/issues/11 · Stage: Later · Labels: roadmap, hooks

Idea from [Link](https://github.com/gowtham0992/link) by gowtham0992.

## Problem
A pattern matched on raw tool input is easy to slip past, even by accident, and a hook the agent can edit is not a guard.

## Goal
Graduated hooks and `check` patterns match commands as the shell will run them, and cannot be edited by the agent.

## Non-goals
- Claiming a sandbox; this reduces accidents, not a determined attacker.

## Requirements
1. Split compound commands (`&&`, `;`, pipes) and unwrap `bash -c` and `sudo` before matching.
2. Tests covering chains, `bash -c` and `sudo` on each shipped example.
3. Deny agent edits to the hook files themselves.
4. Document what is and is not covered.

## Data handling
None. Hooks inspect commands locally.

## Risks and open questions
- Shell parsing edge cases. Document limits instead of promising completeness.

## Dependencies
Pairs with #5.

## Done when
Example hooks parse compound commands before matching, have tests, protect their own files and document limits.
