# solomon

A fork of [Karpathy's LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) that turns it on the agent itself: corrections become tested rules, and rules the model outgrows are retired, within a fixed context budget.

Packaged as a Claude Code plugin with two skills:
- **`/solomon:km`** closes a session: it captures what is worth keeping, records each correction as an eval case, checks graph health, and writes after a short Q&A. `/solomon:km lean` is the cheap version to run before `/compact`.
- **`/solomon:km-audit`** tests the rules against the current model and retires the ones it no longer needs, reporting pass rate next to always-loaded bytes.

Credit: the pattern comes from Andrej Karpathy's LLM Wiki gist (2026-04-04). Kept from it: the LLM writes and maintains, the human directs; an index plus an append-only log; lint; git history. Status: v0.1, tested by one person on one profile. See [Results so far](#results-so-far).

## Who it is for

I built this under constraints that I think many corporate knowledge workers share. Each one forced a design choice.

| Constraint | Design it forced |
|---|---|
| Small token budget | Hub-and-spoke graph; a byte budget on always-loaded context; retirement as a primary output |
| Can't always use the best model | `basis` tags on rules; cases record the model that failed; rules re-tested and retired when the model changes |
| No control over corporate repositories | Sources stored as pointers, never reorganised or copied; work and personal kept in separate profiles (one config dir each), so each profile sets its own memory path and scope rule |
| Locations change without warning | Pointers repaired when used, not swept; unused and stale is acceptable |

Karpathy's gist implicitly assumes a person who owns their sources, uses a frontier model and has context to spare.

## What is different

1. **A behaviour layer, not only a knowledge base.** Corrections become eval cases (`eval/cases.jsonl`). Rules are re-tested per model and retired when the model no longer needs them. Karpathy's wiki is a library the agent maintains; this is the agent's own training layer, kept outside the weights.
2. **A hub-and-spoke graph sized to a context budget, not a flat index.** `MEMORY.md` points to hubs; each hub's `**Cluster:**` line points to its spokes. Nodes are typed (feedback, project, reference, user). `scripts/km_graph_check.py` measures reachability, hops and the bytes read along each path. A flat index grows with every page; hub-and-spoke grows with the number of hubs.
3. **Sources by reference, freshness by use.** The graph stores where a source is and what it holds. It never copies or reorganises the source.

Two layers, split by the `basis` tag on each rule:
- **Knowledge** the model can't know (`fact`, `preference`). Permanent.
- **Governance** for what the model can't yet do reliably (`compensation`). Should shrink as models improve. Only this layer is retired on model grounds.

Example: "sensor readings are tenths of a degree" is a `fact`; no model can guess it. "Read a sheet's header before writing to it" is a `compensation`; a stronger model may not need telling, and `km-audit` is what finds out.

## Related approaches

| | Karpathy, LLM Wiki | Balakrishnan, NanoClaw | This fork |
|---|---|---|---|
| Fits | the pattern | owned infrastructure | rented model, uncontrolled environment |
| Sources | wiki pages the LLM writes | raw sources copied and archived | pointers; sources stay where they are |
| Retrieval | index file | SQLite + embeddings graph, recall injected on every message | hub-and-spoke index, files loaded on demand |
| Scarce resource | — | storage and data control (fixed-cost hardware) | tokens |
| Pruning, evals | lint | not described | cases, per-model re-tests, retirement |

[Vivian Balakrishnan's NanoClaw gist](https://gist.github.com/VivianBalakrishnan/a7d4eec3833baee4971a0ee54b08f322) (2026-04-24) also forks Karpathy, in the opposite direction, running on a Raspberry Pi. It fits owned infrastructure: sovereign storage at a fixed cost, data kept off public cloud, and a local model could take inference off the meter too. This fork fits a rented model in an environment you don't control, where tokens are the scarce resource and sources live elsewhere. Same cost and control question, opposite starting points. Neither is better; pick the one that matches your constraints.

## Tech stack

Built and tested on:
- Claude Code in the Claude Desktop app (Code tab), CLI 2.1.330
- Windows 11; Windows PowerShell 5.1 and Git Bash
- Python 3.13; pywin32 for the probe runner only
- Claude Pro plan, no extra usage; models switched per task (Opus 5.5, Sonnet 5.5)
- Memory kept in a git repo, so every close-out and structural fix is a revertable commit
- Work systems reached through local scripts rather than MCP servers, because the corporate environment was not mine to configure

| Component | Portability | Constraint behind it |
|---|---|---|
| Graph pattern and [schema](docs/schema.md) | Portable as-is | Small token budget |
| `scripts/km_graph_check.py` (stdlib only) | Portable as-is | Small token budget |
| Eval file formats ([evals.md](docs/evals.md) §Files) | Portable as-is | Can't always use the best model |
| `km` and `km-audit` method | Portable as-is | All four |
| `scripts/bare_probe.py` + `bare_probe_token_setup.py` | **Windows only**: pywin32, Windows Credential Manager. On macOS the token would go in Keychain (not written yet) | Can't always use the best model |
| Commit step | Needs the memory dir in a git repo; skipped otherwise | Locations change |

Without the probe runner, `km-audit` still runs: it skips rule probes and bases its verdicts on recorded cases and transcripts, and says so in its plan. The dated reason behind each choice is in [docs/evolution.md](docs/evolution.md).

## Install

From GitHub (once published):

```bash
claude plugin marketplace add <owner>/<repo>
claude plugin install solomon@solomon --config memory_path="<your memory dir>" --config owner_name="<your name>"
```

Or install from inside Claude Code with `/plugin`, which prompts for the options. Change them later with `/plugin` → configure.

Local, for one session, without installing:

```bash
claude --plugin-dir "<path to this repo>"
```

Options (stored per profile, so two profiles can point at two memory dirs):

| Key | Type | Purpose |
|---|---|---|
| `memory_path` | directory | Folder with `MEMORY.md` and the memory files. Claude Code's auto-memory lives at `<config dir>/projects/<project>/memory` |
| `owner_name` | string | How the skills refer to you |
| `scope_rule_file` | file, optional | Which memory is in scope for this profile ([format](docs/scope-rule.md)) |

The version is pinned in `plugin.json`, so a new commit reaches installed copies only when the version is bumped.

### Python prerequisites

- Python 3 on `PATH` as `python`.
- `km_graph_check.py` needs nothing else.
- `bare_probe.py` (optional, Windows) needs pywin32: `python -m pip install pywin32`. One-time token setup, in a plain terminal outside Claude: run `claude setup-token`, copy the token, then `python scripts/bare_probe_token_setup.py`. The token goes straight to Windows Credential Manager; it is never echoed or written to disk.

### Try it on the example

`examples/graph/` is a small fictional memory graph (a hobby greenhouse) with hubs, spokes, one feedback rule of each basis and sample eval files:

```bash
python scripts/km_graph_check.py --mem examples/graph
```

Expected: 11 files, 0 islands, 0 unreachable, 0 dead links, nothing missing.

## Results so far

From my own profile's memory, 2026-11-20 to 2026-11-21. One person, one profile: indicative, not proof.

- **MEMORY.md:** 21,233 bytes before the first rules pilot; 20,580 at the start of the first audit; 15,316 after it; 13,039 bytes today. Always-loaded context in that first audit fell from 28,886 to 23,622 bytes.
- **Feedback rules:** 179 files before the pilot; 167 at the rules pass, when every one was tagged with a `basis`; 91 today. The rest were merged, moved to the tool docs where they apply, graduated into a hook, or retired to `dormant/`.
- **Graph health today:** 256 files, 0 islands, 0 unreachable, 0 dead links. The first audit took unreachable files from 8 to 0 and dead links from 2 to 0.
- **Probes:** 104 bare-context runs on 10 compensation rules across two models. 4 rules passed 3/3 without their text on both models and were retired; 3 were still needed. One rule passed its probes yet transcripts showed it broken in 614 of 1,073 shell calls on one model, so it went to a hook instead: a transcript violation outranks a probe pass.
- **Hooks:** 11 rules graduated into one reminder hook; their text left memory.

## Roadmap

Out of v0.1, planned for later updates:
- Prove the rules-separation method on a second cluster.
- Full evolution history (v0.1 ships a short dated list).
- Session grooming as an optional extra (Desktop-only).
- `bare_probe.py` beyond Windows (macOS Keychain, Linux secret store).
- The rules-reminder hook as an example `hooks/` folder.
- Four more checker scripts, a `Trigger:` backfill for older rules, a Why-exemption for hubs, and calibration of the compaction path-bytes cap.

## Layout

```
.claude-plugin/   plugin.json (name, version, options) · marketplace.json
skills/km/        SKILL.md
skills/km-audit/  SKILL.md
scripts/          km_graph_check.py · bare_probe.py · bare_probe_token_setup.py
docs/             schema.md · evals.md · scope-rule.md · evolution.md
examples/graph/   fictional memory graph
```

The plugin name (`solomon`) sets the command prefix. It appears in `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` and this README; the skills never name it.

## Licence

MIT. See [LICENSE](LICENSE). To cite, see [CITATION.cff](CITATION.cff).
