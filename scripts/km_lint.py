"""Report-only lint of memory files: the mechanical parts of km Behaviours D, E, G and H.
Stdlib only. Never writes, never runs git, never uses the network. Exit 0 whatever it
finds (it reports, the skill decides); exit 2 only for bad arguments or a missing folder.

Usage:  python km_lint.py --mem DIR [slug ...] [--stale-days N] [--json]

With slugs (the files this run created or touched) only those are checked; without,
every top-level *.md except MEMORY.md and log.md. Subfolders are never read.

Checks, one finding per line as `<slug>: <check>: <detail>`:
  D  missing-why / missing-how   feedback and project files need **Why:** and **How to apply:**
     missing-basis               feedback needs metadata.basis: fact | preference | compensation
  E  frontmatter                 name = filename slug, description, metadata.node_type = memory,
                                 metadata.type in feedback | project | reference | user
     description                 more than 2 lines or 400 characters, or just the slug
     missing-trigger             feedback and project files need **Trigger:**
     no-link-line                no **Related:** or **Cluster:** line
     tally                       "confirmed again" style counters (violations go to eval/cases.jsonl)
  G  stale-path                  an absolute or ~ path in a code span that does not exist here
     stamp                       `unverified YYYY-MM-DD` older than --stale-days (default 30), or
                                 `unverified` with no valid date
  H  dead-link                   a [[slug]] or supersedes: target with no file (code spans are
                                 placeholders, not links). Reachability stays with km_graph_check.py.
What it cannot judge stays with the model: whether a description is a retrieval signal, whether
the body leads with the rule, whether a path is meant as a placeholder.
"""
import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

SKIP = {"MEMORY.md", "log.md"}
TYPES = ("feedback", "project", "reference", "user")
BASES = ("fact", "preference", "compensation")
WIKILINK = re.compile(r"\[\[([^\]|#]+?)\]\]")
FENCE = re.compile(r"```.*?```", re.S)
SPAN = re.compile(r"`([^`\n]+)`")
PATH = re.compile(r"^(?:[A-Za-z]:[\\/]|~[\\/]|/[^\s/]+/)[^\s]*$")  # `/compact` is a command, not a path
PLACEHOLDER = re.compile(r"[<>*?{}$]|\.\.\.|YYYY")
STAMP = re.compile(r"unverified(?:\s+(\d{4}-\d{2}-\d{2}))?")
TALLY = re.compile(r"confirmed again|re-?confirmed|\(\s*\d+\s*(?:x|times)\s*\)|\bviolated\s+\d+", re.I)


def parse(text):
    """-> (frontmatter dict with 'metadata' sub-dict, body). Minimal YAML: key: value lines."""
    text = text.lstrip("﻿").replace("\r\n", "\n")
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---", 3)
    if end < 0:
        return None, text
    fm, meta, cur = {}, {}, None
    for line in text[4:end].split("\n"):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"(\s*)([A-Za-z_]+):\s*(.*)$", line)
        if not m:
            if cur is not None and line.startswith((" ", "\t")):
                fm[cur] += "\n" + line.strip()  # continuation of a multi-line value
            continue
        indent, key, val = m.groups()
        val = re.sub(r"\s+#.*$", "", val).strip().strip("\"'")
        if indent:
            meta[key] = val
        else:
            fm[key] = val
            cur = key
    fm["metadata"] = meta
    return fm, text[end + 4:]


