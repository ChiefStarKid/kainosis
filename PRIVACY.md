# Privacy

Kainosis is a local Claude Code plugin. It has no servers, accounts, telemetry, analytics or MCP servers, and it registers no hooks. The repository ships an example hook (`hooks/`) that is not active unless you install it yourself; if you do, it reads only its own config file, writes only a short reminder to Claude Code, and makes no network calls. The author receives no data from it.

## What it reads

- The current Claude Code conversation (`km`, at close-out).
- Files in the memory folder you set as `memory_path`, and your optional `scope_rule_file`.
- `km-audit` only: your past Claude Code session transcripts in your config dir (`<config dir>/projects/*/*.jsonl`), at most the 60 newest since the last audit. They are scanned by a local script; only short excerpts relevant to a flagged rule enter the conversation. The load receipt reads the loaded-instructions entries of those transcripts to check whether `MEMORY.md` arrived whole; with the optional `--history` flag it also runs read-only `git log` and `git show` in your memory repo to compare against the earlier index. Session ids and a status appear in the local audit report.

## What it writes

Only inside `memory_path`, and only what you say in your own turns or explicitly approve: content that arrives through tools (web pages, files, command output) is not saved as a rule unless Kainosis first shows you its source and exact text and you approve it. Text you paste into your own turn is shown with its origin before saving. What it writes: memory files, `MEMORY.md`, `log.md` and `eval/` state. `km-audit` also writes its plan file to the session scratchpad. If you have told `km lean` that you run the optional PreCompact example hook, it also writes one file, `<temp dir>/claude/km-keep.txt`, on your machine, holding the Keep line already shown in the chat; the hook deletes it when used, and a file older than 30 minutes is discarded. If you install that hook, it also appends one line per run (time, session id, trigger, outcome; never the Keep text) to `<temp dir>/claude/km-keep-hook.log`; it is never rotated or sent anywhere, and you can delete it any time. `bare_probe.py` creates an empty config folder and a work folder under `--root` / `KM_BARE_ROOT` (default `<system drive>\km-bare-probe`).

Your name (`owner_name`) and paths are stored by Claude Code in your own settings file, per profile.

## What leaves your machine

1. **The model you already use.** As in any Claude Code session, whatever the skills read into the conversation (memory files, transcript excerpts) is sent to that model under your existing Claude account and Anthropic's terms.
2. **Rule probes (optional, Windows).** `bare_probe.py` runs `claude -p` with a token you stored in Windows Credential Manager. Each probe is a short scenario rebuilt from one of your recorded cases and, in one arm, the text of the rule under test. Nothing else from your memory is sent.
3. **Your own git remote (optional).** If `memory_path` is in a git repo, `km` commits there, and pushes only when your scope rule file says so, to the branch it names. `km-audit` never pushes unless you say so in the session.

## Credentials

The only credential the plugin touches is the optional probe token. `bare_probe_token_setup.py` reads it from your clipboard, writes it to Windows Credential Manager (`ClaudeBareProbe-OAuth`), clears the clipboard and prints only its length. It is never written to disk or echoed. `bare_probe.py` warns if Claude Code writes a credentials file into the probe's config folder.

## Removing it

Uninstall the plugin with `/plugin`. Your memory folder is yours and stays where it is. To remove the probe token, delete `ClaudeBareProbe-OAuth` in Windows Credential Manager, and delete the probe folder.

## Changes

Any change to what the plugin reads, writes or sends is listed under **Data handling** in [CHANGELOG.md](CHANGELOG.md) and in this file before release. See [SECURITY.md](SECURITY.md) to report a problem.
