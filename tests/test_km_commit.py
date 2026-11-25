"""Run: python -X utf8 -I tests/test_km_commit.py
km_commit.py: commits only the named paths, refuses whole-tree paths, prints the closing block,
never pushes. Synthetic git repo in a temp dir."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

script = str(Path(__file__).resolve().parent.parent / "scripts" / "km_commit.py")


IDENT = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
         "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid"}  # CI runners have no git identity


def run(*a, env=None):
    env = {**os.environ, **IDENT, **(env or {})}
    p = subprocess.run([sys.executable, "-X", "utf8", "-I", script, *a], capture_output=True, text=True, encoding="utf-8", env=env)
    return p.returncode, p.stdout, p.stderr


def git(repo, *a):
    p = subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.invalid",
                        "-c", "commit.gpgsign=false", *a], capture_output=True, text=True, encoding="utf-8")
    assert p.returncode == 0, (a, p.stderr)
    return p.stdout.strip()


with tempfile.TemporaryDirectory() as t:
    base = Path(t)
    mem = base / "mem"
    mem.mkdir()
    git(mem, "init", "-q")
    (mem / "MEMORY.md").write_text("- [a](a.md)\n- [old](old.md)\n", encoding="utf-8")
    (mem / "a.md").write_text("a\n", encoding="utf-8")
    (mem / "old.md").write_text("old\n", encoding="utf-8")
    (mem / "log.md").write_text("2026-01-01 | earlier | 0 creates, 0 updates, 0 deletes, 0 cases\n", encoding="utf-8")
    (mem / "other.md").write_text("other session\n", encoding="utf-8")
    git(mem, "add", "-A")
    git(mem, "commit", "-q", "-m", "base")
    head0 = git(mem, "rev-parse", "HEAD")
    inp = base / "close.json"
    inp.write_text(json.dumps({"topic": "lint and commit test", "creates": 1, "updates": 1, "deletes": 1,
                               "retrieval": [{"query": "q", "expected": "new"}], "cases": [{}, {}]}), encoding="utf-8")

    # another session's work: a staged edit and an untracked file, neither named by this run
    (mem / "other.md").write_text("other session, edited\n", encoding="utf-8")
    git(mem, "add", "other.md")
    (mem / "stray.md").write_text("stray\n", encoding="utf-8")
    # this run's work
    (mem / "new.md").write_text("new\n", encoding="utf-8")
    (mem / "a.md").write_text("a changed\n", encoding="utf-8")
    (mem / "old.md").unlink()
    with open(mem / "log.md", "a", encoding="utf-8") as f:
        f.write("2026-11-25 | lint and commit test | 1 creates, 1 updates, 1 deletes, 1 cases\n")

    # refusals: nothing staged, exit 2
    for bad in (["."], [".."], ["-A"], ["*.md"], [str(mem / "a.md")], ["../outside.md"], [], ["a.md", "."], [".git/config"]):
        rc, out, err = run("--mem", str(mem), "--input", str(inp), "--", *bad)
        assert rc == 2 and "nothing staged" in err and not out, (bad, rc, out, err)
    (mem / "dir").mkdir()
    rc, out, err = run("--mem", str(mem), "--input", str(inp), "--", "dir")
    assert rc == 2, err
    rc, out, err = run("--mem", str(mem), "--input", str(mem / "x.json"), "--", "a.md")
    assert rc == 2
    (mem / "in.json").write_text(inp.read_text(encoding="utf-8"), encoding="utf-8")
    rc, out, err = run("--mem", str(mem), "--input", str(mem / "in.json"), "--", "a.md")
    assert rc == 2 and "outside the memory folder" in err, err
    (mem / "in.json").unlink()
    (mem / "dir").rmdir()
    assert git(mem, "rev-parse", "HEAD") == head0 and "a.md" not in git(mem, "diff", "--cached", "--name-only")

    # the commit
    rc, out, err = run("--mem", str(mem), "--input", str(inp), "--date", "2026-11-25", "--",
                       "new.md", "a.md", "old.md", "log.md", "MEMORY.md")
    assert rc == 0, (out, err)
    L = out.splitlines()
    h = git(mem, "rev-parse", "--short", "HEAD")
    assert h != head0[:7] and L[0] == "KM close-out complete.", out
    assert L[1] == "Written: created new.md; updated a.md, log.md; deleted old.md", L[1]
    assert L[2] == "Cases: 1 | Retrieval queries: 1 | MEMORY.md: 2 lines", L[2]  # cases from the log line, not the input
    assert L[3] == f"Committed: {h}" and L[4] == "Pushed: no" and L[5] == f"commit: {h}", out
    assert git(mem, "log", "-1", "--format=%s") == "chore(km): KM close-out 2026-11-25 — lint and commit test"
    assert sorted(git(mem, "show", "--name-only", "--format=", "HEAD").split()) == ["a.md", "log.md", "new.md", "old.md"]
    # other sessions' work is untouched: still staged / untracked, not in the commit
    assert git(mem, "diff", "--cached", "--name-only") == "other.md"
    assert "stray.md" in git(mem, "status", "--porcelain")

    # nothing to commit
    rc, out, err = run("--mem", str(mem), "--input", str(inp), "--", "a.md")
    assert rc == 0 and "Committed: skipped (nothing to commit)" in out and out.splitlines()[-1] == "commit: null", out

    # a git failure is visible and exits 1
    (mem / "a.md").write_text("again\n", encoding="utf-8")
    hook = mem / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\necho blocked >&2\nexit 1\n", encoding="utf-8")
    rc, out, err = run("--mem", str(mem), "--input", str(inp), "--", "a.md")
    assert rc == 1 and "Committed: FAILED: git commit:" in out and out.splitlines()[-1] == "commit: null", (rc, out)
    hook.unlink()

    # not a git repo
    plain = base / "plain"
    plain.mkdir()
    (plain / "a.md").write_text("x\n", encoding="utf-8")
    ceil = dict(os.environ, GIT_CEILING_DIRECTORIES=str(base))  # a temp dir may sit inside some other repo
    rc, out, err = run("--mem", str(plain), "--input", str(inp), "--", "a.md", env=ceil)
    assert rc == 0 and "Committed: skipped (not a git repo)" in out and "commit: null" in out, out

    # the script never pushes
    assert '"push"' not in Path(script).read_text(encoding="utf-8")
print("ok: km_commit")
