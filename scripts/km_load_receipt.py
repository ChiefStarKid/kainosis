"""Load receipt: did the always-loaded MEMORY.md arrive whole in each session?

Used by km-audit triage (docs/evals.md §Load receipt). Reads only the
opening entries of the *.jsonl transcripts triage already scans, plus
MEMORY.md. Never writes. Stdlib only.

Whole = the index's final line AND every index link target appear in the
session's opening context. Otherwise `truncated` (index text started but cut)
or `absent` (no index text found). Only `whole` sessions count as retirement
evidence.

Usage: python km_load_receipt.py --mem <dir> <transcript.jsonl>... [--json]
"""
import argparse
import json
import re
import sys
from pathlib import Path

OPENING = 6  # opening entries searched; the load arrives before the first real turn
LINK = re.compile(r"\]\(([^)\s]+\.md)\)")


def expected(mem):
    lines = [l.rstrip() for l in (Path(mem) / "MEMORY.md").read_text(encoding="utf-8").splitlines()]
    lines = [l for l in lines if l.strip()]
    targets = sorted({m for l in lines for m in LINK.findall(l)})
    return lines[-1].strip(), targets


def opening_text(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for i, raw in enumerate(f):
            if i >= OPENING:
                break
            try:
                msg = json.loads(raw).get("message", {})
            except ValueError:
                continue
            c = msg.get("content", "")
            if isinstance(c, list):
                c = " ".join(b.get("text", "") for b in c if isinstance(b, dict))
            out.append(str(c))
    return "\n".join(out)


def receipt(path, last, targets):
    text = opening_text(path)
    found = [t for t in targets if t in text]
    if not found and last not in text:
        status = "absent"
    elif last in text and len(found) == len(targets):
        status = "whole"
    else:
        status = "truncated"
    return {"session": Path(path).stem, "status": status,
            "hubs": f"{len(found)}/{len(targets)}", "last_line": last in text}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mem", required=True)
    ap.add_argument("transcripts", nargs="+")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    last, targets = expected(a.mem)
    rs = [receipt(p, last, targets) for p in a.transcripts]
    if a.json:
        print(json.dumps(rs, indent=1))
    else:
        for r in rs:
            print(f"{r['status']:9} hubs {r['hubs']:6} last-line {'yes' if r['last_line'] else 'NO '} {r['session']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
