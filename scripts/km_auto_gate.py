"""Confidence gates for automatic memory edits (issue #23, first slice).

Takes a list of proposed edits to the memory folder and decides, for each one,
APPLY or HOLD. Anything that fails a gate, or that the gates cannot judge, is
HELD for the owner. Stdlib only; imports km_graph_check from this folder.
Never runs git, never pushes, never uses the network.

Not wired into `km` yet: this is the gate and the digest, run by hand.

Commands:
  gate   --mem DIR --edits FILE [--approve ID ...]
         Read-only. Prints the decision for every edit as JSON. Writes nothing.
  apply  --mem DIR --edits FILE --opt-in [--approve ID ...] [--run-id R]
         Writes only the APPLY edits into the memory folder and a run folder
         eval/auto_runs/<run>/ (manifest.json, digest.md, held.json). Refuses
         without --opt-in.
  revert --mem DIR --run R --edit ID
         Undoes one applied edit. Refuses unless the text it added is still
         there exactly once (a created file: unless its bytes are unchanged).

Edit file: a JSON list of
  {"id", "kind", "file", "recommended", "source", ...kind fields}
  kind create       content            new file; name == file stem, description present, no supersedes
  kind append       text               added at the end; existing bytes untouched
  kind insert_line  after, text        after an anchor line that occurs once; lines are
                                       "**How to apply:**..." or "**Precedent(s):**..."
  kind fix_fact     old, new, verify   one-line replacement outside frontmatter, backed by a
                                       read-only check: {"type": "path_exists", "value": P} or
                                       {"type": "file_contains", "file": F, "value": V};
                                       the value must appear in `new`
  source            owner | owner_paraphrase | verified_check (fix_fact only).
                    Anything else (for example text read from a tool result) is held.
  file              a top-level *.md file, or eval/retrieval.jsonl (append only).

Gates (all edits are checked one after another against a temporary copy, so
edits to the same file stack):
  kind          only the four kinds above; delete, move, rewrite, supersede are held
  reachability  a stored retrieval query whose expected file was within 2 hops of
                MEMORY.md must still be; no existing file becomes unreachable; no new
                dead link; no link removed. With no stored queries, insert_line and
                fix_fact are held (they cannot be checked).
  protected     MEMORY.md is never edited; the frontmatter block of an existing file
                stays byte-identical
  never automatic  rule files touching sending, deleting or publishing; added text that
                weakens a rule; a source other than the owner's words; edits over
                1,500 characters
  recommended   an edit not marked recommended is held and listed as an option

--approve ID (the owner's yes to a held edit) skips the gates but never the structural
checks: the path stays inside the memory folder, an anchor or old text must be found
exactly once, a file to edit must exist and a file to create must not. Approved edits
are recorded as such in the digest.

Line endings: text is handled as LF and written back in the file's own line ending.
A file with mixed line endings is held.
"""
import argparse
import hashlib
import json
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import km_graph_check as kg  # noqa: E402

MAX_CHARS = 1500
OWNER_SOURCES = {"owner", "owner_paraphrase"}
KINDS = {"create", "append", "insert_line", "fix_fact"}
NEVER_KINDS = {"delete", "move", "rewrite", "supersede", "retire", "rename"}
RETRIEVAL = "eval/retrieval.jsonl"
FILE_RE = re.compile(r"^[A-Za-z0-9_.-]+\.md$")
SENDING = re.compile(
    r"\b(send|sending|sent|email|e-mail|reply|forward|delete|deleting|remove|publish|publishing|"
    r"post|posting|push|pushing|deploy|merge|release|overwrite|overwriting|draft|drafts)\b", re.I)
WEAKENING = re.compile(
    r"\b(no longer|ignore|skip|unless|except|optional|bypass|disable|relax|without asking|"
    r"don'?t need to|do not need to|not required|not necessary|may skip|stop (?:checking|asking))\b", re.I)
HOW_TO = re.compile(r"^\*\*How to apply:\*\*")
PRECEDENT = re.compile(r"^\*\*Precedents?:\*\*")


