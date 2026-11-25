"""Run: python tests/test_km_verdict.py"""
import copy
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root.parent / "scripts"))
from km_verdict_check import verdict  # noqa: E402

fx = root / "fixtures" / "verdict"


def load(name):
    return json.loads((fx / name).read_text(encoding="utf-8"))


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
assert verdict(lean).startswith("SAFE TO COMPACT")
lean["candidates"][1]["verified"] = False
assert verdict(lean).startswith("NOT SAFE TO COMPACT")

# 4. zero candidates: verified sweep -> SAFE; sweep missing -> NOT SAFE
zero = {"mode": "verdict-only", "candidates": [], "reverse_sweep": {"ran": True}, "loose_ends": [], "carry_over": []}
assert verdict(zero) == "SAFE"
zero["reverse_sweep"] = {"ran": False}
assert verdict(zero).startswith("NOT SAFE")
print("ok: km_verdict tests passed")
