# Changelog

Versions follow `plugin.json`. Installed copies update only when the version is bumped.

Any change to what the plugin reads, writes or sends is listed under **Data handling** in its release, and [PRIVACY.md](PRIVACY.md) is updated in the same release.

## 0.2.2

- Changed: the example PreCompact hook (`hooks/precompact_keep.py`) now logs each run, so you can see whether it fired ([#6](https://github.com/ChiefStarKid/kainosis/issues/6)). `hooks/README.md` documents the log and a tip: queue `/compact` while `km lean` is still running and it fires after the Q&A.
- Known limit: the Keep file is shared. Any session compacting in the same profile can consume it, so a second session's compaction can take it before yours does. One queued test run failed this way, and the cause is likely, not proven.
- Tested: typed `/compact` passed twice and `/compact` queued after `km lean` passed once, on Windows with a user-level copy of the hook. Not yet tested: this repo copy through a real `/compact`, `km lean` writing the file end to end, automatic compaction, macOS and Linux.

**Data handling:**
- The example hook, if you install it, appends one line per run (time, session id, trigger and what it did, never the Keep text) to `<temp dir>/claude/km-keep-hook.log` on your machine. The log is never rotated or sent anywhere; delete it any time.
- Nothing else changes. The plugin still registers no hook, and `km lean` still writes the Keep file only when you say you run the hook. [PRIVACY.md](PRIVACY.md) is updated to match.

## 0.2.1

- Added: an opt-in example `PreCompact` hook for `km lean` ([#6](https://github.com/ChiefStarKid/kainosis/issues/6)): `hooks/precompact_keep.py`, with an enable guide in `hooks/README.md`. When you have said in the session that you run it, `km lean` writes its Keep list to a file and a bare `/compact` then carries the list as compaction instructions. Claude Code cannot start a compaction from a skill or hook (tracked upstream: anthropics/claude-code#19877), so `km lean` still ends with the paste-ready `/compact Keep:` line.
- Tested: one real `/compact` on Windows, using a user-level copy of the hook with the same logic. Not yet tested: this repo copy through a real `/compact`, `km lean` writing the file end to end, automatic compaction, macOS and Linux.

**Data handling:**
- `km lean` can now write one file, `<temp dir>/claude/km-keep.txt` (`%TEMP%` on Windows, `$TMPDIR` or `/tmp` elsewhere). It holds the `Keep: ...` text `km lean` already shows in the chat, and it is written only when you have said in that conversation that you run the example hook.
- The example hook is not registered: there is no `hooks.json` and `plugin.json` does not reference `hooks/`. If you install it yourself it reads that file on `PreCompact`, prints it as compaction instructions and deletes it. A file older than 30 minutes is removed unused. No network.
- [PRIVACY.md](PRIVACY.md) is updated to match.

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