class Hold(Exception):
    def __init__(self, category, *reasons):
        super().__init__(category)
        self.category, self.reasons = category, list(reasons)


def die(msg, code=2):
    print(msg, file=sys.stderr)
    sys.exit(code)


# ---- file helpers -------------------------------------------------------

def read_lf(path):
    raw = path.read_bytes()
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError:
        raise Hold("invalid", f"{path.name} is not UTF-8")
    crlf, lf = raw.count(b"\r\n"), raw.count(b"\n")
    if crlf and crlf != lf:
        raise Hold("invalid", f"{path.name} has mixed line endings")
    return raw.decode("utf-8").replace("\r\n", "\n"), ("\r\n" if crlf else "\n")


def write_eol(path, text_lf, eol):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text_lf.replace("\n", eol).encode("utf-8"))


def fm_block(text):
    """The frontmatter block including its closing '---', or '' if none."""
    if not text.startswith("---\n"):
        return ""
    end = text.find("\n---", 3)
    return text[: end + 4] if end >= 0 else ""


def fm_field(text, key):
    m = re.search(rf"^{key}:[ \t]*(.*)$", fm_block(text), re.M)
    return m.group(1).strip().strip("\"'") if m else ""


def link_targets(text):
    return ({t.strip() for t in kg.WIKILINK.findall(kg.CODE.sub("", text))}
            | {Path(t).stem for t in kg.MDLINK.findall(text)}) - {""}


def snapshot(cand):
    """{stem: link set} for every top-level note, same set analyse() reads."""
    out = {}
    for p in cand.glob("*.md"):
        if p.name not in kg.SKIP:
            out[p.stem] = link_targets(p.read_text(encoding="utf-8", errors="replace"))
    return out


def queries(cand):
    p = cand / "eval" / "retrieval.jsonl"
    out = []
    if p.exists():
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if isinstance(row, dict) and row.get("query") and row.get("expected"):
                out.append(row["expected"])
    return out


def state_of(cand):
    a = kg.analyse(cand, [], [])
    reach = {s for s, r in a["route"].items() if r and r["hops_from_index"] <= 2}
    return {"a": a, "reach": reach, "links": snapshot(cand), "expected": queries(cand)}


# ---- building one edit --------------------------------------------------

def build(cand, e):
    """Structural checks and the new text. Returns a plan; raises Hold('invalid', ...)."""
    kind, file = e["kind"], e["file"]
    if file == RETRIEVAL:
        if kind != "append":
            raise Hold("invalid", f"{RETRIEVAL} accepts append only")
    elif not FILE_RE.match(file):
        raise Hold("invalid", f"file must be a top-level *.md name or {RETRIEVAL}: {file!r}")
    path = (cand / file)
    if cand.resolve() not in path.resolve().parents:
        raise Hold("invalid", "path is outside the memory folder")
    exists = path.exists()

    if kind == "create":
        if exists:
            raise Hold("invalid", f"{file} already exists")
        text = e.get("content")
        if not isinstance(text, str) or not text.strip():
            raise Hold("invalid", "create needs non-empty content")
        text = text.replace("\r\n", "\n")
        if not text.endswith("\n"):
            text += "\n"
        return {"path": path, "old": None, "new": text, "eol": "\n", "added": text, "text_before": ""}

    if file == RETRIEVAL and not exists:
        old, eol = "", "\n"
    else:
        if not exists:
            raise Hold("invalid", f"{file} does not exist")
        old, eol = read_lf(path)
    if kind == "append":
        t = e.get("text")
        if not isinstance(t, str) or not t.strip():
            raise Hold("invalid", "append needs non-empty text")
        t = t.replace("\r\n", "\n")
        added = ("" if (not old or old.endswith("\n")) else "\n") + (t if t.endswith("\n") else t + "\n")
        return {"path": path, "old": old, "new": old + added, "eol": eol, "added": added, "text_before": old}
    if kind == "insert_line":
        after, t = e.get("after"), e.get("text")
        if not isinstance(after, str) or not after.strip() or not isinstance(t, str) or not t.strip():
            raise Hold("invalid", "insert_line needs after and text")
        body_start = len(fm_block(old))
        hits, pos = [], 0
        for line in old.split("\n"):
            if pos >= body_start and line.rstrip() == after.rstrip():
                hits.append(pos + len(line))
            pos += len(line) + 1
        if len(hits) != 1:
            raise Hold("invalid", f"anchor line found {len(hits)} times (needs exactly 1)")
        added = "\n" + t.replace("\r\n", "\n").rstrip("\n")
        return {"path": path, "old": old, "new": old[: hits[0]] + added + old[hits[0]:], "eol": eol,
                "added": added, "text_before": old}
    # fix_fact
    o, n = e.get("old"), e.get("new")
    if not isinstance(o, str) or not isinstance(n, str) or not o or o == n:
        raise Hold("invalid", "fix_fact needs old and a different new")
    if old.count(o) != 1:
        raise Hold("invalid", f"old text found {old.count(o)} times (needs exactly 1)")
    if old.find(o) < len(fm_block(old)):
        raise Hold("invalid", "old text is inside the frontmatter")
    return {"path": path, "old": old, "new": old.replace(o, n, 1), "eol": eol, "added": n,
            "text_before": old, "removed": o}


