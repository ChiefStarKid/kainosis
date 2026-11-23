# Example hook: rules reminder

**This is an example. Kainosis does not register it and it is not active unless you install it yourself.** There is no `hooks.json` here and nothing in `.claude-plugin/plugin.json` points at this folder, so installing the plugin loads no hook.

`rules_reminder.py` is a `PreToolUse` hook. Before a tool call it reads one plain-text config of short reminder lines and, for each line whose optional regex matches the tool input, adds the line to the agent's context as a one-line reminder. It never blocks or approves a call.

## Files

- `rules_reminder.py`: the hook (Python 3, stdlib only; Windows, macOS, Linux).
- `rules-reminder.example.txt`: sample rules (a fictional hobby greenhouse). Copy it to `rules-reminder.txt` next to the script and edit.

## Enable it

1. Copy `hooks/` somewhere stable (for example `~/.claude/kainosis-hooks/`) and copy `rules-reminder.example.txt` to `rules-reminder.txt` there.
2. Paste this into your own `~/.claude/settings.json` (or a project's `.claude/settings.json`), with your path:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash|Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python",
            "args": ["/path/to/kainosis-hooks/rules_reminder.py"]
          }
        ]
      }
    ]
  }
}
```

Use `python3` if that is your interpreter name. To turn it off, delete the entry.

Config lines are `regex => reminder` (shown only when the regex matches the tool input, such as the Bash command or the file path) or a bare `reminder` (shown on every matching tool call). `#` starts a comment. At most 5 reminders are shown per call.

## How a rule graduates into it

A rule that keeps failing as soft text in memory (the `km-audit` flow: "Soft rule keeps failing in context → graduate to script or hook; delete rule text") moves here:

1. Add one short line for it to `rules-reminder.txt`, with a regex for the situation where it matters (the rule's `Trigger`/`check`).
2. Delete the rule's text from memory. The hook now carries it; keeping both is a "just in case" duplicate that `km-audit` flags.
3. Rules that are `basis: fact` or `preference` can graduate too, but `km-audit` only proposes it for rules that keep failing, and graduation needs your yes.

## What it reads and writes

- **Reads:** the hook input Claude Code sends on stdin, and its own config file. Nothing else.
- **Writes:** one JSON object to stdout. No files.
- **Network:** none.

---

# Example hook: PreCompact Keep list

**Also an example, not registered, not active unless you install it.** It exists because Claude Code cannot start a compaction from a skill or hook, so `km lean` still ends with a paste-ready `/compact Keep: ...` line. This hook lets a bare `/compact` carry the same list.

`precompact_keep.py` is a `PreCompact` hook (Python 3, stdlib only). When a compaction starts it prints `<temp dir>/claude/km-keep.txt` to stdout, which Claude Code uses as instructions for the compaction summary, then deletes the file. It does nothing if the file is missing, empty or older than 30 minutes (it removes a stale one), and it leaves the file alone when you typed your own text after `/compact`.

## Enable it

1. Copy `precompact_keep.py` somewhere stable.
2. Paste this into your own `~/.claude/settings.json`, with your path (use `python3` if that is your interpreter name):

```json
{
  "hooks": {
    "PreCompact": [
      {
        "matcher": "",
        "hooks": [
          { "type": "command", "command": "python", "args": ["/path/to/precompact_keep.py"], "timeout": 10 }
        ]
      }
    ]
  }
}
```

3. Tell `km lean`, in that conversation, that you run the hook. It cannot detect it, and without your statement it writes no file. It then also writes the Keep text to the temp file and still prints the paste-ready last line.

**Tip: queue the compact.** After you send `/kainosis:km lean`, you can type `/compact` straight away while it is still running. It queues and runs once `km lean` has finished and its questions are answered (tested 2026-11-23: the questions came first, and the Keep list carried through). One bare `/compact` then does the whole hand-off.

The empty matcher also fires on auto-compaction. That is why the file is one-shot and expires: if you run `km lean` and do not compact, an auto-compaction within 30 minutes would use that list.

## What it reads and writes

- **Reads:** the hook input on stdin, and `<temp dir>/claude/km-keep.txt` (`KM_KEEP_FILE` overrides the path).
- **Writes:** the file's text to stdout (at most 9,000 characters). It deletes the keep file and appends one line per run (time, session id, `manual` or `auto`, what it did; never the Keep text) to `km-keep-hook.log` in the same folder. Delete that log any time. Nothing else.
- **Network:** none.
- `km lean` itself writes that one temp file, only on your say-so.
