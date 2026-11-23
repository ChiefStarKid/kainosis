"""Propose (and, only on the owner's yes, apply) a theme-hub restructure of an
oversized MEMORY.md. Used by km-audit Step 4 ("restructure index into theme hubs").
Stdlib only. Reachability is km_graph_check.analyse() itself, not a copy.

Commands (all read-only except `apply`):
  propose --mem M --out D [--max-hubs 4] [--min-group 3]
      Groups M's feedback index lines into theme hubs (by slug, title and description words). Writes a CANDIDATE memory
      (top-level *.md of M + new MEMORY.md + hub files) into the empty/new folder
      D, never into M. Prints a JSON report: bytes before/after, groups, queries,
      replay. Exit 0 = replay passes, 1 = replay blocks the change.
  replay --mem M --candidate D [--hops 2]
      Re-checks any candidate folder against M (also for hand-made candidates).
      Blocks on: a query that passed before and fails after (expected slug not
      reachable from MEMORY.md within --hops), a one-line description that is
      missing or altered, a slug that lost its index/hub line. Exit 1 = blocked.
  apply --mem M --candidate D --owner-approved
      Copies the candidate MEMORY.md and new hub files into M. Refuses without
      --owner-approved (pass it only after the owner said yes) and re-runs replay
      first; refuses if replay blocks.

Queries: one per affected slug, built from its own title and description
(deterministic stand-in; km-audit may reword them, and appends them to
eval/retrieval.jsonl with session "audit:<date>"). An existing retrieval.jsonl
query for the slug is reused instead. The script only checks reachability; the
LLM retrieval replay in evals.md §Retrieval replay still runs on the same queries.
"""
import argparse
import json
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import km_graph_check as g  # noqa: E402

LINE = re.compile(r"^- \[(?P<title>[^\]]+)\]\((?P<file>[^)\s]+?\.md)\)(?P<rest>.*)$")
STOP = {"feedback", "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with", "before",
        "after", "when", "not", "no", "never", "always", "is", "are", "by", "from", "at", "as", "use"}
HUB_PREFIX = "index_feedback_"


def words(slug):
    return [w for w in re.split(r"[_\W]+", slug.removeprefix("feedback_").lower()) if w and w not in STOP]


def read_index(mem):
    return (mem / "MEMORY.md").read_text(encoding="utf-8")


def feedback_lines(mem):
    """[(line_no, raw_line, slug, title, rest)] for index lines naming a feedback file."""
    out = []
    for n, raw in enumerate(read_index(mem).splitlines()):
        m = LINE.match(raw)
        if not m:
            continue
        slug = Path(m["file"]).stem
        p = mem / f"{slug}.md"
        fb = slug.startswith("feedback_")
        if not fb and p.exists():
            fb = g.frontmatter(p.read_text(encoding="utf-8", errors="replace")).get("type") == "feedback"
        if fb:
            out.append((n, raw, slug, m["title"], m["rest"]))
    return out


def tokens(it):
    """Slug words plus title/description words (>= 4 letters), so slugs that share no word can still group."""
    extra = {w for w in re.findall(r"[a-z]{4,}", f"{it[3]} {it[4]}".lower()) if w not in STOP}
    return set(words(it[2])) | extra


def group(items, max_hubs, min_group):
    """Greedy: the word shared by most unassigned lines (>= min_group) names a hub. Words present
    in over half of all lines are too generic to be a theme; slug words win ties."""
    generic = {w for w, n in Counter(w for it in items for w in tokens(it)).items() if n > len(items) / 2}
    toks = {it[2]: tokens(it) - generic for it in items}
    left, groups = list(items), []
    while left and len(groups) < max_hubs - 1:
        freq = Counter(w for it in left for w in toks[it[2]])
        slugw = {w for it in left for w in words(it[2])}
        if not freq:
            break
        word, n = max(sorted(freq.items()), key=lambda kv: (kv[1], kv[0] in slugw))
        if n < min_group:
            break
        groups.append((word, [it for it in left if word in toks[it[2]]]))
        left = [it for it in left if word not in toks[it[2]]]
    if left:  # remainder is the last hub, so no line is left in MEMORY.md
        groups.append(("other", left))
    return groups


def hub_text(theme, members):
    terms = [w for w, _ in Counter(w for it in members for w in words(it[2])).most_common(6)]
    slug = HUB_PREFIX + theme
    desc = f"Behaviour rules grouped by theme '{theme}' ({len(members)}); terms: {', '.join(terms)}"
    body = [f"---\nname: {slug}\ndescription: \"{desc}\"\nmetadata:\n  node_type: memory\n  type: reference\n---",
            "**Members:** " + " · ".join(f"[[{it[2]}]]" for it in members), ""]
    body += [it[1] for it in members]  # the original one-line entries, byte-identical
    return slug, desc, "\n".join(body) + "\n"


