"""Run: python tests/test_km_auto_gate.py
Gates for automatic memory edits (issue #23, first slice). A synthetic memory folder
(tests/fixtures/auto_gate/mem) and a table of edits, each with the expected decision.
Nothing real is read or written; all work happens in a temp dir."""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parent
script = str(root.parent / "scripts" / "km_auto_gate.py")
fx = root / "fixtures" / "auto_gate"


def run(*args):
    p = subprocess.run([sys.executable, "-X", "utf8", "-I", script, *args], capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def tree_hash(mem):
    h = hashlib.sha256()
    for p in sorted(mem.rglob("*")):
        if p.is_file():
            h.update(str(p.relative_to(mem)).encode() + b"\0" + p.read_bytes())
    return h.hexdigest()


def setup(td):
    mem = td / "mem"
    shutil.copytree(fx / "mem", mem)
    # one rule file is CRLF, like a Windows checkout
    u = mem / "feedback_units.md"
    u.write_bytes(u.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    work = td / "root"
    (work / "logs").mkdir(parents=True)
    shutil.copy(fx / "facts.txt", work / "facts.txt")
    text = (fx / "edits.json").read_text(encoding="utf-8").replace("{ROOT}", work.as_posix())
    edits = td / "edits.json"
    edits.write_text(text, encoding="utf-8")
    return mem, edits, json.loads(text)


with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    mem, edits_file, edits = setup(td)
    original = {p.name: p.read_bytes() for p in mem.glob("*.md")}
    before = tree_hash(mem)

    # 1. gate: every edit gets the expected decision, and nothing is written
    rc, out, err = run("gate", "--mem", str(mem), "--edits", str(edits_file))
    assert rc == 0, (rc, err)
    res = json.loads(out)
    got = {}
    for i, (e, d) in enumerate(zip(edits, res["decisions"])):
        want = e["expect"]
        have = "APPLY" if d["decision"] == "APPLY" else f"HOLD:{d['category']}"
        assert have == want, f"edit {i} ({e['id']} {e['kind']} {e['file']}): expected {want}, got {have} {d['reasons']}"
        got[i] = d
    assert tree_hash(mem) == before, "gate must not write to the memory folder"
    n_apply = sum(1 for e in edits if e["expect"] == "APPLY")
    print(f"GATE: {len(edits)} edits, {n_apply} APPLY, {len(edits) - n_apply} HOLD, all as expected, nothing written")

    # 2. apply refuses without --opt-in and writes nothing
    rc, _, err = run("apply", "--mem", str(mem), "--edits", str(edits_file))
    assert rc != 0 and "opt-in" in err and tree_hash(mem) == before
    print("APPLY without --opt-in: refused")

    # 3. apply with --opt-in writes only the APPLY edits
    rc, out, err = run("apply", "--mem", str(mem), "--edits", str(edits_file), "--opt-in", "--run-id", "t1")
    assert rc == 0, (rc, err)
    rep = json.loads(out)
    assert rep["applied"] == ["e1", "e2", "e3", "e4", "e17"], rep
    assert (mem / "reference_new.md").exists() and not (mem / "reference_dead.md").exists()
    assert (mem / "MEMORY.md").read_bytes() == original["MEMORY.md"], "MEMORY.md is never touched"
    for name in ("feedback_send_reports.md", "reference_tools.md", "project_shop.md"):
        assert (mem / name).read_bytes() == original[name], f"{name} must be unchanged"
    units = (mem / "feedback_units.md").read_bytes()
    assert units.count(b"\n") == units.count(b"\r\n") and b"Round to one decimal" in units \
        and b"[[reference_tools]] covered it" in units, "CRLF file stays CRLF"
    assert b"/old/path" not in (mem / "reference_paths.md").read_bytes()
    assert (mem / "reference_paths.md").read_bytes().count(b"/old/cache") == 1
    runs = mem / "eval" / "auto_runs" / "t1"
    digest = (runs / "digest.md").read_text(encoding="utf-8")
    for needle in ("## Applied", "## Held for review", "## Not recommended", "## Warnings", "## Prepared commit",
                   "revert --mem", "--edit e2", "--approve e9", "km auto lean t1: 5 applied, 13 held",
                   "reference_new.md was created but nothing links to it yet", "git -C"):
        assert needle in digest, f"digest lacks {needle!r}"
    held = json.loads((runs / "held.json").read_text(encoding="utf-8"))
    assert [h["id"] for h in held][:3] == ["e5", "e6", "e7"] and len(held) == 13
    print("APPLY --opt-in: 5 applied, 13 held, digest with revert and approve commands, CRLF kept")

    # 4. revert refuses when the file changed, then restores bytes exactly
    new = mem / "reference_new.md"
    new.write_bytes(new.read_bytes() + b"edited by hand\n")
    rc, _, err = run("revert", "--mem", str(mem), "--run", "t1", "--edit", "e1")
    assert rc != 0 and "changed since" in err, err
    new.write_bytes(new.read_bytes().replace(b"edited by hand\n", b""))
    for eid in ("e3", "e2", "e4", "e1"):
        rc, _, err = run("revert", "--mem", str(mem), "--run", "t1", "--edit", eid)
        assert rc == 0, (eid, err)
    assert not new.exists()
    for name in ("feedback_units.md", "reference_paths.md"):
        assert (mem / name).read_bytes() == original[name], f"{name} not restored byte for byte"
    rc, _, err = run("revert", "--mem", str(mem), "--run", "t1", "--edit", "e2")
    assert rc != 0 and "already reverted" in err
    print("REVERT: refuses a changed file, restores 3 files byte for byte, removes the created file")

    # 5. --approve applies a held edit (the owner's yes) and says so; structural checks still hold
    rc, out, err = run("apply", "--mem", str(mem), "--edits", str(runs / "held.json"), "--opt-in",
                       "--approve", "e9,e13", "--run-id", "t2")
    assert rc == 0, err
    rep = json.loads(out)
    # e13 is inside the frontmatter: structural, never overridden. The duplicate-id edit
    # is unique inside held.json, so it applies there on its own merits.
    assert rep["applied"] == ["e9", "e1"] and "e13" in rep["held"], rep
    assert b"a cutter" in (mem / "reference_tools.md").read_bytes()
    d2 = (mem / "eval" / "auto_runs" / "t2" / "digest.md").read_text(encoding="utf-8")
    assert "approved by the owner" in d2
    print("APPROVE: held edit applied and recorded as approved; frontmatter edit still refused")

    # 6. no stored queries: insert_line and fix_fact cannot be checked, so they are held
    mem2 = td / "mem2"
    shutil.copytree(fx / "mem", mem2)
    (mem2 / "eval" / "retrieval.jsonl").unlink()
    only = [e for e in edits if e["id"] in ("e3", "e4")]
    f = td / "only.json"
    f.write_text(json.dumps(only), encoding="utf-8")
    rc, out, err = run("gate", "--mem", str(mem2), "--edits", str(f))
    for d in json.loads(out)["decisions"]:
        assert d["decision"] == "HOLD" and d["category"] == "gate_failed" \
            and any("cannot be checked" in r for r in d["reasons"]), d
    print("ZERO QUERIES: insert_line and fix_fact held")
print("ok")
