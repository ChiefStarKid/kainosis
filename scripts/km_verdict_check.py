"""The km close-out verdict (docs/closeout-verdict.md), run at Step 9 of the skill.
Stdlib only. Read-only: it never writes, and runs git only for `cat-file`, `rev-parse`
and `status`.

Usage:  python km_verdict_check.py LEDGER.json [--mem DIR]

Prints the verdict line, then (if any) a `Model-verified:` list of the claims this script
cannot check. Exit 0 always for a readable ledger; 2 for an unreadable one.

Ledger (JSON, kept outside the memory folder):
  mode               "lean" | "full" | "verdict-only" (default "full")
  full_loaded_marker full and verdict-only: the `Full-load marker` line of docs/km-full.md,
                     quoted. A missing or wrong marker gives NOT SAFE (the run skipped it).
  candidates         [{"id", "disposition": written|merged|rejected|deferred,
                       "verified": bool, "evidence": str, "where": str (free text),
                       "file": path relative to --mem (written/merged rows)}]
  commit             hash of the Step 8 commit, or null
  written_paths      paths relative to --mem this run wrote or changed
  reverse_sweep      {"ran": bool, "unreconciled": [..]}      (full)
  loose_ends         [{"item", "status": clear|tracked|open, "where", "accepted"}]  (full)
  carry_over         [{"item", "where", "accepted"}]                              (full)

With --mem the script itself checks: a candidate's `file` exists inside --mem; `commit`
is a commit in --mem; each written path is committed with no pending change. Without
--mem those checks are listed as model-verified. Claims it cannot check at all (a draft
sent, a process gone, a deferred home outside --mem) stay with the model."""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

MARKER_RE = re.compile(r"Full-load marker: `([^`]+)`")
HASH_RE = re.compile(r"^[0-9a-fA-F]{7,64}$")


def full_marker():
    doc = Path(__file__).resolve().parent.parent / "docs" / "km-full.md"
    m = MARKER_RE.search(doc.read_text(encoding="utf-8"))
    return m.group(1) if m else None


def git(mem, *args):
    p = subprocess.run(["git", "-C", str(mem), *args], capture_output=True, text=True)
    return p.returncode, p.stdout


def inside(mem, rel):
    try:
        p = (Path(mem) / rel).resolve()
        p.relative_to(Path(mem).resolve())
        return p
    except (ValueError, OSError):
        return None


def file_checks(ledger, mem, out, unchecked):
    for c in ledger.get("candidates", []):
        if c.get("disposition") in ("written", "merged"):
            rel, cid = c.get("file"), c.get("id")
            if not rel:
                unchecked.append(f"candidate {cid}: {c.get('disposition')} with no `file`; content read by the model")
            else:
                p = inside(mem, rel)
                if p is None or not p.is_file():
                    out.append(f"candidate {cid}: file {rel} is not in the memory folder")
        elif c.get("disposition") == "deferred" and c.get("where"):
            unchecked.append(f"candidate {c.get('id')}: deferred home '{c.get('where')}' read by the model")
    commit, paths = ledger.get("commit"), ledger.get("written_paths") or []
    in_git = git(mem, "rev-parse", "--is-inside-work-tree")[0] == 0
    if commit:
        if not (isinstance(commit, str) and HASH_RE.match(commit)) or git(mem, "cat-file", "-e", commit + "^{commit}")[0] != 0:
            out.append(f"commit {commit} does not exist in the memory repo")
            return
    if not in_git:
        unchecked.append("memory folder is not a git repo; commit state not checked")
        return
    if paths and not commit:
        out.append("paths were written but there is no commit")
    for rel in paths:
        if inside(mem, rel) is None:
            out.append(f"written path {rel} is outside the memory folder")
        elif git(mem, "ls-files", "--error-unmatch", "--", rel)[0] != 0 and (Path(mem) / rel).exists():
            out.append(f"written path {rel} is not committed")
        elif git(mem, "status", "--porcelain", "--", rel)[1].strip():
            out.append(f"written path {rel} has uncommitted changes")


def blockers(ledger, mem=None, unchecked=None):
    unchecked = unchecked if unchecked is not None else []
    mode = ledger.get("mode", "full")
    lean = mode == "lean"
    out = []
    if not lean:
        want, got = full_marker(), ledger.get("full_loaded_marker")
        if not want:
            out.append("docs/km-full.md has no full-load marker")
        elif got != want:
            out.append("full run: the ledger does not quote docs/km-full.md's marker (km-full.md not read)"
                       if not got else "full run: wrong km-full.md marker")
    for c in ledger.get("candidates", []):
        d, cid = c.get("disposition"), c.get("id")
        if d not in ("written", "merged", "rejected", "deferred"):
            out.append(f"candidate {cid}: no valid disposition")
        elif d in ("written", "merged") and not (c.get("verified") and c.get("evidence")):
            out.append(f"candidate {cid}: claims '{d}' but it is unverified")
        elif d == "deferred" and not (c.get("where") or c.get("accepted")):
            out.append(f"candidate {cid}: deferred with no home")
    if mem is not None:
        file_checks(ledger, mem, out, unchecked)
    else:
        unchecked.append("file, commit and written-path claims (no --mem)")
    if not lean:
        rs = ledger.get("reverse_sweep") or {}
        if not rs.get("ran"):
            out.append("reverse sweep did not run")
        elif rs.get("unreconciled"):
            out.append(f"reverse sweep: {len(rs['unreconciled'])} find(s) not in the ledger")
        for le in ledger.get("loose_ends", []):
            if le.get("status") == "open" and not le.get("accepted"):
                out.append(f"loose end open: {le.get('item')}")
            elif le.get("status") == "tracked" and not le.get("where"):
                out.append(f"loose end tracked with no location: {le.get('item')}")
            elif le.get("status") == "clear":
                unchecked.append(f"loose end clear: {le.get('item')}")
        for co in ledger.get("carry_over", []):
            if not (co.get("where") or co.get("accepted")):
                out.append(f"carry-over unanchored: {co.get('item')}")
    return out


def verdict(ledger, mem=None, unchecked=None):
    b = blockers(ledger, mem, unchecked)
    if ledger.get("mode", "full") == "lean":
        if b:
            return "NOT SAFE TO COMPACT - " + "; ".join(b)
        return "SAFE TO COMPACT (lean: no reverse sweep, no loose-ends sweep; not an archive/delete verdict)"
    return "NOT SAFE - " + "; ".join(b) if b else "SAFE"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("ledger")
    ap.add_argument("--mem")
    a = ap.parse_args(argv)
    try:
        with open(a.ledger, encoding="utf-8") as f:
            ledger = json.load(f)
        if not isinstance(ledger, dict):
            raise ValueError("ledger must be a JSON object")
    except (OSError, ValueError) as e:
        print(f"cannot read ledger: {e}", file=sys.stderr)
        return 2
    unchecked = []
    print(verdict(ledger, a.mem, unchecked))
    if unchecked:
        print("Model-verified (this script cannot check; the ledger must name the evidence):")
        for u in unchecked:
            print(f"- {u}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
