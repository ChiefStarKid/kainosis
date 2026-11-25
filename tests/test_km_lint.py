"""Run: python -X utf8 -I tests/test_km_lint.py
km_lint.py: report-only mechanical checks (Behaviours D, E, G, H). Synthetic memory in a temp dir."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

script = str(Path(__file__).resolve().parent.parent / "scripts" / "km_lint.py")

GOOD = """---
name: feedback_good
description: Short status updates; read before drafting any progress message
metadata:
  node_type: memory
  type: feedback
  basis: preference
---

Lead with the rule.

**Trigger:** drafting a status update.
**Why:** the owner skims.
**How to apply:** three lines max.
**Related:** [[project_hub]]
"""
BAD = """---
name: other_name
description: wrong_name
metadata:
  type: feedback
---

Confirmed again today.
See `/nonexistent_dir_km/lint/file.txt` and [[ghost_slug]]; `[[placeholder]]` is fine.
Run `/compact` later. Status unverified 2020-01-01 and unverified.
"""
HUB = """---
name: project_hub
description: Hub for the lint test
metadata:
  node_type: memory
  type: project
  supersedes_note: x
---

**Cluster:** [[feedback_good]]
**Trigger:** t
**Why:** w
**How to apply:** h
"""


def run(*a):
    p = subprocess.run([sys.executable, "-X", "utf8", "-I", script, *a], capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


with tempfile.TemporaryDirectory() as t:
    mem = Path(t)
    (mem / "feedback_good.md").write_text(GOOD, encoding="utf-8")
    (mem / "project_hub.md").write_text(HUB, encoding="utf-8")
    (mem / "wrong_name.md").write_text(BAD, encoding="utf-8")
    (mem / "MEMORY.md").write_text("- [x](feedback_good.md)\n", encoding="utf-8")
    (mem / "sub").mkdir()
    (mem / "sub" / "ignored.md").write_text("no frontmatter", encoding="utf-8")
    before = {p.name: p.read_bytes() for p in mem.glob("*.md")}

    rc, out, err = run("--mem", str(mem), "--today", "2026-11-25")
    assert rc == 0, (rc, err)
    assert out.splitlines()[-1].startswith("km_lint: "), out
    assert "feedback_good:" not in out and "project_hub:" not in out, out  # clean files, no findings
    for needle in ("wrong_name: frontmatter: name is", "wrong_name: description: just the slug",
                   "wrong_name: frontmatter: metadata.node_type", "missing-why", "missing-how", "missing-trigger",
                   "missing-basis", "no-link-line", "tally", "dead-link: [[ghost_slug]]",
                   "stale-path: /nonexistent_dir_km/lint/file.txt", "unverified 2020-01-01 is",
                   "`unverified` without a YYYY-MM-DD date"):
        assert needle in out, (needle, out)
    assert "placeholder" not in out and "/compact" not in out, out  # code-span placeholders, slash commands
    assert "ignored" not in out
    # slug list limits the check; a missing slug is reported
    rc, out, _ = run("--mem", str(mem), "feedback_good", "nope", "--today", "2026-11-25")
    assert rc == 0 and "nope: missing-file" in out and "wrong_name" not in out, out
    # a fresh stamp is not stale
    (mem / "feedback_good.md").write_text(GOOD + "Claim unverified 2026-11-20.\n", encoding="utf-8")
    rc, out, _ = run("--mem", str(mem), "feedback_good", "--today", "2026-11-25")
    assert "feedback_good:" not in out, out
    # json mode
    rc, out, _ = run("--mem", str(mem), "wrong_name", "--json", "--today", "2026-11-25")
    d = json.loads(out)
    assert d["checked"] == 1 and any(f["check"] == "tally" for f in d["findings"]), d
    # nothing was written
    assert {p.name: p.read_bytes() for p in mem.glob("*.md") if p.name != "feedback_good.md"} == \
        {k: v for k, v in before.items() if k != "feedback_good.md"}
    # bad arguments
    rc, out, err = run("--mem", str(mem / "absent"))
    assert rc == 2 and "not found" in err
    rc, out, err = run("--mem", "")
    assert rc == 2
print("ok: km_lint")
