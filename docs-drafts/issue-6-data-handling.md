# Issue #6 data-handling draft (for the 0.2.1 release; do not apply here)

## CHANGELOG, "Data handling"
- New: `km lean` can write one file, `<temp dir>/claude/km-keep.txt` (`%TEMP%` on Windows, `$TMPDIR` or `/tmp` elsewhere), containing the `Keep: ...` text it already prints. It does so only when you have said in that conversation that you run the example hook.
- New example: `hooks/precompact_keep.py`. Not registered by the plugin (no `hooks.json`, nothing in `plugin.json`). If you install it yourself it reads that file on `PreCompact`, prints it as compaction instructions, and deletes it. No network.

## PRIVACY.md
- Add the temp file to the "what it writes" list: one file, on your machine, contents = the Keep line already shown in the chat; deleted by the hook on use, expired after 30 minutes.
- Keep the sentence that the plugin registers no hooks; the PreCompact hook is an example you copy into your own settings.

## README wording
- Where hooks are described: "Two example hooks ship in `hooks/` (rules reminder, PreCompact Keep list). Neither is registered."
- Remove or reword the Roadmap's opt-in `PreCompact` item once released; mention upstream anthropics/claude-code#19877 (skills cannot start `/compact`).