# ---- policy and gates ---------------------------------------------------

def policy(cand, e, plan):
    """Gate (a), (c), (d): what the edit is, before the graph is looked at."""
    kind, file, reasons = e["kind"], e["file"], []
    added = plan["added"]
    if file in ("MEMORY.md", "log.md"):
        raise Hold("never_automatic", f"{file} is never edited automatically (new index lines wait for the owner)")
    if e.get("source") not in OWNER_SOURCES | ({"verified_check"} if kind == "fix_fact" else set()):
        raise Hold("never_automatic", f"source {e.get('source')!r} is not the owner's words"
                   + (" (verified_check is for fix_fact only)" if e.get("source") == "verified_check" else ""))
    if len(added) > MAX_CHARS:
        reasons.append(f"edit adds {len(added)} characters (limit {MAX_CHARS})")
    if file != RETRIEVAL:
        shown = plan["new"] if kind == "create" else added
        before = plan["text_before"]
        rule = (Path(file).stem.startswith("feedback_") or fm_field(before, "type") == "feedback"
                or fm_field(plan["new"], "type") == "feedback")
        if rule:
            blob = " ".join([Path(file).stem, fm_field(plan["new"], "description"), shown])
            m = SENDING.search(blob)
            if m:
                reasons.append(f"rule file touches sending, deleting or publishing ({m.group(0)!r})")
        m = WEAKENING.search(shown)
        if m:
            reasons.append(f"added text may weaken a rule ({m.group(0)!r})")
    if reasons:
        raise Hold("never_automatic", *reasons)
    if e.get("recommended") is not True:
        raise Hold("not_recommended", "not marked recommended")
    # kind-specific content rules (gate a)
    if kind == "create":
        t = plan["new"]
        stem = Path(file).stem
        if not t.startswith("---\n") or not fm_block(t):
            raise Hold("gate_failed", "created file needs a frontmatter block")
        if fm_field(t, "name") != stem:
            raise Hold("gate_failed", f"frontmatter name must equal the file stem {stem!r}")
        if not fm_field(t, "description"):
            raise Hold("gate_failed", "frontmatter description is missing")
        if re.search(r"^\s*supersedes:", fm_block(t), re.M):
            raise Hold("gate_failed", "supersedes is never set automatically")
    elif kind == "insert_line":
        have = {p.stem for p in cand.glob("*.md")}
        for line in added.strip("\n").split("\n"):
            if not (HOW_TO.match(line) or PRECEDENT.match(line)):
                raise Hold("gate_failed", f"inserted line is not a How to apply or Precedent line: {line[:60]!r}")
            links = [t.strip() for t in kg.WIKILINK.findall(kg.CODE.sub("", line))]
            if PRECEDENT.match(line) and not links:
                raise Hold("gate_failed", "a Precedent line needs at least one [[link]]")
            gone = [t for t in links if t not in have]
            if gone:
                raise Hold("gate_failed", f"links to files that do not exist: {gone}")
    elif kind == "fix_fact":
        v = e.get("verify")
        if not isinstance(v, dict) or not v.get("value"):
            raise Hold("gate_failed", "fix_fact needs a read-only verify with a value")
        if "\n" in e["old"] or "\n" in e["new"]:
            raise Hold("gate_failed", "fix_fact is one line only")
        if str(v["value"]) not in e["new"]:
            raise Hold("gate_failed", "the verified value does not appear in the new text")
        if v.get("type") == "path_exists":
            if not Path(str(v["value"])).expanduser().exists():
                raise Hold("gate_failed", f"path does not exist: {v['value']}")
        elif v.get("type") == "file_contains":
            try:
                ok = str(v["value"]) in Path(str(v.get("file", ""))).read_text(encoding="utf-8", errors="replace")
            except OSError:
                ok = False
            if not ok:
                raise Hold("gate_failed", f"{v.get('file')} does not contain the verified value")
        else:
            raise Hold("gate_failed", f"unknown verify type {v.get('type')!r}")
    elif file == RETRIEVAL:
        have = {p.stem for p in cand.glob("*.md")}
        for line in added.strip("\n").split("\n"):
            try:
                row = json.loads(line)
                q, ex = row["query"], row["expected"]
            except (ValueError, KeyError, TypeError):
                raise Hold("gate_failed", f"not a query row: {line[:60]!r}")
            if not q or ex not in have:
                raise Hold("gate_failed", f"expected file does not exist: {ex!r}")