def build_candidate(mem, out, groups):
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        sys.exit(f"--out must be empty: {out}")
    for p in mem.glob("*.md"):
        if p.name != "MEMORY.md":
            shutil.copy2(p, out / p.name)
    moved = {it[0] for _, ms in groups for it in ms}
    hub_lines = {}
    for theme, ms in groups:
        slug, desc, text = hub_text(theme, ms)
        (out / f"{slug}.md").write_text(text, encoding="utf-8")
        hub_lines[slug] = f"- **Feedback: {theme}** → [{slug}.md]({slug}.md) — {len(ms)} rules; open when deciding how to act on: {desc.split('terms: ')[1]}"
    lines, placed = [], False
    for n, raw in enumerate(read_index(mem).splitlines()):
        if n in moved:
            if not placed:
                lines += list(hub_lines.values())
                placed = True
            continue
        lines.append(raw)
    (out / "MEMORY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def queries_for(mem, items):
    existing = {}
    rp = mem / "eval" / "retrieval.jsonl"
    if rp.exists():
        for ln in rp.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(ln)
                existing.setdefault(r["expected"], r["query"])
            except (ValueError, KeyError):
                pass
    qs = []
    for _, _, slug, title, rest in items:
        desc = rest.lstrip(" —-").strip()
        q = existing.get(slug) or f"what is my rule about: {title.lower()}" + (f" ({desc})" if desc else "")
        qs.append({"query": q, "expected": slug, "source": "retrieval.jsonl" if slug in existing else "generated"})
    return qs


def reach_map(mem, hops):
    r = g.analyse(mem, [], [])
    return {s: (rt is not None and rt["hops_from_index"] <= hops) for s, rt in r["route"].items()}, r


def replay(mem, cand, hops=2):
    items = feedback_lines(mem)
    queries = queries_for(mem, items)
    before, rb = reach_map(mem, hops)
    after, ra = reach_map(cand, hops)
    results = []
    for q in queries:
        b, a = before.get(q["expected"], False), after.get(q["expected"], False)
        results.append({**q, "before": "pass" if b else "fail", "after": "pass" if a else "fail"})
    blocked = [r for r in results if r["before"] == "pass" and r["after"] == "fail"]
    # one-line descriptions must survive verbatim somewhere in the candidate
    cand_text = "\n".join(p.read_text(encoding="utf-8") for p in cand.glob("*.md"))
    cand_lines = set(cand_text.splitlines())
    lost_desc = [it[2] for it in items if it[1] not in cand_lines]
    new_unreach = sorted(set(ra["unreachable"]) - set(rb["unreachable"]))
    ok = not blocked and not lost_desc and not new_unreach
    return {
        "ok": ok, "hops_budget": hops,
        "bytes_before": rb["memory_md_bytes"], "bytes_after": ra["memory_md_bytes"],
        "bytes_saved": rb["memory_md_bytes"] - ra["memory_md_bytes"],
        "queries": len(results), "pass_to_fail": [r["expected"] for r in blocked],
        "descriptions_lost": lost_desc, "newly_unreachable": new_unreach,
        "new_dead_links": sorted(set(ra["dead_links"]) - set(rb["dead_links"])),
        "results": results,
    }


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("propose", "replay", "apply"):
        p = sub.add_parser(name)
        p.add_argument("--mem", type=Path, required=True)
        p.add_argument("--hops", type=int, default=2)
        if name == "propose":
            p.add_argument("--out", type=Path, required=True)
            p.add_argument("--max-hubs", type=int, default=4)
            p.add_argument("--min-group", type=int, default=3)
        else:
            p.add_argument("--candidate", type=Path, required=True)
        if name == "apply":
            p.add_argument("--owner-approved", action="store_true")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if a.cmd == "propose":
        items = feedback_lines(a.mem)
        if not items:
            sys.exit("no feedback index lines to restructure")
        groups = group(items, a.max_hubs, a.min_group)
        build_candidate(a.mem, a.out, groups)
        rep = replay(a.mem, a.out, a.hops)
        rep["groups"] = {t: len(ms) for t, ms in groups}
        rep["candidate"] = str(a.out)
        print(json.dumps(rep, indent=1))
        sys.exit(0 if rep["ok"] else 1)
    rep = replay(a.mem, a.candidate, a.hops)
    if a.cmd == "replay":
        print(json.dumps(rep, indent=1))
        sys.exit(0 if rep["ok"] else 1)
    if not a.owner_approved:
        sys.exit("refused: apply writes only after the owner's yes (--owner-approved)")
    if not rep["ok"]:
        print(json.dumps({k: rep[k] for k in ("pass_to_fail", "descriptions_lost", "newly_unreachable")}))
        sys.exit("refused: replay blocks this change")
    for p in a.candidate.glob("*.md"):
        if p.name == "MEMORY.md" or not (a.mem / p.name).exists():
            shutil.copy2(p, a.mem / p.name)
    print(f"applied: MEMORY.md {rep['bytes_before']} -> {rep['bytes_after']} bytes")


if __name__ == "__main__":
    main()
