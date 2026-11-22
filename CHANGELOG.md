# Changelog

Versions follow `plugin.json`. Installed copies update only when the version is bumped.

Any change to what the plugin reads, writes or sends is listed under **Data handling** in its release, and [PRIVACY.md](PRIVACY.md) is updated in the same release.

## 0.2.0

- Added: capture from the owner's words only ([#10](https://github.com/ChiefStarKid/kainosis/issues/10)). `km` and `km-audit` take cases and rules only from the owner's own turns; tool-result text needs the owner's approval, shown with its source (`docs/schema.md` A7). Idea from [Link](https://github.com/gowtham0992/link) by gowtham0992.
- Added: load receipt in `km-audit` triage ([#8](https://github.com/ChiefStarKid/kainosis/issues/8)): per session, `whole`, `truncated`, `absent` or `unknown`; only `whole` sessions count as retirement evidence. `scripts/km_load_receipt.py`, with a test. Idea from [Link](https://github.com/gowtham0992/link) by gowtham0992.
- Added: `supersedes:` frontmatter field written by `km` when a close-out replaces a node; `km-audit` skips the contradiction pairs it resolves but still lists them; `km_graph_check.py` reports a missing target as a dead link ([#12](https://github.com/ChiefStarKid/kainosis/issues/12)). Idea from [Link](https://github.com/gowtham0992/link) by gowtham0992.
- Added: `hooks/`, an **example** rules-reminder hook (`rules_reminder.py`, Python standard library only) with a sample config and an enable guide ([#5](https://github.com/ChiefStarKid/kainosis/issues/5)).

**Data handling:**
- Capture is narrower: nothing from tool results is written to memory without your approval and a visible source. No new data is stored.
- The load receipt reads the same session transcripts `km-audit` already scans (the loaded-instructions entries and first messages) and `MEMORY.md`. With the optional `--history` flag it also runs read-only `git log` and `git show` in your memory repo to read the earlier `MEMORY.md`. It writes nothing and contacts nothing.
- `supersedes:` adds one optional frontmatter field in memory files. No new data read or sent.
- The plugin still registers no hook: there is no `hooks.json`, and `plugin.json` does not reference `hooks/`, so nothing runs unless you copy the settings snippet into your own `settings.json`. If you do, the hook reads only the hook input Claude Code sends it and its own config file, writes only a reminder to stdout, and uses no network.
- [PRIVACY.md](PRIVACY.md) and the README "What it reads, writes and sends" section are updated to match.

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
