# Issue #5 draft: Data handling wording (not yet applied)

For the roadmap owner to merge into CHANGELOG.md, PRIVACY.md and README.md in the v0.2 release, together with #10.

## CHANGELOG "Data handling" entry

- Adds `hooks/`, an **example** rules-reminder hook (`rules_reminder.py`, Python stdlib only) with a sample config and an enable guide. The plugin still registers no hook: there is no `hooks.json` and `plugin.json` does not reference the folder, so nothing runs unless you copy the settings snippet into your own `settings.json`. If you do, the hook reads only the hook input Claude Code sends it and its own config file, writes only a reminder to stdout, and uses no network.

## PRIVACY.md

Replace "…telemetry, analytics, hooks or MCP servers." with:

> It has no servers, accounts, telemetry, analytics or MCP servers, and it registers no hooks. The repository ships an example hook (`hooks/`) that is not active unless you install it yourself; if you do, it reads only its own config file, writes only a short reminder to Claude Code, and makes no network calls. The author receives no data from it.

## README

"What it reads, writes and sends" paragraph, replace "no hooks" with:

> No telemetry, no other services, no MCP servers, and the plugin registers no hooks. The repo ships an example rules-reminder hook in `hooks/` that is not active unless you install it (reads only its own config, no network).

Roadmap: move #5 from "Next (v0.2)" to shipped once released.
