"""Read-only graph-health summary for the memory wiki.

Shared by the km skill (Step 2, Behaviours C/F/H) and km-audit
(scripted triage, MEMORY.md compaction, scorecard bytes_always). Owned by
km; change the output format in both skills together. Stdlib only.
Never writes.

Memory dir: --mem <dir>, else the CLAUDE_PLUGIN_OPTION_MEMORY_PATH or
KM_MEMORY_PATH environment variable.

A `supersedes:` target with no file is reported as a dead link.
Scans top-level *.md only. Excluded from every check: MEMORY.md, log.md and
all subdirectories (eval/, dormant/, ...). [[ ]] inside code spans are
placeholders, not links.

Usage:
  python km_graph_check.py                            # ~1 KB human summary
  python km_graph_check.py --json                     # full machine-readable output
  python km_graph_check.py --reachable a b            # reachable from MEMORY.md? (Behaviour H)
  python km_graph_check.py --reachable-excluding-self a b
        # still reachable if the slug's own MEMORY.md line were removed? (compaction)
  python km_graph_check.py --list                     # human summary without truncation
  python km_graph_check.py --mem <dir>                # memory dir (else env, see above)

--json also emits `route` (every file) and `route_excluding_self` (the
--reachable-excluding-self slugs, own index lines removed):
  {"hops_from_index": n, "path_bytes": b, "via": [slugs]} or null.
hops = BFS minimum from MEMORY.md; path_bytes/via = cheapest route by bytes of
the files opened before arriving (MEMORY.md and the target itself excluded).
"""
import argparse
import heapq
import json
import os
import re
import sys
from collections import deque
from pathlib import Path

SKIP = {"MEMORY.md", "log.md"}
WIKILINK = re.compile(r"\[\[([^\]|#]+?)\]\]")
MDLINK = re.compile(r"\]\(([^)\s]+?\.md)\)")
CODE = re.compile(r"```.*?```|`[^`\n]*`", re.S)  # placeholders like `[[name]]` are not links
CAP = 12


def default_mem():
    for var in ("CLAUDE_PLUGIN_OPTION_MEMORY_PATH", "KM_MEMORY_PATH"):
        if os.environ.get(var):
            return Path(os.environ[var])
    sys.exit("No memory dir: pass --mem <dir> or set KM_MEMORY_PATH")


def frontmatter(text):
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    fm = {}
    for line in text[3:end].splitlines():
        m = re.match(r"\s*(name|type|basis|supersedes):\s*(.*)", line)
        if m and m.group(1) not in fm:
            fm[m.group(1)] = m.group(2).strip().strip("\"'")
    return fm


def bfs(roots, edges):
    seen, q = set(roots), deque(roots)
    while q:
        for nxt in edges[q.popleft()]:
            if nxt not in seen:
                seen.add(nxt)
                q.append(nxt)
    return seen


def routes(roots, edges, size):
    # Per slug: min hops from the roots (BFS) and the cheapest route by bytes
    # opened before arriving (Dijkstra; roots cost 0, the target's own bytes excluded).
    hops = {s: 0 for s in roots}
    q = deque(roots)
    while q:
        cur = q.popleft()
        for nxt in edges[cur]:
            if nxt not in hops:
                hops[nxt] = hops[cur] + 1
                q.append(nxt)
    cost, prev = {s: 0 for s in roots}, {}
    heap = [(0, s) for s in sorted(roots)]
    while heap:
        c, cur = heapq.heappop(heap)
        if c > cost[cur]:
            continue
        for nxt in edges[cur]:
            nc = c + size[cur]
            if nc < cost.get(nxt, float("inf")):
                cost[nxt], prev[nxt] = nc, cur
                heapq.heappush(heap, (nc, nxt))

    def rec(slug):
        if slug not in hops:
            return None
        via, cur = [], slug
        while cur in prev:
            cur = prev[cur]
            via.append(cur)
        return {"hops_from_index": hops[slug], "path_bytes": cost[slug], "via": via[::-1]}
    return rec


