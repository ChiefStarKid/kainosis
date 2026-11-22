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
     *(str(fx / f"{n}.jsonl") for n in ("whole", "truncated", "absent"))],
    capture_output=True, text=True, check=True).stdout
got = {r["session"]: r["status"] for r in json.loads(out)}
assert got == {"whole": "whole", "truncated": "truncated", "absent": "absent"}, got
print("ok", got)
