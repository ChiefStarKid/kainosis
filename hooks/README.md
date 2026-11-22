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
