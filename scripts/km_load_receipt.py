"""Load receipt: did the always-loaded MEMORY.md arrive whole in each session?

Used by km-audit triage (docs/evals.md §Load receipt). Reads only the
opening messages and the `instructions` attachments of the *.jsonl transcripts
triage already scans, plus MEMORY.md. Never writes. Stdlib only.

Whole = the index's final line AND every index link target appear in the
session's loaded context. Otherwise `truncated` (index text started but cut)
or `absent` (no index text found). Only `whole` sessions count as retirement
evidence. `stale_index` flags a non-whole receipt whose MEMORY.md was
modified after the session started (the mismatch may be an edit, not a cut).

Usage: python km_load_receipt.py --mem <dir> <transcript.jsonl>... [--json]
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

OPENING = 6  # opening message entries searched; the load arrives before the first real turn
LINK = re.compile(r"\]\(([^)\s]+\.md)\)")


def expected(mem):
    lines = [l.rstrip() for l in (Path(mem) / "MEMORY.md").read_text(encoding="utf-8").splitlines()]
    lines = [l for l in lines if l.strip()]
    targets = sorted({m for l in lines for m in LINK.findall(l)})
    return lines[-1].strip(), targets


def parse_ts(ts):
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except ValueError:
        return None


def opening_text(path):
    out, start = [], None
    with open(path, encoding="utf-8") as f:
        for i, raw in enumerate(f):
            try:
                d = json.loads(raw)
            except ValueError:
                continue
            if start is None:
                start = parse_ts(d.get("timestamp"))
            msg = d.get("message") or {}
            c = msg.get("content", "") if isinstance(msg, dict) else ""
            if isinstance(c, list):
                c = " ".join(b.get("text", "") for b in c if isinstance(b, dict))
            if i < OPENING:
                out.append(str(c))
            # real transcripts carry the memory load in an `instructions` attachment
            for af in (d.get("attachment") or {}).get("files", []):
                out.append(str(af.get("content", "")))
    return "\n".join(out), start


def receipt(path, last, targets, index_mtime):
    text, start = opening_text(path)
    found = [t for t in targets if t in text]
    if not found and last not in text:
        status = "absent"
    elif last in text and len(found) == len(targets):
        status = "whole"
    else:
        status = "truncated"
    # index edited after the session began: a non-whole status may only mean MEMORY.md changed since
    stale = status != "whole" and start is not None and index_mtime > start
    return {"session": Path(path).stem, "status": status,
            "hubs": f"{len(found)}/{len(targets)}", "last_line": last in text,
            "session_start": start.isoformat() if start else None,
            "index_modified": index_mtime.isoformat(), "stale_index": stale}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mem", required=True)
    ap.add_argument("transcripts", nargs="+")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    last, targets = expected(a.mem)
    mtime = datetime.fromtimestamp((Path(a.mem) / "MEMORY.md").stat().st_mtime, timezone.utc)
    rs = [receipt(p, last, targets, mtime) for p in a.transcripts]
    if a.json:
        print(json.dumps(rs, indent=1))
    else:
        for r in rs:
            print(f"{r['status']:9} hubs {r['hubs']:6} last-line {'yes' if r['last_line'] else 'NO '} {r['session']}"
                  + ("  (index edited since session start)" if r["stale_index"] else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
