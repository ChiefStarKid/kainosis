# Kainosis

**A Claude Code plugin implementing the Solomon Framework: a Karpathy LLM Wiki fork for agents on a context budget. Corrections become tested rules; rules the model outgrows are retired.**

Topics: `llm-wiki` · `karpathy-llm-wiki` · `claude-code` · `claude-code-plugin` · `claude-skills` · `agent-memory` · `llm-memory` · `knowledge-graph` · `knowledge-management` · `personal-knowledge-management` · `context-engineering` · `context-window` · `llm-evaluation` · `evals` · `ai-agents` · `coding-agents` · `memory-pruning` · `second-brain` · `markdown` · `hub-and-spoke`

A fork of [Karpathy's LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) that turns it on the agent itself: corrections become tested rules, and rules the model outgrows are retired, within a fixed context budget.

The **Solomon Framework** is the method: the thinking behind the capture, re-test and retire loop, set out in [What is different](#what-is-different) and [docs/](docs/). Its own home, written independent of any tool, is [the Solomon Framework gist](https://gist.github.com/ChiefStarKid/bb10932b9dd04752deb4db632f7c6fdc), a fork of Karpathy's. Kainosis is its Claude Code implementation, with two skills:
- **`/kainosis:km`** closes a session: it captures what is worth keeping, records each correction as an eval case, checks graph health, and writes after a short Q&A. `/kainosis:km lean` is the cheap version to run before `/compact`.
- **`/kainosis:km-audit`** tests the rules against the current model and retires the ones it no longer needs, reporting pass rate next to always-loaded bytes.

Credit: the pattern comes from Andrej Karpathy's LLM Wiki gist (2026-04-04). Kept from it: the LLM writes and maintains, the human directs; an index plus an append-only log; lint; git history. The original gist carries no licence; this repo contains no text from it, only the pattern described in its own words. Status: v0.1, tested by one person on one profile. See [Results so far](#results-so-far).

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

From GitHub:

```bash
claude plugin marketplace add ChiefStarKid/kainosis
claude plugin install kainosis@kainosis --config memory_path="<your memory dir>" --config owner_name="<your name>"
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

### Example prompts

1. At the end of a session in which you corrected Claude: `/kainosis:km`. It asks what to keep, records each correction as an eval case, and commits the memory changes.
2. When the context is filling up: `/kainosis:km lean`, then paste the `/compact Keep: …` line it ends with. Claude Code doesn't let a skill start a compaction itself, so this last step stays manual.
3. After switching to a new model, or once a month: `/kainosis:km-audit`. It reports which rules the model still needs and proposes retiring the rest, with the always-loaded bytes saved.

### What it reads, writes and sends

Everything stays on your machine except the two items marked **network**.

| Component | Reads | Writes | Network |
|---|---|---|---|
| `km` | The current conversation; files in `memory_path`; your `scope_rule_file` | Memory files, `MEMORY.md`, `log.md` and `eval/*.jsonl` inside `memory_path` | If `memory_path` is in a git repo it commits there. It runs `git push` to **your own remote** only if your scope file says to, to the branch it names; never a force-push |
| `km-audit` | Files in `memory_path`; your past Claude Code session transcripts in your config dir (`<config dir>/projects/*/*.jsonl`, at most the 60 newest since the last run) | Memory files and `eval/` state inside `memory_path`, and a plan file in the session scratchpad | Commits like `km`; never pushes unless you say so in the session. Rule probes go through `bare_probe.py` (below) |
| `scripts/km_graph_check.py` | Files in `memory_path` | Nothing | None |
| `scripts/bare_probe.py` (optional, Windows) | A token you stored in Windows Credential Manager (`ClaudeBareProbe-OAuth`) | An empty config folder and a work folder under `--root` / `KM_BARE_ROOT` (default `<system drive>\km-bare-probe`) | **network:** runs `claude -p` to send short test prompts to Anthropic, as you, with that token. A prompt is a scenario rebuilt from one of your recorded cases and, in one of the two arms, the text of the rule under test |
| `scripts/bare_probe_token_setup.py` (optional, once) | Your clipboard (the token you copied from `claude setup-token`) | The token into Windows Credential Manager; then it clears the clipboard. It prints only the token's length | None |

No telemetry, no other services, no hooks, no MCP servers. The plugin itself stores your name, memory files and eval state only on your machine. As in any Claude Code session, whatever the skills read into the conversation (memory files, transcript excerpts) goes to the model you are using; beyond that, data leaves your machine only as probe prompts sent by `bare_probe.py` and whatever you choose to push to your own git remote.

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
- Session grooming as an optional extra (Desktop-only): archive sessions with a searchable catalogue, keep a list of sessions cited as eval evidence, and propose deletes of noise threads for approval. The keep-list and the delete step ship together.
- `bare_probe.py` beyond Windows (macOS Keychain, Linux secret store).
- The rules-reminder hook as an example `hooks/` folder.
- Four more checker scripts, a `Trigger:` backfill for older rules, a Why-exemption for hubs, and calibration of the compaction path-bytes cap.

## Layout
From comparing notes with [Link](https://github.com/gowtham0992/link), another implementation of the LLM Wiki pattern:
- **Load receipt.** A per-session check that the always-loaded context arrived whole and was not cut short, added to `km-audit` triage.
- **Published error rates.** Report how often each check is wrong: retire-candidates later found still needed, probe verdicts that transcripts contradict, and triage correction hits that were false. Make the probe-versus-transcript disagreement a standing metric in `runs.md`.
- **Capture from the owner's words only.** Cases and correction candidates come only from the owner's own turns; text from tool results never enters a rule without the owner seeing its source. Memory loads into every session, so it is a prompt-injection target.
- **Harder hooks and checks.** Match `check` patterns and graduated hooks against commands as the shell runs them (inside `&&` chains, `bash -c`, `sudo`), not raw tool input, and stop the agent from editing its own hook files.
- **Supersession at write time.** A `supersedes:` field written at close-out, so a revised fact names what it replaces and the audit's contradiction pass has fewer pairs to judge.


```
.claude-plugin/   plugin.json (name, version, options) · marketplace.json
skills/km/        SKILL.md
skills/km-audit/  SKILL.md
scripts/          km_graph_check.py · bare_probe.py · bare_probe_token_setup.py
docs/             schema.md · evals.md · scope-rule.md · evolution.md
examples/graph/   fictional memory graph
PRIVACY.md · SECURITY.md · CHANGELOG.md · LICENSE · CITATION.cff
```

The plugin id (`kainosis`) sets the command prefix. To rename it, change `name` in `.claude-plugin/plugin.json`, the marketplace `name` and plugin entry `name` in `.claude-plugin/marketplace.json`, and the `/kainosis:` commands and `kainosis@kainosis` install line in this README. The skills never name it.

## Licence

MIT. See [LICENSE](LICENSE). To cite, see [CITATION.cff](CITATION.cff). Privacy: [PRIVACY.md](PRIVACY.md). Security reports and support: [SECURITY.md](SECURITY.md). Changes: [CHANGELOG.md](CHANGELOG.md).