def analyse(mem, reach, reach_ex):
    files = {p.stem: p for p in mem.glob("*.md") if p.name not in SKIP}
    texts = {s: p.read_text(encoding="utf-8", errors="replace") for s, p in files.items()}
    meta = {s: frontmatter(t) for s, t in texts.items()}
    edges, inbound, dead, total_wiki = {}, {s: 0 for s in files}, [], 0
    for s, text in texts.items():
        # supersedes: slug or [slug, slug]; a missing target is a dead link, not an edge.
        for t in re.split(r"[,\s\[\]]+", meta[s].get("supersedes", "")):
            if t and t.removesuffix(".md") not in files:
                dead.append(f"{s}->{t} (supersedes)")
        wiki = {t.strip() for t in WIKILINK.findall(CODE.sub("", text))} - {""}
        md = {Path(t).stem for t in MDLINK.findall(text)}
        total_wiki += len(wiki & files.keys())
        edges[s] = (wiki | md) & files.keys() - {s}
        for t in wiki:
            if t in files:
                if t != s:
                    inbound[t] += 1
            else:
                dead.append(f"{s}->{t}")

    index_path = mem / "MEMORY.md"
    index = index_path.read_text(encoding="utf-8", errors="replace") if index_path.exists() else ""
    index_lines, bytes_by_slug = [], {}
    for n, line in enumerate(index.splitlines(), 1):
        slugs = sorted({Path(t).stem for t in MDLINK.findall(line)} & files.keys())
        if not slugs:
            continue
        b = len(line.encode("utf-8")) + 1
        index_lines.append({"line": n, "bytes": b, "slugs": slugs})
        for s in slugs:
            # A slug can appear on several lines; keep every occurrence.
            bytes_by_slug.setdefault(s, []).append({"line": n, "bytes": b, "shared_with": len(slugs) - 1})
    indexed = {s for rec in index_lines for s in rec["slugs"]}
    reachable = bfs(indexed, edges)

    def reachable_excluding_self(slug):
        # Drop every MEMORY.md line naming the slug (its co-listed slugs go with it).
        roots = {s for rec in index_lines if slug not in rec["slugs"] for s in rec["slugs"]}
        return slug in bfs(roots, edges)

    size = {s: p.stat().st_size for s, p in files.items()}
    route = routes(indexed, edges, size)

    def route_excluding_self(slug):
        roots = {s for rec in index_lines if slug not in rec["slugs"] for s in rec["slugs"]}
        return routes(roots, edges, size)(slug)

    def state(slug, fn):
        slug = slug.removesuffix(".md")
        if slug not in files:
            return slug, "missing_file"
        return slug, "reachable" if fn(slug) else "unreachable"

    fb = sorted(s for s in files if meta[s].get("type") == "feedback" or s.startswith("feedback_"))
    return {
        "memory_dir": str(mem),
        "files": len(files),
        "feedback_files": len(fb),
        "memory_md_lines": len(index.splitlines()),
        "memory_md_bytes": len(index.encode("utf-8")),
        "indexed": len(indexed),
        "interlink_density": round(total_wiki / max(len(files), 1), 2),
        "islands": sorted(s for s, n in inbound.items() if n == 0),
        "unreachable": sorted(files.keys() - reachable),
        "dead_links": sorted(dead),
        "feedback_missing": {
            "why": [s for s in fb if "**Why:**" not in texts[s]],
            "trigger": [s for s in fb if "**Trigger:**" not in texts[s]],
            "basis": [s for s in fb if not meta[s].get("basis")],
        },
        "index_lines": index_lines,
        "bytes_by_slug": bytes_by_slug,
        "reachable": dict(state(s, lambda x: x in reachable) for s in reach),
        "reachable_excluding_self": dict(state(s, reachable_excluding_self) for s in reach_ex),
        # Added 2026-11-21 (audit D1); null = unreachable. JSON only.
        "route": {s: route(s) for s in sorted(files)},
        "route_excluding_self": {s.removesuffix(".md"): route_excluding_self(s.removesuffix(".md"))
                                 for s in reach_ex if s.removesuffix(".md") in files},
    }


def show(label, items, full):
    if not items:
        print(f"{label}: 0")
        return
    shown = items if full else items[:CAP]
    more = "" if full or len(items) <= CAP else f" (+{len(items) - CAP} more)"
    print(f"{label}: {len(items)} -- {', '.join(shown)}{more}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mem", type=Path)
    ap.add_argument("--reachable", nargs="*", default=[])
    ap.add_argument("--reachable-excluding-self", nargs="*", default=[])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    mem = a.mem or default_mem()
    if not mem.is_dir():
        sys.exit(f"Memory dir not found: {mem}")
    r = analyse(mem, a.reachable, a.reachable_excluding_self)

    if a.json:
        print(json.dumps(r, indent=1))
        return
    fm = r["feedback_missing"]
    print(f"memory dir: {r['memory_dir']}")
    print(f"files: {r['files']} (feedback {r['feedback_files']}) | MEMORY.md: {r['memory_md_lines']} lines, "
          f"{r['memory_md_bytes']} bytes | indexed: {r['indexed']}")
    print(f"interlink density: {r['interlink_density']:.2f} [[ ]] links/file (flag if < 1.0)")
    show("islands (0 inbound [[ ]])", r["islands"], a.list)
    show("unreachable from MEMORY.md", r["unreachable"], a.list)
    show("dead [[ ]] links", r["dead_links"], a.list)
    print(f"feedback missing Why: {len(fm['why'])} | Trigger: {len(fm['trigger'])} | basis: {len(fm['basis'])}")
    if a.list:
        show("  no Why", fm["why"], True)
        show("  no Trigger", fm["trigger"], True)
    for s, v in r["reachable"].items():
        print(f"reachable? {s}: {v}")
    for s, v in r["reachable_excluding_self"].items():
        print(f"reachable excluding own index line? {s}: {v}")


if __name__ == "__main__":
    main()
