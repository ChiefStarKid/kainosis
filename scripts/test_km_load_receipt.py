"""Run: python scripts/test_km_load_receipt.py"""
import json
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
fx = root / "scripts" / "fixtures" / "load_receipt"
out = subprocess.run(
    [sys.executable, "-X", "utf8", "-I", str(root / "scripts" / "km_load_receipt.py"),
     "--mem", str(root / "examples" / "graph"), "--json",
     *(str(fx / f"{n}.jsonl") for n in ("whole", "truncated", "truncated_old", "absent"))],
    capture_output=True, text=True, check=True).stdout
rs = {r["session"]: r for r in json.loads(out)}
got = {k: (r["status"], r["stale_index"]) for k, r in rs.items()}
assert got == {"whole": ("whole", False), "truncated": ("truncated", False),
               "truncated_old": ("truncated", True), "absent": ("absent", False)}, got
print("ok", got)
