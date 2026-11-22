# Privacy

Kainosis is a local Claude Code plugin. It has no servers, accounts, telemetry, analytics, hooks or MCP servers. The author receives no data from it.

## What it reads

- The current Claude Code conversation (`km`, at close-out).
- Files in the memory folder you set as `memory_path`, and your optional `scope_rule_file`.
- `km-audit` only: your past Claude Code session transcripts in your config dir (`<config dir>/projects/*/*.jsonl`), at most the 60 newest since the last audit. They are scanned by a local script; only short excerpts relevant to a flagged rule enter the conversation.

## What it writes

Only inside `memory_path`: memory files, `MEMORY.md`, `log.md` and `eval/` state. `km-audit` also writes its plan file to the session scratchpad. `bare_probe.py` creates an empty config folder and a work folder under `--root` / `KM_BARE_ROOT` (default `<system drive>\km-bare-probe`).

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
