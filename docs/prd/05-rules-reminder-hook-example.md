# PRD: Rules-reminder hook as an example hooks/ folder

Issue: https://github.com/ChiefStarKid/kainosis/issues/5 · Stage: v0.2 · Labels: roadmap, hooks, data-handling

## Problem
Graduating a rule into a hook is part of the method, but v0.1 only describes it, so nobody can copy a working example.

## Goal
An example `hooks/` folder holding the rules-reminder hook, off by default, with a short guide to enabling it.

## Non-goals
- Enabling any hook by default.
- Registering the hook in `plugin.json` so it loads on install.

## Requirements
1. Provide the hook script and an example settings snippet the user copies in themselves.
2. Document how a rule graduates: the rule text leaves memory, the hook carries it.
3. Hook output is a short reminder only; it reads no files beyond its own config.
4. Update the README 'no hooks' line so it says the repo ships an example, not an active hook.

## Data handling
The plugin still registers no hook. The example runs only if the owner installs it. CHANGELOG 'Data handling' and PRIVACY.md state exactly that.

## Risks and open questions
- Readers may think the hook is active. Name it 'example' everywhere.

## Dependencies
Release together with #10 so one Data handling entry covers both.

## Done when
`hooks/` exists with the example and enable guide, nothing is enabled by default, and the README, CHANGELOG and PRIVACY.md are updated.
