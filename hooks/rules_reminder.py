#!/usr/bin/env python3
"""EXAMPLE rules-reminder hook for Claude Code (PreToolUse). Not active unless you install it.

Reads the hook input JSON from stdin, reads ONE plain-text config file (its own),
and prints a short reminder for every rule whose `check` regex matches the tool input.
No network, no other files, writes nothing. Python 3, stdlib only.

Config file (default: rules-reminder.txt next to this script; override with the
first argument or the KM_REMINDER_CONFIG environment variable). One rule per line:

    # comment
    reminder text                      -> shown on every tool call the hook is registered for
    regex => reminder text             -> shown only when the regex matches the tool input

The regex is searched (case-insensitive) in the tool input as JSON text, e.g.
the Bash command or the file_path. Keep reminders to one short line each.
"""
import json
import os
import re
import sys

MAX_RULES_SHOWN = 5


def load_rules(path):
    rules = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                check, sep, text = line.partition("=>")
                if sep:
                    rules.append((check.strip(), text.strip()))
                else:
                    rules.append((None, line))
    except OSError:
        pass  # no config: say nothing, never block the tool call
    return rules


def main():
    config = (sys.argv[1] if len(sys.argv) > 1 else None) or os.environ.get(
        "KM_REMINDER_CONFIG"
    ) or os.path.join(os.path.dirname(os.path.abspath(__file__)), "rules-reminder.txt")
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return 0
    tool_input = json.dumps(data.get("tool_input", {}), ensure_ascii=False)

    hits = []
    for check, text in load_rules(config):
        if not text:
            continue
        try:
            if check is None or re.search(check, tool_input, re.IGNORECASE):
                hits.append(text)
        except re.error:
            continue  # a bad regex skips that rule only
    if not hits:
        return 0

    reminder = "Reminders: " + " | ".join(hits[:MAX_RULES_SHOWN])
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": data.get("hook_event_name", "PreToolUse"),
            "additionalContext": reminder,
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
