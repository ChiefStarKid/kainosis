# PRD: bare_probe.py beyond Windows

Issue: https://github.com/ChiefStarKid/kainosis/issues/4 · Stage: Later · Labels: roadmap, probe, data-handling

## Problem
Rule probes are the strongest evidence for retiring a rule, but the runner needs pywin32 and Windows Credential Manager, so only Windows users get them.

## Goal
The same probe run and one-time token setup on macOS and Linux.

## Non-goals
- Storing the token in a plain file.
- Changing what a probe sends.

## Requirements
1. macOS: store the token in Keychain. Linux: use the Secret Service (libsecret) where present.
2. No pywin32 import off Windows.
3. Token setup never echoes the token and clears the clipboard.
4. If no secret store exists, stop and say so; do not fall back to a file.
5. Update the README portability table.

## Data handling
The token's storage location changes per OS, so the README table, CHANGELOG 'Data handling' and PRIVACY.md must say where it lives on each.

## Risks and open questions
- Headless Linux often has no secret store. The clear failure message is the fallback.
- Not testable by one person on one OS; needs a tester per platform.

## Dependencies
None.

## Done when
Token setup and a probe run work on macOS and Linux, the token is never written to a plain file, and the docs name each location.
