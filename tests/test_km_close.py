"""Run: python tests/test_km_close.py
km_close.py, the mechanical file appends of a close-out. A synthetic memory folder
(tests/fixtures/close) is copied to a temp dir; nothing real is read or written."""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parent
script = str(root.parent / "scripts" / "km_close.py")
fx = root / "fixtures" / "close"
fails = 0
counter = 0


def check(name, cond, extra=""):
    global fails
    if not cond:
        fails += 1
        print(f"FAIL {name} {extra}")


def run(*args, env=None):
    p = subprocess.run([sys.executable, "-X", "utf8", "-I", script, *args], capture_output=True, text=True, env=env)
    return p.returncode, p.stdout, p.stderr


def fresh(base, crlf=False):
    """A new work dir with its own copy of the fixture memory folder -> (dir, mem)."""
    global counter
    counter += 1
    d = base / f"case{counter}"
    d.mkdir()
    mem = d / "mem"
    shutil.copytree(fx / "mem", mem)
    if crlf:
        for f in mem.glob("*.md"):
            f.write_bytes(f.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    return d, mem


def load_input(**over):
    d = json.loads((fx / "input.json").read_text(encoding="utf-8"))
    d.update(over)
    return d


def go(d, mem, data, *extra, env=None):
    f = d / "in.json"
    f.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")
    return run("--mem", str(mem), "--input", str(f), *extra, env=env)


def lines(p):
    return p.read_bytes().decode("utf-8").replace("\r\n", "\n").split("\n")[:-1]


def tree(mem):
    return {p.relative_to(mem).as_posix(): p.read_bytes() for p in sorted(mem.rglob("*")) if p.is_file()}


with tempfile.TemporaryDirectory() as t:
    base = Path(t)

    # full close-out: exact formats, eval/ created
    d, mem = fresh(base)
    rc, out, err = go(d, mem, load_input())
    check("full rc", rc == 0, err)
    cases = lines(mem / "eval" / "cases.jsonl")
    check("two cases", len(cases) == 2)
    c0 = json.loads(cases[0])
    check("case key order and values", list(c0) == ["rule", "session", "model", "date", "situation", "expected",
          "check", "kind", "captured_by", "status"] and c0["captured_by"] == "km" and c0["status"] == "open"
          and c0["session"] == "sess-1" and c0["date"] == "2026-06-01" and c0["check"]["type"] == "tool_call_absent")
    check("case line is skill format", cases[0].startswith(
        '{"rule": "feedback_sheet_read_before_write", "session": "sess-1", "model": "claude-sonnet-5-5", "date": "2026-06-01", "situation":'))
    check("null check", json.loads(cases[1])["check"] is None)
    ret = lines(mem / "eval" / "retrieval.jsonl")
    check("retrieval line", ret == ['{"query": "where do the greenhouse readings end up?", "expected": '
          '"reference_greenhouse_sheet", "session": "sess-1", "date": "2026-06-01"}'], str(ret))
    log = lines(mem / "log.md")
    check("log line", log[-1] == "2026-06-01 | sheet write rules and retry wrapper | 2 creates, 1 updates, 0 deletes, 2 cases", log[-1])
    check("log separator kept", log[-3] == "---" and log[-2].startswith("2026-05-01"))
    bl = lines(mem / "build_backlog.md")
    old = "| 2026-05-01 | retry wrapper | flaky sheet writes | open |"
    check("backlog row after last row", bl[bl.index(old) + 1] ==
          "| 2026-06-01 | sheet header cache \\| with pipe | repeated header reads | open |", str(bl))
    check("backlog tail kept", bl[-1].startswith("**Related:**"))

    # rerun: dedup of cases (rule+session), retrieval and backlog row
    before = tree(mem)
    rc, out, err = go(d, mem, load_input())
    after = tree(mem)
    check("rerun rc", rc == 0)
    for f in ("eval/cases.jsonl", "eval/retrieval.jsonl", "build_backlog.md"):
        check(f"rerun leaves {f}", before[f] == after[f])
    check("rerun reports skips", out.count("skipped") == 4, out)
    check("rerun log says 0 cases", lines(mem / "log.md")[-1].endswith("0 deletes, 0 cases"))

    # same rule in another session: new line; same rule twice in one input: one line
    dd = load_input(session="sess-2")
    dd["cases"] = [dd["cases"][0], dict(dd["cases"][0])]
    dd["backlog"] = []
    rc, out, err = go(d, mem, dd)
    check("other session adds one", rc == 0 and len(lines(mem / "eval" / "cases.jsonl")) == 3)

    # lean: ", lean" suffix; backlog items refused
    d, mem = fresh(base)
    dd = load_input(lean=True)
    dd["backlog"] = []
    rc, out, err = go(d, mem, dd)
    check("lean rc", rc == 0, err)
    check("lean suffix", lines(mem / "log.md")[-1].endswith("2 cases, lean"))
    check("lean leaves backlog", (mem / "build_backlog.md").read_bytes() == (fx / "mem" / "build_backlog.md").read_bytes())
    d, mem = fresh(base)
    rc, out, err = go(d, mem, load_input(lean=True))
    check("lean with backlog refused", rc == 2 and "lean" in err)

    # CRLF files stay CRLF, including new lines; new files are LF
    d, mem = fresh(base, crlf=True)
    (mem / "eval").mkdir()
    (mem / "eval" / "cases.jsonl").write_bytes(b'{"rule": "old", "session": "s0"}\r\n')
    rc, out, err = go(d, mem, load_input())
    check("crlf rc", rc == 0, err)
    for f in ("log.md", "build_backlog.md", "eval/cases.jsonl"):
        b = (mem / f).read_bytes()
        check(f"crlf kept {f}", b.count(b"\r\n") == b.count(b"\n") and b.count(b"\n") > 0)
    check("crlf old case line intact", (mem / "eval" / "cases.jsonl").read_bytes().startswith(b'{"rule": "old", "session": "s0"}\r\n'))
    check("new file is LF", b"\r" not in (mem / "eval" / "retrieval.jsonl").read_bytes())

    # no trailing newline: the append goes on a new line and the file still ends bare
    d, mem = fresh(base)
    (mem / "log.md").write_bytes(b"---\n2026-05-01 | x | 0 creates, 0 updates, 0 deletes, 0 cases")
    (mem / "build_backlog.md").write_bytes(b"# B\n\n## Backlog\n\n| Date | Candidate | Session context | Status |\n|---|---|---|---|\n| 2026-05-01 | a | b | open |")
    (mem / "eval").mkdir()
    (mem / "eval" / "cases.jsonl").write_bytes(b'{"rule": "old", "session": "s0"}')
    rc, out, err = go(d, mem, load_input())
    b = (mem / "log.md").read_bytes()
    check("no trailing newline kept", rc == 0 and b.startswith(b"---\n2026-05-01 | x | 0 creates, 0 updates, 0 deletes, 0 cases\n2026-06-01 |")
          and not b.endswith(b"\n"), repr(b))
    bb = (mem / "build_backlog.md").read_bytes()
    check("backlog bare end kept", bb.endswith(b"open |") and bb.count(b"\n") == 7, repr(bb))
    cb = (mem / "eval" / "cases.jsonl").read_bytes()
    check("jsonl bare end kept", cb.startswith(b'{"rule": "old", "session": "s0"}\n{"rule"') and not cb.endswith(b"\n"), repr(cb))

    # mixed line endings: untouched lines keep their own endings
    d, mem = fresh(base)
    (mem / "log.md").write_bytes(b"# Log\r\n---\n2026-05-01 | x | 0 creates, 0 updates, 0 deletes, 0 cases\r\n")
    rc, out, err = go(d, mem, load_input())
    b = (mem / "log.md").read_bytes()
    check("mixed endings preserved", rc == 0 and b.startswith(b"# Log\r\n---\n2026-05-01 | x | 0 creates, 0 updates, 0 deletes, 0 cases\r\n2026-06-01 |")
          and b.endswith(b"\r\n"), repr(b))

    # BOM: kept, and does not defeat the dedup of the first line
    d, mem = fresh(base)
    (mem / "eval").mkdir()
    first = json.dumps({"rule": "feedback_sheet_read_before_write", "session": "sess-1"})
    (mem / "eval" / "cases.jsonl").write_bytes(b"\xef\xbb\xbf" + first.encode() + b"\n")
    (mem / "log.md").write_bytes(b"\xef\xbb\xbf---\n")
    rc, out, err = go(d, mem, load_input())
    cb = (mem / "eval" / "cases.jsonl").read_bytes()
    check("bom kept", rc == 0 and cb.startswith(b"\xef\xbb\xbf{") and cb.count(b"\xef\xbb\xbf") == 1
          and (mem / "log.md").read_bytes().startswith(b"\xef\xbb\xbf---\n"), err)
    check("bom does not defeat dedup", cb.count(b"feedback_sheet_read_before_write") == 1 and "skipped case" in out, out)

    # non-UTF-8 file: refused, nothing written
    d, mem = fresh(base)
    (mem / "log.md").write_bytes(b"---\n2026-05-01 | caf\xe9\n")
    before = tree(mem)
    rc, out, err = go(d, mem, load_input())
    check("non-utf8 refused", rc == 2 and "UTF-8" in err and "nothing written" in err, err)
    check("non-utf8 wrote nothing", tree(mem) == before)

    # unreadable target (a directory where a file belongs): refused, nothing written
    d, mem = fresh(base)
    (mem / "eval").mkdir()
    (mem / "eval" / "retrieval.jsonl").mkdir()
    before = tree(mem)
    rc, out, err = go(d, mem, load_input())
    check("unreadable target refused", rc == 2 and "nothing written" in err, err)
    check("unreadable target wrote nothing", tree(mem) == before and not (mem / "eval" / "cases.jsonl").exists())

    # input inside the memory folder: refused
    d, mem = fresh(base)
    f = mem / "in.json"
    f.write_text(json.dumps(load_input()), encoding="utf-8")
    rc, out, err = run("--mem", str(mem), "--input", str(f))
    check("input inside mem refused", rc == 2 and "outside the memory folder" in err
          and (mem / "log.md").read_bytes() == (fx / "mem" / "log.md").read_bytes(), err)

    # written paths are listed, relative to --mem
    d, mem = fresh(base)
    rc, out, err = go(d, mem, load_input())
    files = [ln[6:] for ln in out.splitlines() if ln.startswith("file: ")]
    check("file lines", files == ["eval/cases.jsonl", "eval/retrieval.jsonl", "build_backlog.md", "log.md"], str(files))
    check("no temp files left", not list(mem.rglob("*.km_tmp")))
    d, mem = fresh(base)
    rc, out, err = go(d, mem, load_input(), "--dry-run")
    check("dry run lists would-write", "would write file: log.md" in out and not any(ln.startswith("file: ") for ln in out.splitlines()), out)

    # a failure while writing temp files leaves nothing behind
    sys.path.insert(0, str(root.parent / "scripts"))
    import km_close
    d, mem = fresh(base)
    before = tree(mem)
    calls = []
    real = km_close.write_tmp

    def flaky(tmp, data):
        calls.append(tmp)
        if len(calls) == 3:
            raise OSError("disk full")
        real(tmp, data)

    km_close.write_tmp = flaky
    f = d / "in.json"
    f.write_text(json.dumps(load_input()), encoding="utf-8")
    sys.stderr = open(os.devnull, "w")
    rc = km_close.main(["--mem", str(mem), "--input", str(f)])
    sys.stderr = sys.__stderr__
    km_close.write_tmp = real
    check("partial write refused", rc == 2 and len(calls) == 3)
    check("partial write left nothing", tree(mem) == before and not list(mem.rglob("*.km_tmp")))

    # missing build_backlog.md: backlog_links required, then created with table and links
    d, mem = fresh(base)
    (mem / "build_backlog.md").unlink()
    before = tree(mem)
    rc, out, err = go(d, mem, load_input())
    check("missing backlog without links refused", rc == 2 and "backlog_links" in err, err)
    check("refusal wrote nothing", tree(mem) == before)
    rc, out, err = go(d, mem, load_input(backlog_links=["reference_a", "reference_b"]))
    bl = lines(mem / "build_backlog.md")
    check("backlog created", rc == 0 and "created build_backlog.md" in out, err)
    check("backlog frontmatter", bl[0] == "---" and "name: build_backlog" in bl and "  type: project" in bl and bl[6] == "---", str(bl[:8]))
    check("backlog table", "## Backlog" in bl and "|---|---|---|---|" in bl and
          "| 2026-06-01 | sheet header cache \\| with pipe | repeated header reads | open |" in bl)
    check("backlog outbound links", bl[-1] == "**Related:** [[reference_a]] · [[reference_b]]", bl[-1])

    # backlog file without a ## Backlog heading gets one at the end
    d, mem = fresh(base)
    (mem / "build_backlog.md").write_bytes(b"# Build backlog\n\nNotes only.\n")
    rc, out, err = go(d, mem, load_input())
    bl = lines(mem / "build_backlog.md")
    check("heading added", rc == 0 and bl[-1].startswith("| 2026-06-01 |") and bl[-5] == "## Backlog", str(bl))

    # missing log.md is created with the line only; a log.md without a separator gets none
    d, mem = fresh(base)
    (mem / "log.md").unlink()
    rc, out, err = go(d, mem, load_input())
    log = lines(mem / "log.md")
    check("log created, no separator", rc == 0 and len(log) == 1 and log[0].startswith("2026-06-01 |"), str(log))
    d, mem = fresh(base)
    (mem / "log.md").write_bytes(b"# Log\n\nfree text\n")
    rc, out, err = go(d, mem, load_input())
    log = lines(mem / "log.md")
    check("no separator added", rc == 0 and log[-2] == "free text" and "---" not in log and "separator" not in out + err, str(log))

    # dry run writes nothing
    d, mem = fresh(base)
    before = tree(mem)
    rc, out, err = go(d, mem, load_input(), "--dry-run")
    check("dry run", rc == 0 and tree(mem) == before and "dry run" in out and "separator" not in out)

    # bad input: refused, nothing written, exit 2
    c1 = load_input()["cases"][0]
    bad = {
        "not json": "{nope",
        "not object": "[1]",
        "unknown key": load_input(extra=1),
        "missing topic": {k: v for k, v in load_input().items() if k != "topic"},
        "negative count": load_input(creates=-1),
        "bool count": load_input(updates=True),
        "bad date": load_input(date="01/06/2026"),
        "bad kind": load_input(cases=[dict(c1, kind="mistake")]),
        "missing check": load_input(cases=[{k: v for k, v in c1.items() if k != "check"}]),
        "bad check type": load_input(cases=[dict(c1, check={"type": "vibes"})]),
        "blank rule": load_input(cases=[dict(c1, rule=" ")]),
        "multiline situation": load_input(cases=[dict(c1, situation="a\nb")]),
        "retrieval junk": load_input(retrieval=[{"query": "q", "expected": "s", "x": 1}]),
        "good then bad item": load_input(cases=[c1, dict(c1, rule="other", kind="nope")]),
    }
    for name, data in bad.items():
        d, mem = fresh(base)
        before = tree(mem)
        rc, out, err = go(d, mem, data)
        check(f"bad input '{name}' exits 2", rc == 2, f"rc={rc} err={err}")
        check(f"bad input '{name}' says why", err.startswith("km_close:") and "nothing written" in err, err)
        check(f"bad input '{name}' writes nothing", tree(mem) == before)
    d, mem = fresh(base)
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CODE_SESSION_ID"}
    rc, out, err = go(d, mem, {k: v for k, v in load_input().items() if k != "session"}, env=env)
    check("no session refused", rc == 2 and "session" in err)
    env["CLAUDE_CODE_SESSION_ID"] = "from-env"
    rc, out, err = go(d, mem, {k: v for k, v in load_input().items() if k != "session"}, env=env)
    check("session from env", rc == 0 and json.loads(lines(mem / "eval" / "cases.jsonl")[0])["session"] == "from-env", err)

    # the check contract: the skill text and example match what the script accepts
    skill = (root.parent / "skills" / "km" / "SKILL.md").read_text(encoding="utf-8")
    sys.path.insert(0, str(root.parent / "scripts"))
    import km_close
    check("skill names every check type", all(f"`{t}`" in skill for t in km_close.CHECK_TYPES))
    m = re.search(r'"check":(\{.*?\})\|null', skill)
    check("skill example has a check object", m is not None)
    if m:
        ex = json.loads(m.group(1).replace("<regex>", "x"))
        case = dict(load_input()["cases"][0], check=ex)
        d, mem = fresh(base)
        rc, out, err = go(d, mem, load_input(cases=[case], backlog=[]))
        check("skill example check passes", rc == 0, err)
    d, mem = fresh(base)
    prose = dict(load_input()["cases"][0], check="no `send` command with a new subject line")
    rc, out, err = go(d, mem, load_input(cases=[prose], backlog=[]))
    check("prose check rejected", rc == 2 and "'check' must be null or an object" in err, err)
    check("prose rejected writes nothing", not (mem / "eval" / "cases.jsonl").exists())
    bad = dict(load_input()["cases"][0], check={"type": "no_send_with_new_subject"})
    rc, out, err = go(d, mem, load_input(cases=[bad], backlog=[]))
    check("unknown check type rejected", rc == 2, err)

    # missing memory folder, missing input file
    rc, out, err = run("--mem", str(base / "absent"), "--input", str(fx / "input.json"))
    check("missing mem", rc == 2 and "memory folder not found" in err)
    rc, out, err = run("--mem", str(fx / "mem"), "--input", str(base / "absent.json"))
    check("missing input", rc == 2 and "cannot read input" in err)

    # --help carries the input format
    rc, out, err = run("--help")
    check("help documents format", rc == 0 and "cases " in out and "backlog_links" in out and "CRLF" in out)

    # km_close never creates git state
    check("no git side effects", not list(base.glob("**/.git")))

if fails:
    print(f"{fails} failure(s)")
    sys.exit(1)
print("ok: km_close")
