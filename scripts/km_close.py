"""Mechanical file appends of a `km` close-out (Step 8): cases, retrieval queries,
build-backlog rows and the log line. Stdlib only. Never runs git, never pushes,
never uses the network: the commit, the push and the final output stay in the skill.

Usage:  python km_close.py --mem DIR --input FILE [--dry-run]

Everything is validated first; on any error nothing is written and the exit code
is 2. Existing line endings are kept (CRLF files stay CRLF; new files use LF).

Input: one JSON object.
  session   string. Defaults to $CLAUDE_CODE_SESSION_ID; one of the two is required.
  date      "YYYY-MM-DD". Defaults to today.
  topic     string, the log topic (5-8 words).
  creates, updates, deletes   non-negative integers, for the log line.
  lean      true | false (default false). Lean adds ", lean" to the log line and
            takes no backlog items.
  cases     list (default []) of
              {"rule": slug, "model": id|"unknown", "situation": str, "expected": str,
               "check": null | {"type": tool_call_absent|tool_call_present|arg_matches|
                                file_unchanged, ...}, "kind": correction|violation|re-explanation}
            Appended to eval/cases.jsonl (eval/ is created if absent) as
            docs/evals.md §Files defines, with captured_by "km", status "open".
            Skipped when a line with the same rule + session exists (one case per rule
            per session).
  retrieval list (default []) of {"query": str, "expected": slug}. Appended to
            eval/retrieval.jsonl; an identical query + expected + session is skipped.
  backlog   list (default []) of {"candidate": str, "context": str}. Full runs only.
            Row `| date | candidate | context | open |` is added to the `## Backlog`
            table of build_backlog.md. A missing file is created with frontmatter, the
            table and a **Related:** line from backlog_links; indexing it is left to the
            skill.
  backlog_links  list of slugs for that **Related:** line (only used when the file is
            created; required then, so the new file is not an island).

The log line `date | topic | N creates, N updates, N deletes, N cases[, lean]` goes at the
end of log.md, under its `---` separator (a log.md without one gets the separator first).
N cases is the number of case lines written, not skipped.

Exit: 0 done (skips are reported, not errors), 2 bad input or unwritable file.
"""
import argparse
import json
import os
import re
import sys
from datetime import date as _date
from pathlib import Path

KINDS = ("correction", "violation", "re-explanation")
CHECK_TYPES = ("tool_call_absent", "tool_call_present", "arg_matches", "file_unchanged")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SLUG_RE = re.compile(r"^[A-Za-z0-9_.:\-]+$")
BACKLOG_HEAD = "## Backlog"
TABLE_HEAD = ["| Date | Candidate | Session context | Status |", "|---|---|---|---|"]


class Bad(Exception):
    pass


def jline(obj):
    return json.dumps(obj, ensure_ascii=False)


def read_lines(path):
    if not path.exists():
        return [], "\n", False
    data = path.read_bytes()
    if not data:
        return [], "\n", True
    text = data.decode("utf-8")
    eol = "\r\n" if text.count("\r\n") * 2 > text.count("\n") else "\n"
    text = text.replace("\r\n", "\n")
    return (text[:-1] if text.endswith("\n") else text).split("\n"), eol, True


def join_lines(lines, eol):
    return (eol.join(lines) + eol).encode("utf-8")


def need_str(obj, key, where):
    v = obj.get(key)
    if not isinstance(v, str) or not v.strip():
        raise Bad(f"{where}: '{key}' must be a non-empty string")
    if "\n" in v or "\r" in v:
        raise Bad(f"{where}: '{key}' must be one line")
    return v.strip()


def need_count(obj, key):
    v = obj.get(key)
    if isinstance(v, bool) or not isinstance(v, int) or v < 0:
        raise Bad(f"'{key}' must be a non-negative integer")
    return v


def need_slug(obj, key, where):
    v = need_str(obj, key, where)
    if not SLUG_RE.match(v):
        raise Bad(f"{where}: '{key}' is not a slug: {v!r}")
    return v


