"""Commit a km close-out and print its closing block. Stdlib only, no network. The last
call of Step 8. It never pushes: the push (branch and permission come from the scope file
or the owner) stays in the skill, after this script and before the final message.

Usage:  python km_commit.py --mem DIR --input CLOSE.json [--date YYYY-MM-DD] -- PATH [PATH ...]

PATH: files this run wrote, deleted or changed, relative to --mem (steps 2-3 and the
`file:` lines of km_close.py). Refused, with exit 2 and nothing staged: no path, `.`,
`..`, an absolute path, a glob, a directory, a path outside --mem or inside `.git`.
Git runs only for rev-parse, status, add and commit, always with explicit paths, and the
commit is limited to them (`git commit -- PATH`), so changes other sessions staged in the
same repo are never swept in. CLOSE.json is the km_close.py input (topic, creates,
updates, deletes, lean, retrieval) and must be outside --mem.

Output (stdout), the closing block of the skill:
  KM close-out complete.                 (the skill's Step 9 changes this line on NOT SAFE)
  Written: created a.md; updated b.md; deleted c.md
  Cases: N | Retrieval queries: N | MEMORY.md: N lines
  Committed: <hash> | skipped (nothing to commit) | skipped (not a git repo) | FAILED: <reason>
  Pushed: no                             (the skill edits it if it pushes)
and a last machine line `commit: <hash>` or `commit: null`, which is what the Step 9 ledger
quotes. Cases = case lines the run wrote (the last log.md line), else the input's count.

Exit: 0 committed or skipped, 1 git failed (reported as FAILED above, never silent),
2 bad arguments (nothing staged).
"""
import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

GLOB = re.compile(r"[*?\[\]]")
LOG_CASES = re.compile(r"(\d+) cases(?:, lean)?\s*$")


class Bad(Exception):
    pass


def git(mem, *args):
    p = subprocess.run(["git", "-C", str(mem), *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def clean_paths(mem, raw):
    if not raw:
        raise Bad("no paths: pass the files this run wrote after `--`")
    root = mem.resolve()
    out = []
    for p in raw:
        s = p.strip()
        if s in ("", ".", "..", "-A", "--all") or s.startswith("-"):
            raise Bad(f"refused path {p!r}: name the files this run wrote, never a whole tree")
        if GLOB.search(s) or s.startswith(":"):
            raise Bad(f"refused path {p!r}: no globs or pathspec magic")
        pp = Path(s)
        if pp.is_absolute() or pp.drive:
            raise Bad(f"refused path {p!r}: give paths relative to the memory folder")
        full = (root / pp).resolve()
        try:
            rel = full.relative_to(root)
        except ValueError:
            raise Bad(f"refused path {p!r}: outside the memory folder")
        if ".git" in rel.parts:
            raise Bad(f"refused path {p!r}: inside .git")
        if full.is_dir():
            raise Bad(f"refused path {p!r}: a directory; name its files")
        out.append(rel.as_posix())
    return list(dict.fromkeys(out))


def load_input(path, mem):
    inp = Path(path)
    if inp.resolve().is_relative_to(mem.resolve()):
        raise Bad("the input file must be outside the memory folder")
    try:
        d = json.loads(inp.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as e:
        raise Bad(f"cannot read input: {e}")
    if not isinstance(d, dict) or not isinstance(d.get("topic"), str) or not d["topic"].strip():
        raise Bad("input must be the km_close.py JSON object with a 'topic'")
    for k in ("creates", "updates", "deletes"):
        if isinstance(d.get(k), bool) or not isinstance(d.get(k, 0), int) or d.get(k, 0) < 0:
            raise Bad(f"'{k}' must be a non-negative integer")
    return d


def cases_written(mem, d):
    """Case lines the run wrote = the count on the last log.md line; else the input's list."""
    log = mem / "log.md"
    try:
        lines = [ln for ln in log.read_text(encoding="utf-8-sig").splitlines() if ln.strip()]
        m = LOG_CASES.search(lines[-1]) if lines else None
        if m and d["topic"].strip() in lines[-1]:
            return int(m.group(1))
    except OSError:
        pass
    return len(d.get("cases") or [])


def memory_lines(mem):
    try:
        return len((mem / "MEMORY.md").read_text(encoding="utf-8-sig").splitlines())
    except OSError:
        return 0


def written_line(mem, paths):
    """created / updated / deleted per path, from `git status` (untracked or added = created)."""
    by = {"created": [], "updated": [], "deleted": []}
    for p in paths:
        _, out, _ = git(mem, "status", "--porcelain", "--", p)
        code = out[:2]
        if not out:
            continue
        by["created" if "?" in code or "A" in code else "deleted" if "D" in code else "updated"].append(p)
    parts = [f"{k} {', '.join(v)}" for k, v in by.items() if v]
    return "; ".join(parts) if parts else "nothing changed"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mem", required=True)
    ap.add_argument("--input", required=True)
    ap.add_argument("--date", help="YYYY-MM-DD for the commit subject (default: today)")
    ap.add_argument("paths", nargs="*", help="after `--`")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        mem = Path(a.mem)
        if not mem.is_dir():
            raise Bad(f"memory folder not found: {mem}")
        d = load_input(a.input, mem)
        paths = clean_paths(mem, a.paths)
        day = a.date or date.today().isoformat()
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
            raise Bad("--date must be YYYY-MM-DD")
    except Bad as e:
        print(f"km_commit: {e}", file=sys.stderr)
        print("km_commit: nothing staged", file=sys.stderr)
        return 2

    status, commit, rc_out = None, None, 0
    rc, top, err = git(mem, "rev-parse", "--show-toplevel")
    written = None
    if rc != 0:
        status = "skipped (not a git repo)"
    else:
        written = written_line(mem, paths)
        rc, changed, err = git(mem, "status", "--porcelain", "--", *paths)
        if rc != 0:
            status, rc_out = f"FAILED: git status: {err or 'unknown error'}", 1
        elif not changed:
            status = "skipped (nothing to commit)"
        else:
            rc, _, err = git(mem, "add", "--", *paths)
            if rc != 0:
                status, rc_out = f"FAILED: git add: {err or 'unknown error'}", 1
            else:
                msg = f"chore(km): KM close-out {day} — {d['topic'].strip()}"
                rc, _, err = git(mem, "commit", "-m", msg, "--", *paths)
                if rc != 0:
                    status, rc_out = f"FAILED: git commit: {err or 'unknown error'}", 1
                else:
                    rc, commit, err = git(mem, "rev-parse", "--short", "HEAD")
                    if rc != 0 or not commit:
                        commit, status, rc_out = None, f"FAILED: commit made but rev-parse failed: {err}", 1
                    else:
                        status = commit
    if written is None:
        written = "; ".join(paths) + " (not in a git repo, so no created/updated/deleted split)"
    print("KM close-out complete.")
    print(f"Written: {written}")
    print(f"Cases: {cases_written(mem, d)} | Retrieval queries: {len(d.get('retrieval') or [])} | MEMORY.md: {memory_lines(mem)} lines")
    print(f"Committed: {status}")
    print("Pushed: no")
    print(f"commit: {commit or 'null'}")
    return rc_out


if __name__ == "__main__":
    sys.exit(main())