def check_file(slug, path, files, today, stale_days):
    out = []

    def add(check, detail):
        out.append({"slug": slug, "check": check, "detail": detail})

    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as e:
        add("unreadable", str(e))
        return out
    fm, body = parse(text)
    typ = None
    if fm is None:
        add("frontmatter", "no frontmatter block")
        fm = {"metadata": {}}
    else:
        meta = fm["metadata"]
        typ = meta.get("type")
        if fm.get("name") != slug:
            add("frontmatter", f"name is {fm.get('name')!r}, must equal the filename slug")
        if not fm.get("description"):
            add("frontmatter", "description missing")
        else:
            d = fm["description"]
            if d.count("\n") >= 2 or len(d) > 400:
                add("description", "over 2 lines or 400 characters")
            if d.strip().lower().replace("_", " ") in (slug.lower().replace("_", " "), slug.lower()):
                add("description", "just the slug, not a retrieval signal")
        if meta.get("node_type") != "memory":
            add("frontmatter", "metadata.node_type must be memory")
        if typ not in TYPES:
            add("frontmatter", f"metadata.type must be one of {', '.join(TYPES)} (got {typ!r})")
    is_fb = typ == "feedback" or slug.startswith("feedback_")
    if is_fb or typ == "project":
        if "**Why:**" not in body:
            add("missing-why", "no **Why:** line")
        if "**How to apply:**" not in body:
            add("missing-how", "no **How to apply:** line")
        if "**Trigger:**" not in body:
            add("missing-trigger", "no **Trigger:** line")
    if is_fb:
        b = fm["metadata"].get("basis") or fm.get("basis")
        if not b:
            add("missing-basis", "feedback needs metadata.basis")
        elif b not in BASES:
            add("missing-basis", f"basis {b!r} is not one of {', '.join(BASES)}")
    if "**Related:**" not in body and "**Cluster:**" not in body:
        add("no-link-line", "no **Related:** or **Cluster:** line")
    plain = FENCE.sub("", body)
    for m in TALLY.finditer(plain):
        add("tally", f"{m.group(0)!r}: violations go to eval/cases.jsonl, not the file")
    # H: links outside code spans
    nospan = SPAN.sub("", plain)
    for t in sorted({x.strip() for x in WIKILINK.findall(nospan)} - {""}):
        if t not in files:
            add("dead-link", f"[[{t}]] has no file")
    for t in re.split(r"[,\s\[\]]+", fm.get("supersedes", "")):
        if t and t.removesuffix(".md") not in files:
            add("dead-link", f"supersedes {t} has no file")
    # G: paths and stamps
    for sp in sorted({s.strip() for s in SPAN.findall(plain)}):
        if "://" in sp or PLACEHOLDER.search(sp) or not PATH.match(sp):
            continue
        if not Path(sp).expanduser().exists():
            add("stale-path", f"{sp} does not exist here (verify, fix or drop)")
    for m in STAMP.finditer(plain):
        if not m.group(1):
            add("stamp", "`unverified` without a YYYY-MM-DD date")
            continue
        try:
            age = (today - datetime.strptime(m.group(1), "%Y-%m-%d").date()).days
        except ValueError:
            add("stamp", f"invalid date {m.group(1)}")
            continue
        if age > stale_days:
            add("stamp", f"unverified {m.group(1)} is {age} days old (re-verify or drop the claim)")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mem", required=True, help="memory folder")
    ap.add_argument("slugs", nargs="*", help="check only these files (default: all top-level)")
    ap.add_argument("--stale-days", type=int, default=30)
    ap.add_argument("--today", help="YYYY-MM-DD, for tests (default: today)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    mem = Path(a.mem) if a.mem.strip() else None
    if mem is None or not mem.is_dir():
        print(f"km_lint: memory folder not found: {a.mem!r}", file=sys.stderr)
        return 2
    try:
        today = datetime.strptime(a.today, "%Y-%m-%d").date() if a.today else date.today()
    except ValueError:
        print("km_lint: --today must be YYYY-MM-DD", file=sys.stderr)
        return 2
    files = {p.stem: p for p in mem.glob("*.md") if p.name not in SKIP}
    want = [s.removesuffix(".md") for s in a.slugs] or sorted(files)
    findings, missing = [], []
    for s in want:
        if s in files:
            findings += check_file(s, files[s], files.keys(), today, a.stale_days)
        else:
            missing.append(s)
            findings.append({"slug": s, "check": "missing-file", "detail": "no such file in the memory folder"})
    if a.json:
        print(json.dumps({"checked": len(want) - len(missing), "findings": findings}, indent=1))
        return 0
    for f in findings:
        print(f"{f['slug']}: {f['check']}: {f['detail']}")
    n_files = len({f["slug"] for f in findings})
    print(f"km_lint: {len(findings)} finding(s) in {n_files} file(s); {len(want) - len(missing)} checked (report only, nothing changed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
