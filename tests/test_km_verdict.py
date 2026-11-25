"""Run: python tests/test_km_verdict.py"""
import copy
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root.parent / "scripts"))
from km_verdict_check import verdict  # noqa: E402

fx = root / "fixtures" / "verdict"


MARKER = re.search(r"Full-load marker: `([^`]+)`", (root.parent / "docs" / "km-full.md").read_text(encoding="utf-8")).group(1)


def load(name):
    d = json.loads((fx / name).read_text(encoding="utf-8"))
    if d.get("mode", "full") != "lean":
        d["full_loaded_marker"] = MARKER
    return d


# 1. unverified claim -> NOT SAFE; verifying it -> SAFE
v = verdict(load("unverified_merge.json"))
assert v.startswith("NOT SAFE") and "candidate 2" in v and "unverified" in v, v
good = load("verified_merge.json")
assert verdict(good) == "SAFE"


# 2. each other blocker flips SAFE to NOT SAFE
def broken(f):
    d = copy.deepcopy(good)
    f(d)
    return verdict(d)


assert broken(lambda d: d.pop("reverse_sweep")).startswith("NOT SAFE")
assert broken(lambda d: d["reverse_sweep"].update(unreconciled=["x"])).startswith("NOT SAFE")
assert broken(lambda d: d["loose_ends"].append({"item": "unsent draft", "status": "open"})).startswith("NOT SAFE")
assert broken(lambda d: d["carry_over"].append({"item": "id 42", "where": None})).startswith("NOT SAFE")
assert broken(lambda d: d["candidates"][2].update(where=None)).startswith("NOT SAFE")
# owner acceptance clears a blocker
assert broken(lambda d: d["loose_ends"].append({"item": "scratch", "status": "open", "accepted": True})) == "SAFE"

# 3. lean never says SAFE
lean = copy.deepcopy(good)
lean["mode"] = "lean"
lean.pop("full_loaded_marker")  # lean needs no marker
assert verdict(lean).startswith("SAFE TO COMPACT")
lean["candidates"][1]["verified"] = False
assert verdict(lean).startswith("NOT SAFE TO COMPACT")

# 4. zero candidates: verified sweep -> SAFE; sweep missing -> NOT SAFE
zero = {"mode": "verdict-only", "candidates": [], "reverse_sweep": {"ran": True}, "loose_ends": [], "carry_over": [],
        "full_loaded_marker": MARKER}
assert verdict(zero) == "SAFE"
zero["reverse_sweep"] = {"ran": False}
assert verdict(zero).startswith("NOT SAFE")

# 5. the full-load marker: missing or wrong -> NOT SAFE; lean needs none
assert broken(lambda d: d.pop("full_loaded_marker")).startswith("NOT SAFE") and "not read" in broken(lambda d: d.pop("full_loaded_marker"))
w = broken(lambda d: d.update(full_loaded_marker="km-full-v0-old"))
assert w.startswith("NOT SAFE") and "wrong" in w, w
z = dict(zero)
z.pop("full_loaded_marker")
assert verdict(z).startswith("NOT SAFE")

# 6. file-backed claims, checked against a real (temporary) memory repo
def git(mem, *a):
    subprocess.run(["git", "-C", str(mem), *a], check=True, capture_output=True)


with tempfile.TemporaryDirectory() as tmp:
    mem = Path(tmp) / "mem"
    mem.mkdir()
    git(mem, "init", "-q")
    git(mem, "config", "user.email", "t@example.invalid")
    git(mem, "config", "user.name", "t")
    for n in ("feedback_confirm_bulk_delete.md", "feedback_reply_all.md"):
        (mem / n).write_text("x", encoding="utf-8")
    git(mem, "add", ".")
    git(mem, "commit", "-q", "-m", "m")
    head = subprocess.run(["git", "-C", str(mem), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()

    def backed(f=lambda d: None):
        d = copy.deepcopy(good)
        d["candidates"][0]["file"] = "feedback_confirm_bulk_delete.md"
        d["candidates"][1]["file"] = "feedback_reply_all.md"
        d["commit"] = head
        d["written_paths"] = ["feedback_confirm_bulk_delete.md", "feedback_reply_all.md"]
        f(d)
        un = []
        return verdict(d, mem, un), un

    v, un = backed()
    assert v == "SAFE", v
    assert any("deferred home" in u for u in un) and any("no --mem" not in u for u in un)  # model-verified list
    # the same ledger without --mem: allowed, but the file claims are listed as model-verified
    un2 = []
    d0 = copy.deepcopy(good)
    assert verdict(d0, None, un2) == "SAFE" and any("no --mem" in u for u in un2)
    # a written row with no `file` is model-verified only
    v, un = backed(lambda d: d["candidates"][0].pop("file"))
    assert v == "SAFE" and any("candidate 1" in u and "no `file`" in u for u in un), (v, un)
    # missing where-file
    v, _ = backed(lambda d: d["candidates"][0].update(file="feedback_gone.md"))
    assert v.startswith("NOT SAFE") and "feedback_gone.md" in v, v
    # path traversal out of the memory folder is not a pass
    v, _ = backed(lambda d: d["candidates"][0].update(file="../mem/feedback_reply_all.md"))
    assert v == "SAFE"  # resolves inside mem
    v, _ = backed(lambda d: d["candidates"][0].update(file="../../etc/passwd"))
    assert v.startswith("NOT SAFE")
    # missing commit hash
    v, _ = backed(lambda d: d.update(commit="0123456789abcdef0123456789abcdef01234567"))
    assert v.startswith("NOT SAFE") and "does not exist" in v, v
    v, _ = backed(lambda d: d.update(commit="not-a-hash; rm -rf"))
    assert v.startswith("NOT SAFE"), v
    # written but never committed
    v, _ = backed(lambda d: d.update(commit=None))
    assert v.startswith("NOT SAFE") and "no commit" in v, v
    (mem / "feedback_new.md").write_text("y", encoding="utf-8")
    v, _ = backed(lambda d: d["written_paths"].append("feedback_new.md"))
    assert v.startswith("NOT SAFE") and "feedback_new.md is not committed" in v, v
    (mem / "feedback_reply_all.md").write_text("changed", encoding="utf-8")
    v, _ = backed()
    assert v.startswith("NOT SAFE") and "uncommitted changes" in v, v
    # lean mode with file claims checked too
    lean2 = copy.deepcopy(lean)
    lean2["candidates"][0]["file"] = "feedback_gone.md"
    assert verdict(lean2, mem).startswith("NOT SAFE TO COMPACT")

# 7. command line: reads a ledger file, prints verdict then the model-verified list
script = str(root.parent / "scripts" / "km_verdict_check.py")
with tempfile.TemporaryDirectory() as tmp:
    f = Path(tmp) / "ledger.json"
    f.write_text(json.dumps(good), encoding="utf-8")
    r = subprocess.run([sys.executable, "-I", script, str(f)], capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout.splitlines()[0] == "SAFE" and "Model-verified" in r.stdout, r
    f.write_text("{not json", encoding="utf-8")
    r = subprocess.run([sys.executable, "-I", script, str(f)], capture_output=True, text=True)
    assert r.returncode == 2, r
print("ok: km_verdict tests passed")
