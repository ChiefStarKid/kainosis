# PRD: End-of-thread chain: km, then compact or archive

Issue: https://github.com/ChiefStarKid/kainosis/issues/26 · Stage: Later · Labels: roadmap, km

## Problem
After `km`, an owner often compacts the thread or archives it. Compact is for a thread that carries on; archive is for one that is finished. Nothing connects the close-out to that choice.

## Goal
A short end-of-thread flow, offered and never forced: `km`, then compact (with the Keep list) or archive, and only a SAFE thread may be archived.

## Non-goals
- Archiving or compacting without the owner's choice.
- Archiving a thread whose verdict is not SAFE.

## Requirements
1. After the verdict, offer the next step that fits: compact with the Keep list, or archive.
2. Archive is offered only for a SAFE verdict (#19); NOT SAFE shows what clears it.
3. Not every `km` ends this way; the flow is skippable.

## Data handling
None beyond what `km` already reads and writes.

## Risks and open questions
- Archiving is a Desktop action; the plugin can only offer it.
- Needs #19 to have had real use first.

## Dependencies
#19, #6, #24.

## Done when
The flow is designed, offered after a SAFE verdict, and never archives anything that is not SAFE.
