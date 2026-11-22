# PRD: Capture cases and rules from the owner's words only

Issue: https://github.com/ChiefStarKid/kainosis/issues/10 · Stage: v0.2 · Labels: roadmap, km, km-audit, data-handling

Idea from [Link](https://github.com/gowtham0992/link) by gowtham0992.

## Problem
Memory loads into every session, so it is a prompt-injection target. A rule written from text in a web page, file or command output would persist and apply everywhere.

## Goal
Cases and correction candidates come only from the owner's own turns. Anything else needs the owner to see its source first.

## Non-goals
- Ignoring tool results entirely; they can still support a fact the owner confirms.
- Blocking the owner from pasting text into their own turn.

## Requirements
1. `km` and `km-audit` take case and correction candidates only from owner turns.
2. A candidate whose wording came from a tool result is shown with its source and needs explicit approval before it is written.
3. Keep skill additions short; they load into context.
4. Document the rule in `docs/`; add a source field to case records only if needed, and keep the example graph clean.

## Data handling
Narrows what is written to memory. Needs a CHANGELOG 'Data handling' entry and a PRIVACY.md note.

## Risks and open questions
- Owner turns can contain pasted untrusted text. The source display is the safeguard.

## Dependencies
Release with #5.

## Done when
Both skills capture only from owner turns, tool-result candidates need source-visible approval, and the rule is documented.