def validate(raw):
    if not isinstance(raw, dict):
        raise Bad("input must be a JSON object")
    known = {"session", "date", "topic", "creates", "updates", "deletes", "lean",
             "cases", "retrieval", "backlog", "backlog_links"}
    extra = sorted(set(raw) - known)
    if extra:
        raise Bad(f"unknown key(s): {', '.join(extra)}")
    session = raw.get("session") or os.environ.get("CLAUDE_CODE_SESSION_ID", "")
    if not isinstance(session, str) or not session.strip():
        raise Bad("'session' missing and $CLAUDE_CODE_SESSION_ID is not set")
    day = raw.get("date") or _date.today().isoformat()
    if not isinstance(day, str) or not DATE_RE.match(day):
        raise Bad("'date' must be YYYY-MM-DD")
    lean = raw.get("lean", False)
    if not isinstance(lean, bool):
        raise Bad("'lean' must be true or false")
    for k in ("cases", "retrieval", "backlog", "backlog_links"):
        if not isinstance(raw.get(k, []), list):
            raise Bad(f"'{k}' must be a list")
    cases = []
    for i, c in enumerate(raw.get("cases", [])):
        w = f"cases[{i}]"
        if not isinstance(c, dict):
            raise Bad(f"{w} must be an object")
        extra = sorted(set(c) - {"rule", "model", "situation", "expected", "check", "kind"})
        if extra:
            raise Bad(f"{w}: unknown key(s): {', '.join(extra)}")
        kind = need_str(c, "kind", w)
        if kind not in KINDS:
            raise Bad(f"{w}: 'kind' must be one of {', '.join(KINDS)}")
        if "check" not in c:
            raise Bad(f"{w}: 'check' is required (an object, or null for a judgment rule)")
        chk = c["check"]
        if chk is not None and not (isinstance(chk, dict) and chk.get("type") in CHECK_TYPES):
            raise Bad(f"{w}: 'check' must be null or an object whose 'type' is one of {', '.join(CHECK_TYPES)}")
        cases.append({"rule": need_slug(c, "rule", w), "session": session.strip(), "model": need_str(c, "model", w),
                      "date": day, "situation": need_str(c, "situation", w), "expected": need_str(c, "expected", w),
                      "check": chk, "kind": kind, "captured_by": "km", "status": "open"})
    retrieval = []
    for i, r in enumerate(raw.get("retrieval", [])):
        w = f"retrieval[{i}]"
        if not isinstance(r, dict) or set(r) - {"query", "expected"}:
            raise Bad(f"{w} must be an object with 'query' and 'expected' only")
        retrieval.append({"query": need_str(r, "query", w), "expected": need_slug(r, "expected", w),
                          "session": session.strip(), "date": day})
    backlog = []
    for i, b in enumerate(raw.get("backlog", [])):
        w = f"backlog[{i}]"
        if not isinstance(b, dict) or set(b) - {"candidate", "context"}:
            raise Bad(f"{w} must be an object with 'candidate' and 'context' only")
        backlog.append((need_str(b, "candidate", w), need_str(b, "context", w)))
    links = raw.get("backlog_links", [])
    for s in links:
        if not isinstance(s, str) or not SLUG_RE.match(s):
            raise Bad(f"backlog_links: not a slug: {s!r}")
    if lean and backlog:
        raise Bad("backlog items are full-run only; this input says lean")
    return {"day": day, "lean": lean, "topic": need_str(raw, "topic", "input"),
            "creates": need_count(raw, "creates"), "updates": need_count(raw, "updates"),
            "deletes": need_count(raw, "deletes"), "cases": cases, "retrieval": retrieval,
            "backlog": backlog, "links": links}


def cell(s):
    return s.replace("|", "\\|")


def plan_jsonl(path, new, same, label, out):
    """Append the entries of `new` not already present (by `same`). -> (bytes|None, wrote)"""
    lines, eol, _ = read_lines(path)
    seen = []
    for ln in lines:
        try:
            obj = json.loads(ln)
        except ValueError:
            continue
        if isinstance(obj, dict):
            seen.append(obj)
    wrote = 0
    for e in new:
        if any(same(e, o) for o in seen):
            out.append(f"skipped {label}: {e.get('rule') or e.get('query')!r} (already recorded this session)")
            continue
        seen.append(e)
        lines.append(jline(e))
        out.append(f"wrote {label}: {e.get('rule') or e.get('query')!r}")
        wrote += 1
    return (join_lines(lines, eol) if wrote else None), wrote


