# Changelog

Versions follow `plugin.json`. Installed copies update only when the version is bumped.

Any change to what the plugin reads, writes or sends is listed under **Data handling** in its release, and [PRIVACY.md](PRIVACY.md) is updated in the same release.

## Unreleased

- Added: `hooks/`, an **example** rules-reminder hook (`rules_reminder.py`, Python standard library only) with a sample config and an enable guide ([#5](https://github.com/ChiefStarKid/kainosis/issues/5)). It is on `main` but not yet in a tagged release; installed copies get it when the version is bumped.

**Data handling:** the plugin still registers no hook: there is no `hooks.json`, and `plugin.json` does not reference the folder, so nothing runs unless you copy the settings snippet into your own `settings.json`. If you do, the hook reads only the hook input Claude Code sends it and its own config file, writes only a reminder to stdout, and uses no network. [PRIVACY.md](PRIVACY.md) and the README "What it reads, writes and sends" section are updated to match.

## 0.1.1

Fix release.

- Fixed: the YAML frontmatter of both skills did not parse, because the `description:` lines contained an unquoted `: `. Claude Code loaded `km` and `km-audit` with empty metadata, so their descriptions and the `lean` argument hint were dropped. The descriptions are now quoted, and `claude plugin validate .` passes.
- Added: a placeholder plugin icon (`.claude-plugin/icon.png`).

**Data handling:** no change.

## 0.1.0

First public release.

- `/kainosis:km` and `/kainosis:km lean`: session close-out to a hub-and-spoke memory graph; corrections recorded as eval cases.
- `/kainosis:km-audit`: re-tests rules on the current model, retires the ones it no longer needs, compacts the index within a byte budget.
- `scripts/km_graph_check.py`: graph health (islands, unreachable files, dead links, path bytes).
- `scripts/bare_probe.py` and `bare_probe_token_setup.py`: bare-context rule probes (Windows only).
- `examples/graph/`: fictional sample graph.

**Data handling:** as described in [PRIVACY.md](PRIVACY.md).