def graph_gate(cand, e, plan, before):
    """Gate (b) and the frontmatter rule, run on the candidate after the edit is written."""
    after = state_of(cand)
    reasons = []
    if not before["expected"] and e["kind"] in ("insert_line", "fix_fact"):
        reasons.append("no stored retrieval queries: this edit cannot be checked")
    if e["file"] != RETRIEVAL:
        if e["kind"] != "create" and fm_block(plan["text_before"]) != fm_block(plan["new"]):
            reasons.append("frontmatter block changed")
    broke = sorted({x for x in before["expected"] if x in before["reach"] and x not in after["reach"]})
    if broke:
        reasons.append(f"stored queries would lose their route: {broke}")
    lost = sorted((set(before["links"]) & set(after["a"]["unreachable"])) - set(before["a"]["unreachable"]))
    if lost:
        reasons.append(f"files become unreachable: {lost}")
    dead = sorted(set(after["a"]["dead_links"]) - set(before["a"]["dead_links"]))
    if dead:
        reasons.append(f"new dead links: {dead}")
    for stem, links in before["links"].items():
        gone = sorted(links - after["links"].get(stem, set()))
        if gone:
            reasons.append(f"{stem} loses links: {gone}")
    if reasons:
        raise Hold("gate_failed", *reasons)
    return after


# ---- the run ------------------------------------------------------------

def load_edits(path):
    try:
        edits = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as ex:
        die(f"cannot read edits: {ex}")
    if not isinstance(edits, list):
        die("edits file must be a JSON list")
    return edits


