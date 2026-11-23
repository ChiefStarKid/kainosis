"""Run: python scripts/test_km_index_restructure.py
Builds a synthetic oversized memory graph (fictional bakery, 120 feedback lines)
in a temp dir; nothing real is used."""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

script = str(Path(__file__).resolve().parent / "km_index_restructure.py")
THEMES = {
    "oven": ["preheat", "steam", "rack", "door", "timer", "tray"],
    "dough": ["proof", "hydration", "knead", "flour", "yeast", "fold"],
    "pricing": ["margin", "discount", "rounding", "tax", "bundle", "tip"],
    "supplier": ["invoice", "delivery", "butter", "sugar", "returns", "contract"],
}


def build(mem):
    mem.mkdir()
    lines = ["# Memory index", "", "## Wiki Hubs", "- **Bakery** → [project_bakery.md](project_bakery.md)", "",
             "## Feedback"]
    (mem / "project_bakery.md").write_text(
        "---\nname: project_bakery\ndescription: \"Bakery project\"\nmetadata:\n  type: project\n---\n"
        "**Cluster:** [[feedback_oven_preheat_0]]\n", encoding="utf-8")
    for theme, topics in THEMES.items():
        for i in range(30):
            slug = f"feedback_{theme}_{topics[i % 6]}_{i}"
            title = f"{theme.capitalize()} rule about {topics[i % 6]} number {i}"
            desc = f"always check {topics[i % 6]} detail {i} when handling {theme} work in the shop, and confirm it before the next batch goes out"
            (mem / f"{slug}.md").write_text(
                f"---\nname: {slug}\ndescription: \"{desc}\"\nmetadata:\n  type: feedback\n  basis: preference\n---\n"
                f"**Why:** synthetic.\n**Trigger:** {theme}.\n", encoding="utf-8")
            lines.append(f"- [{title}]({slug}.md) — {desc}")
    (mem / "MEMORY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    # one link so project_bakery is not an island and one feedback has a wikilink inbound
    return mem


def run(*args):
    p = subprocess.run([sys.executable, "-X", "utf8", "-I", script, *args], capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    mem = build(td / "mem")
    before = (mem / "MEMORY.md").read_bytes()

    # 1. good restructure: passes replay, cuts bytes, writes nothing into mem
    rc, out, err = run("propose", "--mem", str(mem), "--out", str(td / "cand"))
    rep = json.loads(out)
    assert rc == 0 and rep["ok"], (rc, err, out[:500])
    assert rep["queries"] == 120 and not rep["pass_to_fail"] and not rep["descriptions_lost"]
    assert rep["bytes_saved"] > 8000 and rep["bytes_before"] > 17000 > rep["bytes_after"], rep
    assert (mem / "MEMORY.md").read_bytes() == before, "propose must not write to mem"
    assert sorted(rep["groups"]) == ["dough", "oven", "pricing", "supplier"] or "other" in rep["groups"], rep["groups"]
    print(f"GOOD: ok, MEMORY.md {rep['bytes_before']} -> {rep['bytes_after']} bytes "
          f"(saved {rep['bytes_saved']}), {rep['queries']} queries, 0 pass->fail, groups {rep['groups']}")

    # 2. bad restructure: a hub silently drops one slug's line -> blocked
    bad = td / "bad"
    shutil.copytree(td / "cand", bad)
    hub = next(bad.glob("index_feedback_oven.md"))
    victim = "feedback_oven_steam_1"
    hub.write_text("\n".join(ln for ln in hub.read_text(encoding="utf-8").splitlines()
                             if f"({victim}.md)" not in ln).replace(f" · [[{victim}]]", ""), encoding="utf-8")
    rc, out, _ = run("replay", "--mem", str(mem), "--candidate", str(bad))
    rep = json.loads(out)
    assert rc == 1 and not rep["ok"] and rep["pass_to_fail"] == [victim], (rc, rep["pass_to_fail"])
    assert victim in rep["descriptions_lost"], rep["descriptions_lost"]
    print(f"BAD (dropped {victim}): BLOCKED, pass->fail {rep['pass_to_fail']}, descriptions lost {rep['descriptions_lost']}")

    # 3. altered description is blocked even though the slug stays reachable
    alt = td / "alt"
    shutil.copytree(td / "cand", alt)
    hub = alt / "index_feedback_dough.md"
    hub.write_text(hub.read_text(encoding="utf-8").replace("always check", "check", 1), encoding="utf-8")
    rc, out, _ = run("replay", "--mem", str(mem), "--candidate", str(alt))
    rep = json.loads(out)
    assert rc == 1 and len(rep["descriptions_lost"]) == 1 and not rep["pass_to_fail"], rep
    print(f"ALTERED description: BLOCKED, {rep['descriptions_lost']}")

    # 4. apply: refused without owner approval and for a blocked candidate; allowed for the good one
    rc, _, err = run("apply", "--mem", str(mem), "--candidate", str(td / "cand"))
    assert rc != 0 and "owner" in err and (mem / "MEMORY.md").read_bytes() == before
    rc, _, err = run("apply", "--mem", str(mem), "--candidate", str(bad), "--owner-approved")
    assert rc != 0 and "blocks" in err and (mem / "MEMORY.md").read_bytes() == before
    rc, out, err = run("apply", "--mem", str(mem), "--candidate", str(td / "cand"), "--owner-approved")
    assert rc == 0 and (mem / "MEMORY.md").stat().st_size < len(before), (err, out)
    print("APPLY: refused without --owner-approved, refused when blocked, applied for the good candidate:", out.strip())

    # 5. the applied graph is healthy per km_graph_check
    chk = subprocess.run([sys.executable, "-X", "utf8", "-I", str(Path(script).with_name("km_graph_check.py")),
                          "--mem", str(mem), "--json"], capture_output=True, text=True, check=True).stdout
    r = json.loads(chk)
    assert not r["unreachable"] and not r["dead_links"], (r["unreachable"][:3], r["dead_links"][:3])
    print("graph check after apply: 0 unreachable, 0 dead links")
print("ALL PASS")
