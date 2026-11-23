#!/usr/bin/env python3
"""EXAMPLE PreCompact hook for Claude Code. Not active unless you install it.

`km lean` writes its Keep list to <temp dir>/claude/km-keep.txt (only when you have said
you run this hook). When a compaction starts, this hook prints that file to stdout, which
Claude Code uses as instructions for the compaction summary, then deletes it so an old
list never feeds a later compaction. Python 3, stdlib only. No network.

It does nothing (and keeps the file) when you typed your own instructions after /compact.
It does nothing, and removes the file, when the file is older than MAX_AGE_S.
Each run appends one line (time, session id, trigger, what it did) to km-keep-hook.log next to
the keep file, so you can see whether it fired. Delete that log any time.
Override the file with the KM_KEEP_FILE environment variable (used by tests).
"""
import json
import os
import sys
import tempfile
import time

MAX_AGE_S = 30 * 60
MAX_CHARS = 9000  # Claude Code cuts PreCompact stdout at 10,000 characters


def keep_path():
    return os.environ.get("KM_KEEP_FILE") or os.path.join(
        tempfile.gettempdir(), "claude", "km-keep.txt")


def main():
    try:
        event = json.load(sys.stdin)
    except Exception:
        event = {}
    path = keep_path()

    def log(action):
        try:
            with open(os.path.join(os.path.dirname(path), "km-keep-hook.log"), "a", encoding="utf-8") as lf:
                lf.write("%s session=%s trigger=%s action=%s\n" % (
                    time.strftime("%H:%M:%S"), event.get("session_id"), event.get("trigger"), action))
        except OSError:
            pass

    if event.get("custom_instructions"):
        log("skip-own-instructions")
        return 0
    try:
        stale = time.time() - os.path.getmtime(path) > MAX_AGE_S
        text = "" if stale else open(path, encoding="utf-8").read().strip()
        os.remove(path)
    except OSError:
        log("no-file")
        return 0
    log("stale-removed" if stale else "emitted %d chars" % len(text))
    if text:
        sys.stdout.write(text[:MAX_CHARS] + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
