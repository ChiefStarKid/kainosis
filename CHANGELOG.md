# Changelog

Versions follow `plugin.json`. Installed copies update only when the version is bumped.

Any change to what the plugin reads, writes or sends is listed under **Data handling** in its release, and [PRIVACY.md](PRIVACY.md) is updated in the same release.

## Unreleased

- Changed: `skills/km/SKILL.md` is smaller, 18,261 to about 14,600 bytes committed ([#30](https://github.com/ChiefStarKid/kainosis/issues/30)). Steps only a full run performs moved to `docs/km-full.md` (read at Step 1 of a full run, never by `km lean`); the structure rules that apply only when creating wiki or per-tool files are in `docs/structure-rules.md`.
- Added: `scripts/km_close.py`, which writes the mechanical Step 8 appends (cases, retrieval queries, backlog rows, log line) so the model no longer does it by hand. It validates everything first, writes through temp files, keeps each file's line endings, final newline and BOM, refuses non-UTF-8 files, never adds a separator to `log.md`, and prints the paths it wrote.
- Fixed: the close-out commit now stages only the files the run wrote, never `git add .`, so another session's unfinished work in a shared memory repo is not committed. The close-out input file is kept in the temp folder, outside the memory folder.
- Fixed: three doc pointers in the skill lost their `${CLAUDE_PLUGIN_ROOT}/` prefix and are restored. A lean run with no candidates skips the two question rounds. OWNER's instruction in the conversation overrides the scope rule's push setting. The lean verdict again states that the sweeps were not run.

- Fixed: the case `check` instructions now match `km_close.py` (`null`, or an object with one of four types); a prose check is rejected and a test covers it ([#37](https://github.com/ChiefStarKid/kainosis/issues/37)).
- Changed: Step 9 runs `scripts/km_verdict_check.py` on a JSON ledger. It checks that a row's file exists, the recorded commit exists and written paths are committed, and a full-run ledger must quote the marker in `docs/km-full.md`. A lean run no longer opens `docs/closeout-verdict.md`.

**Data handling:** no new data is read or written: `km_close.py` writes the same memory-folder files `km` already wrote, plus a short-lived `*.km_tmp` file beside each. No network access. [PRIVACY.md](PRIVACY.md) needs no change.

## 0.3.0

- Added: close-out verdict in `km` ([#19](https://github.com/ChiefStarKid/kainosis/issues/19)). Close-out now ends with a ledger of what was captured and what was left open, a loose-ends sweep, a carry-over list, a reverse sweep (is anything in the thread not yet in memory?) and a verdict, SAFE or NOT SAFE, for ending or archiving the thread. `km lean` never gives a plain SAFE. A carry-over item with no home blocks SAFE unless you accept it. `scripts/km_verdict_check.py`, with a test.
- Added: `km-audit` can propose restructuring an oversized index into theme hubs ([#20](https://github.com/ChiefStarKid/kainosis/issues/20)). `scripts/km_index_restructure.py` groups the feedback lines into a few hub files, keeps every one-line description verbatim, and replays reachability before and after. A query that passed before and fails after, an altered description or a lost slug blocks the change. `--themes` takes your own grouping. Nothing is written to your memory folder until you say yes.
- Added: `km-audit` flags stale command names and non-existent paths in your CLAUDE.md files after a rename (report only), and a `truncated` load receipt now outranks the byte target as the first finding.
- Added: second-cluster results page ([#1](https://github.com/ChiefStarKid/kainosis/issues/1)), `docs/second-cluster.md`: 17 rules, 6 probed, 100 runs plus 2 canaries, 0 retired. One person's memory, a second data point, not proof.
- Known limit: the restructure's retrieval replay checks reachability and stored queries; the model-judged retrieval replay in `docs/evals.md` still runs on the same queries.

**Data handling:**
- Close-out verdict: no new data is read or written. The ledger, sweeps and verdict are shown in the chat only. The checks use read-only local calls (file exists, `git log`, process list) already within what `km` does.
- Index restructure: `propose` and `replay` are read-only on your memory folder (the candidate goes to a scratch folder). `apply` refuses without your approval, re-runs replay first, then writes only `MEMORY.md` and new `index_feedback_<theme>.md` hub files in the memory folder. It is a normal commit, reverted with `git revert`.
- Stale-name check: `km-audit` already opens your CLAUDE.md files to count always-loaded bytes. It now also searches their text for renamed command names and tests whether the paths they name exist on disk. Existence check only; no other file is opened and CLAUDE.md is never edited without your yes.
- No network access; nothing new leaves your machine. [PRIVACY.md](PRIVACY.md) is updated to match.

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