def run_gate(mem, edits, approve):
    tmp = tempfile.TemporaryDirectory()
    cand = Path(tmp.name) / "mem"
    shutil.copytree(mem, cand, ignore=shutil.ignore_patterns(".git", "auto_runs"))
    st, seen, decisions, applied = state_of(cand), set(), [], []
    for i, e in enumerate(edits):
        eid = str(e.get("id", "")) if isinstance(e, dict) else ""
        d = {"id": eid or f"#{i}", "kind": e.get("kind") if isinstance(e, dict) else None,
             "file": e.get("file") if isinstance(e, dict) else None, "approved": eid in approve}
        snap, plan, written = None, None, False
        try:
            if not isinstance(e, dict) or not eid:
                raise Hold("invalid", "edit needs an id")
            if eid in seen:
                raise Hold("invalid", "duplicate id")
            seen.add(eid)
            if e.get("kind") in NEVER_KINDS:
                raise Hold("never_automatic", f"kind {e['kind']!r} is never automatic")
            if e.get("kind") not in KINDS or not isinstance(e.get("file"), str):
                raise Hold("invalid", f"unknown kind or missing file ({e.get('kind')!r})")
            plan = build(cand, e)
            if not d["approved"]:
                policy(cand, e, plan)
            snap = plan["path"].read_bytes() if plan["path"].exists() else None
            write_eol(plan["path"], plan["new"], plan["eol"])
            written = True
            st = state_of(cand) if d["approved"] else graph_gate(cand, e, plan, st)
            d.update(decision="APPLY", category=None, reasons=(["approved by the owner: gates skipped"] if d["approved"] else []))
            applied.append({"id": eid, "kind": e["kind"], "file": e["file"], "added": plan["added"],
                            "removed": plan.get("removed"), "eol": plan["eol"], "approved": d["approved"],
                            "sha256": hashlib.sha256(plan["path"].read_bytes()).hexdigest()
                            if e["kind"] == "create" else None,
                            "summary": summarize(e, plan)})
        except Hold as h:
            if written:
                _restore(plan["path"], snap)
            d.update(decision="HOLD", category=h.category, reasons=h.reasons)
        decisions.append(d)
    return tmp, cand, decisions, applied


def _restore(path, snap):
    if snap is None:
        if path.exists():
            path.unlink()
    else:
        path.write_bytes(snap)


def summarize(e, plan):
    if e["kind"] == "fix_fact":
        return f"{e['file']}: {plan['removed'][:70]!r} -> {plan['added'][:70]!r}"
    first = plan["added"].strip("\n").split("\n")[0]
    return f"{e['kind']} {e['file']}: {first[:90]}"


def cmd_gate(a):
    mem = Path(a.mem)
    tmp, _, decisions, applied = run_gate(mem, load_edits(a.edits), set(a.approve))
    try:
        print(json.dumps({"mem": str(mem), "apply": len(applied), "hold": len(decisions) - len(applied),
                          "decisions": decisions}, indent=2))
    finally:
        tmp.cleanup()