def plan_backlog(path, v, out):
    lines, eol, existed = read_lines(path)
    rows = []
    for cand, ctx in v["backlog"]:
        row = f"| {v['day']} | {cell(cand)} | {cell(ctx)} | open |"
        if row in lines or row in rows:
            out.append(f"skipped backlog row: {cand!r} (identical row exists)")
        else:
            rows.append(row)
            out.append(f"wrote backlog row: {cand!r}")
    if not rows:
        return None
    if not existed or not lines:
        if not v["links"]:
            raise Bad("build_backlog.md is absent: 'backlog_links' (slugs it links out to) is required to create it")
        lines = ["---", "name: build_backlog",
                 "description: Open build and automation candidates from close-outs; read when choosing what to build next",
                 "metadata:", "  node_type: memory", "  type: project", "---", "", "# Build backlog", "",
                 BACKLOG_HEAD, "", *TABLE_HEAD, "", "**Related:** " + " · ".join(f"[[{s}]]" for s in v["links"])]
        out.append("created build_backlog.md (index it in MEMORY.md or a hub)")
        existed = False
    h = next((i for i, ln in enumerate(lines) if ln.strip() == BACKLOG_HEAD), None)
    if h is None:
        lines += ["", BACKLOG_HEAD, "", *TABLE_HEAD]
        h = len(lines) - 4
    end = h + 1
    while end < len(lines) and lines[end].strip() == "":
        end += 1
    start = end
    while end < len(lines) and lines[end].lstrip().startswith("|"):
        end += 1
    if end == start:  # heading without a table
        lines[start:start] = [*TABLE_HEAD]
        end = start + len(TABLE_HEAD)
    lines[end:end] = rows
    return join_lines(lines, eol)


def plan_log(path, v, wrote_cases, out):
    lines, eol, _ = read_lines(path)
    entry = f"{v['day']} | {v['topic']} | {v['creates']} creates, {v['updates']} updates, {v['deletes']} deletes, {wrote_cases} cases"
    if v["lean"]:
        entry += ", lean"
    if "---" not in [ln.strip() for ln in lines]:
        lines.append("---")
        out.append("log.md had no '---' separator: added one")
    lines.append(entry)
    out.append(f"wrote log line: {entry}")
    return join_lines(lines, eol)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mem", required=True, help="memory folder")
    ap.add_argument("--input", required=True, help="JSON file of confirmed items (format below)")
    ap.add_argument("--dry-run", action="store_true", help="validate and report, write nothing")
    a = ap.parse_args(argv)
    out = []
    try:
        mem = Path(a.mem)
        if not mem.is_dir():
            raise Bad(f"memory folder not found: {mem}")
        try:
            raw = json.loads(Path(a.input).read_text(encoding="utf-8-sig"))
        except OSError as e:
            raise Bad(f"cannot read input: {e}")
        except ValueError as e:
            raise Bad(f"input is not valid JSON: {e}")
        v = validate(raw)
        writes = []
        ev = mem / "eval"
        data, n_cases = plan_jsonl(ev / "cases.jsonl", v["cases"],
                                   lambda e, o: o.get("rule") == e["rule"] and o.get("session") == e["session"],
                                   "case", out)
        if data is not None:
            writes.append((ev / "cases.jsonl", data))
        data, _ = plan_jsonl(ev / "retrieval.jsonl", v["retrieval"],
                             lambda e, o: (o.get("query"), o.get("expected"), o.get("session"))
                             == (e["query"], e["expected"], e["session"]), "retrieval query", out)
        if data is not None:
            writes.append((ev / "retrieval.jsonl", data))
        if v["backlog"]:
            data = plan_backlog(mem / "build_backlog.md", v, out)
            if data is not None:
                writes.append((mem / "build_backlog.md", data))
        writes.append((mem / "log.md", plan_log(mem / "log.md", v, n_cases, out)))
        if not a.dry_run:
            for p, data in writes:
                try:
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_bytes(data)
                except OSError as e:
                    raise Bad(f"cannot write {p}: {e}")
    except Bad as e:
        print(f"km_close: {e}", file=sys.stderr)
        print("km_close: nothing written", file=sys.stderr)
        return 2
    if a.dry_run:
        out.insert(0, "dry run: nothing written")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
