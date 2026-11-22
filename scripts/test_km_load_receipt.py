"""Run: python scripts/test_km_load_receipt.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parent.parent
fx = root / "scripts" / "fixtures" / "load_receipt"
mem = root / "examples" / "graph"
script = str(root / "scripts" / "km_load_receipt.py")


def run(*args):
    out = subprocess.run([sys.executable, "-X", "utf8", "-I", script, "--mem", str(mem), "--json", *args],
                         capture_output=True, text=True, check=True).stdout
    return {r["session"]: (r["status"], r["stale_index"]) for r in json.loads(out)}


# 1. no history: whole / truncated (cut, index unchanged) / absent / unknown (stale, no history)
got = run(*(str(fx / f"{n}.jsonl") for n in ("whole", "truncated", "unknown", "absent")))
assert got == {"whole": ("whole", False), "truncated": ("truncated", False),
               "unknown": ("unknown", True), "absent": ("absent", False)}, got

# 2. history: a temp git repo holds an older index (last hub line is the old final line)
cur = (mem / "MEMORY.md").read_text(encoding="utf-8")
old = cur.split("\n## User Profile")[0].rstrip() + "\n"
with tempfile.TemporaryDirectory() as td:
    repo = Path(td) / "mem"
    repo.mkdir()
    env = {**os.environ, "GIT_AUTHOR_DATE": "2020-01-01T00:00:00Z", "GIT_COMMITTER_DATE": "2020-01-01T00:00:00Z"}
    git = lambda *a: subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.invalid", *a],
                                    env=env, check=True, capture_output=True)
    git("init", "-q")
    (repo / "MEMORY.md").write_text(old, encoding="utf-8")
    git("add", "MEMORY.md")
    git("commit", "-q", "-m", "old index")

    def transcript(name, index, ts="2020-06-01T00:00:00Z"):
        p = Path(td) / f"{name}.jsonl"
        p.write_text(json.dumps({"type": "attachment", "attachment": {"type": "instructions", "files": [
            {"path": "MEMORY.md", "type": "AutoMem", "content": index}]}, "timestamp": ts}) + "\n", encoding="utf-8")
        return str(p)

    cut = old.rstrip().rsplit("\n", 1)[0]  # drop the old index's final line: a real cut
    got = run(transcript("stale_whole", old), transcript("stale_truncated", cut),
              "--history", str(repo), "--index-path", "MEMORY.md")
    assert got == {"stale_whole": ("whole", True), "stale_truncated": ("truncated", True)}, got
    # same stale session without history is unknown, not truncated
    assert run(transcript("stale_whole", old)) == {"stale_whole": ("unknown", True)}
    # session older than any index commit: no history to compare, unknown
    assert run(transcript("too_old", old, "2019-01-01T00:00:00Z"), "--history", str(repo),
               "--index-path", "MEMORY.md") == {"too_old": ("unknown", True)}
print("ok")