def cmd_apply(a):
    if not a.opt_in:
        die("refused: automatic edits are off unless --opt-in is passed", 2)
    mem = Path(a.mem)
    edits = load_edits(a.edits)
    run = a.run_id or datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    rundir = mem / "eval" / "auto_runs" / run
    if rundir.exists():
        die(f"refused: run {run} already exists")
    tmp, cand, decisions, applied = run_gate(mem, edits, set(a.approve))
    try:
        touched = sorted({x["file"] for x in applied})
        for f in touched:
            src = cand / f
            dst = mem / f
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(src.read_bytes())
        warnings = []
        links_all = {p.stem: link_targets(p.read_text(encoding="utf-8", errors="replace"))
                     for p in mem.glob("*.md") if p.name != "log.md"}
        for x in applied:
            if x["kind"] == "create":
                stem = Path(x["file"]).stem
                if not any(stem in t for s, t in links_all.items() if s != stem):
                    warnings.append(f"{x['file']} was created but nothing links to it yet")
        by_id = {e.get("id"): e for e in edits if isinstance(e, dict)}
        held = [by_id[d["id"]] for d in decisions if d["decision"] == "HOLD" and d["id"] in by_id]
        rundir.mkdir(parents=True)
        manifest = {"run": run, "mem": str(mem), "applied": applied, "decisions": decisions,
                    "warnings": warnings, "reverted": []}
        (rundir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        (rundir / "held.json").write_text(json.dumps(held, indent=2), encoding="utf-8")
        files = touched + [f"eval/auto_runs/{run}/{n}" for n in ("manifest.json", "digest.md", "held.json")]
        (rundir / "digest.md").write_text(digest(mem, run, applied, decisions, held, warnings, files),
                                          encoding="utf-8")
        print(json.dumps({"run": run, "applied": [x["id"] for x in applied],
                          "held": [d["id"] for d in decisions if d["decision"] == "HOLD"],
                          "digest": str(rundir / "digest.md")}, indent=2))
    finally:
        tmp.cleanup()


def digest(mem, run, applied, decisions, held, warnings, files):
    me = f'python scripts/km_auto_gate.py'
    held_d = [d for d in decisions if d["decision"] == "HOLD"]
    out = [f"# Auto km lean run {run}", "",
           f"{len(applied)} applied, {len(held_d)} held. Nothing was committed or pushed.", "", "## Applied", ""]
    out += [f"- **{x['id']}** {x['summary']}" + (" (approved by the owner)" if x["approved"] else "")
            + f"\n  undo: `{me} revert --mem \"{mem}\" --run {run} --edit {x['id']}`" for x in applied] or ["- none"]
    out += ["", "## Held for review", ""]
    real = [d for d in held_d if d["category"] != "not_recommended"]
    for d in real:
        out.append(f"- **{d['id']}** ({d['category']}): {'; '.join(d['reasons'])}\n"
                   f"  approve: `{me} apply --mem \"{mem}\" --edits \"{mem}/eval/auto_runs/{run}/held.json\" "
                   f"--opt-in --approve {d['id']}`")
    out += [] if real else ["- none"]
    out += ["", "## Not recommended (add if you want)", ""]
    nr = [d for d in held_d if d["category"] == "not_recommended"]
    for d in nr:
        out.append(f"- **{d['id']}** {d.get('file')}: `{me} apply --mem \"{mem}\" --edits "
                   f"\"{mem}/eval/auto_runs/{run}/held.json\" --opt-in --approve {d['id']}`")
    out += [] if nr else ["- none"]
    out += ["", "## Warnings", ""] + ([f"- {w}" for w in warnings] or ["- none"])
    msg = f"km auto lean {run}: {len(applied)} applied, {len(held_d)} held"
    quoted = " ".join(f'"{f}"' for f in files)
    out += ["", "## Prepared commit (not run)", "",
            f"Message: `{msg}`", "", "```", f'git -C "{mem}" add -- {quoted}',
            f'git -C "{mem}" commit -m "{msg}" -- {quoted}', "```", ""]
    return "\n".join(out)


def cmd_revert(a):
    mem = Path(a.mem)
    mf = mem / "eval" / "auto_runs" / a.run / "manifest.json"
    if not mf.exists():
        die(f"no such run: {a.run}")
    m = json.loads(mf.read_text(encoding="utf-8"))
    x = next((i for i in m["applied"] if i["id"] == a.edit), None)
    if x is None:
        die(f"edit {a.edit} was not applied in run {a.run}")
    if a.edit in m["reverted"]:
        die(f"edit {a.edit} is already reverted")
    path = mem / x["file"]
    if not path.exists():
        die(f"refused: {x['file']} no longer exists")
    if x["kind"] == "create":
        if hashlib.sha256(path.read_bytes()).hexdigest() != x["sha256"]:
            die(f"refused: {x['file']} was changed since it was created")
        path.unlink()
    else:
        try:
            text, eol = read_lf(path)
        except Hold as h:
            die(f"refused: {h.reasons[0]}")
        add, rem = x["added"], x["removed"]
        if text.count(add) != 1:
            die(f"refused: the added text is in {x['file']} {text.count(add)} times (needs exactly 1)")
        text = text.replace(add, rem if x["kind"] == "fix_fact" else "", 1)
        write_eol(path, text, eol)
    m["reverted"].append(a.edit)
    mf.write_text(json.dumps(m, indent=2), encoding="utf-8")
    print(json.dumps({"reverted": a.edit, "file": x["file"]}))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("gate", cmd_gate), ("apply", cmd_apply), ("revert", cmd_revert)):
        p = sub.add_parser(name)
        p.add_argument("--mem", required=True)
        p.set_defaults(fn=fn)
        if name != "revert":
            p.add_argument("--edits", required=True)
            p.add_argument("--approve", nargs="*", default=[])
        if name == "apply":
            p.add_argument("--opt-in", action="store_true")
            p.add_argument("--run-id")
        if name == "revert":
            p.add_argument("--run", required=True)
            p.add_argument("--edit", required=True)
    a = ap.parse_args()
    if hasattr(a, "approve"):
        a.approve = [i for x in a.approve for i in x.split(",") if i]
    a.fn(a)


if __name__ == "__main__":
    main()
