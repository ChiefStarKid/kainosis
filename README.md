# Kainosis plugin

**Claude's memory only grows. This plugin tests each rule against the current model and stops loading the ones it no longer needs, so your memory gets smaller as models get better.**

The model's weights belong to the vendor. The context belongs to you. The Kainosis plugin tunes that context against measured results: it tests each rule on the current model and retires the ones it no longer needs.

Topics: `llm-wiki` · `karpathy-llm-wiki` · `claude-code` · `claude-code-plugin` · `claude-skills` · `agent-memory` · `llm-memory` · `knowledge-graph` · `knowledge-management` · `personal-knowledge-management` · `context-engineering` · `context-window` · `llm-evaluation` · `evals` · `ai-agents` · `coding-agents` · `memory-pruning` · `second-brain` · `markdown` · `hub-and-spoke`

A fork of [Karpathy's LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) that turns it on the agent itself: corrections become tested rules, and rules the model outgrows are retired, within a fixed context budget.

**Before:** your memory says "read a sheet's header before writing to it", and every session pays for that line. **After:** `km-audit` runs the situation on the current model with and without the rule. If the model gets it right without being told, and your past sessions agree, the rule moves to `dormant/` and stops loading. "Sensor readings are tenths of a degree" is private knowledge no model can guess, so it stays.

**Use this if** you use Claude Code every day, keep memory or `CLAUDE.md` files, keep correcting Claude, and those files keep growing. It is built for one knowledge worker who controls only their own local folders, not the company's repositories, and has little time to tidy even those. Knowledge shared across a team or organisation is out of scope for now.

The **Solomon Framework** is the method: the thinking behind the capture, re-test and retire loop, set out in [What is different](#what-is-different) and [docs/](docs/). Its own home, written independent of any tool, is [the Solomon Framework gist](https://gist.github.com/ChiefStarKid/bb10932b9dd04752deb4db632f7c6fdc), a fork of Karpathy's. The gist treats the AI harness as an operating system with three jobs: what gets loaded, what gets written and how sessions relate. The Kainosis plugin implements the memory part. Connecting mail and other systems is not part of the plugin. It has two skills:
- **`/kainosis:km`** closes a session: it captures what is worth keeping, records each correction as an eval case (the situation, what you expected and the model that failed), checks graph health, and writes after a short Q&A. `/kainosis:km lean` is the cheap version to run before `/compact`.
- **`/kainosis:km-audit`** tests the rules against the current model and retires the ones it no longer needs, reporting pass rate next to always-loaded bytes (the size of what every session reads before you type).

Credit: the pattern comes from Andrej Karpathy's LLM Wiki gist (2026-04-04). Kept from it: the LLM writes and maintains, the human directs; an index plus an append-only log; lint; git history (optional here). Status: see the [latest release](https://github.com/ChiefStarKid/kainosis/releases/latest); the method is tested by one person on one profile. See [Results so far](#results-so-far).

### Terms

- **Memory Graph:** what Claude reads from memory (`MEMORY.md`, its hubs and pages, and the links between them), plus the settings you control.
- **Basis tag:** each rule is tagged `fact` or `preference` (permanent), or `compensation` (guards a model weakness, so it can retire).
- **Probe:** a clean-room test of a rule, run with and without its text on the current model, with no memory or tools loaded.
- **Retire:** move a rule to `dormant/`, where it no longer loads and can be moved back.
- **Graduate:** replace a rule's text with a hook (a script Claude Code runs around a tool call) that enforces it.
- **Hub-and-spoke:** `MEMORY.md` points to a few hubs, and each hub lists its pages, so the index stays small as pages grow.

## Use this if

Beyond the line above, it fits best if you work under constraints like these, which I think many corporate knowledge workers share. Each one forced a design choice.

| Constraint | Design it forced |
|---|---|
| Small token budget | Hub-and-spoke graph; a byte budget on always-loaded context; retirement as a primary output |
| Can't always use the best model | `basis` tags on rules; cases record the model that failed; rules re-tested and retired when the model changes |
| No control over corporate repositories | Sources stored as pointers, never reorganised or copied; work and personal kept in separate profiles (one config dir each), so each profile sets its own memory path and scope rule |
| Locations change without warning | Pointers repaired when used, not swept; unused and stale is acceptable |

The original pattern fits well when you own your sources, run a frontier model and have context to spare. Take those away and the design has to change.

## What is different

1. **A behaviour layer, not only a knowledge base.** Corrections become eval cases (`eval/cases.jsonl`). Rules are re-tested per model and retired when the model no longer needs them. A rule earns no credit when the model behaves correctly without it: a model that refuses a risky action on its own is not the rule working. Each probe runs with and without the rule's text to tell the two apart. Karpathy's wiki is a library the agent maintains; this is the agent's own training layer, kept outside the weights.
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
| Upkeep | lint | an archive of copied sources on owned storage | cases, per-model re-tests, retirement |

[Vivian Balakrishnan's NanoClaw gist](https://gist.github.com/VivianBalakrishnan/a7d4eec3833baee4971a0ee54b08f322) (2026-04-24) also forks Karpathy, in the opposite direction, running on a Raspberry Pi. It fits owned infrastructure: sovereign storage at a fixed cost, data kept off public cloud, and a local model could take inference off the meter too. This fork fits a rented model in an environment you don't control, where tokens are the scarce resource and sources live elsewhere. Same cost and control question, opposite starting points. Neither is better; pick the one that matches your constraints.

## Tech stack

Built and tested on:
- Claude Code in the Claude Desktop app (Code tab), CLI 2.1.330
- Windows 11; Windows PowerShell 5.1 and Git Bash
- Python 3.13; pywin32 for the probe runner only
- Claude Pro plan, no extra usage; models switched per task (Opus 5.5, Sonnet 5.5)
- Memory kept in a local git repo, so every close-out and structural fix is a revertable commit. Git is optional: a local safety net that needs no company repository, not a requirement. Without it, the commit step is skipped
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

### Updating

Nothing is pushed to your client: you pull updates. The marketplace points at the latest release, so a new install and an update both get the released Kainosis plugin, never work in progress on `main`, and you get a new version only when a release changes `version` in `plugin.json`. Auto-update is off by default for third-party marketplaces like this one, so update by hand or turn it on in `/plugin` → Marketplaces → select the marketplace → auto-update.

To update by hand:

1. In a terminal, run `claude plugin update kainosis@kainosis`; it refreshes the marketplace listing first. In the app, refresh the listing yourself, then update: `/plugin` → Marketplaces → Update marketplace, then Installed → Update now.
2. Run `/reload-plugins`, or start a new session.

If the Update button in the app is greyed out although a newer release exists, the listing is probably out of date: refresh the marketplace first. The app lists the plugin as "Kainosis".

`/reload-plugins` picks up most changes in an open session, but a new session is the sure way. New releases are listed in the [CHANGELOG](CHANGELOG.md).

### Example prompts

1. At the end of a session in which you corrected Claude: `/kainosis:km`. It asks what to keep, records each correction as an eval case, and commits the memory changes.
2. When the context is filling up: `/kainosis:km lean`, then paste the `/compact Keep: …` line it ends with. Claude Code doesn't let a skill start a compaction itself, so this last step stays manual. If you run the optional PreCompact example hook and tell `km lean` so, a bare `/compact` carries the Keep list instead. You can type that `/compact` while `km lean` is still running: it queues and fires after the Q&A.
   `/kainosis:km lean auto` is the opt-in variant, needed on every run: edits that pass a strict gate (new notes, appended lines, one-line fact fixes, only from your own words) are written without a question, and everything else is asked as usual. Each run leaves a digest with one revert command per edit. It is new and has had no live run yet ([details](docs/auto-km-lean.md)).
3. After switching to a new model, or once a month: `/kainosis:km-audit`. It reports which rules the model still needs and proposes retiring the rest, with the always-loaded bytes saved.

### What it reads, writes and sends

Everything stays on your machine except the two items marked **network**.

| Component | Reads | Writes | Network |
|---|---|---|---|
| `km` | The current conversation; files in `memory_path`; your `scope_rule_file` | Memory files, `MEMORY.md`, `log.md` and `eval/*.jsonl` inside `memory_path`. `km lean` also writes `<temp dir>/claude/km-keep.txt` (the Keep line already shown in the chat), only when you have said in that conversation that you run the PreCompact example hook | If `memory_path` is in a git repo it commits there. It runs `git push` to **your own remote** only if your scope file says to, to the branch it names; never a force-push |
| `km-audit` | Files in `memory_path`; your past Claude Code session transcripts in your config dir (`<config dir>/projects/*/*.jsonl`, at most the 60 newest since the last run); for the load receipt, their loaded-instructions entries, and with the optional `--history` flag read-only `git log`/`git show` in your memory repo | Memory files and `eval/` state inside `memory_path`, and a plan file in the session scratchpad | Commits like `km`; never pushes unless you say so in the session. Rule probes go through `bare_probe.py` (below) |
| `scripts/km_graph_check.py` | Files in `memory_path` | Nothing | None |
| `scripts/km_auto_gate.py` (only for `km lean auto`, or `--opt-in` yourself) | The proposed edits and files in `memory_path` | Without asking: new notes, appended or inserted lines and one-line fact fixes in `memory_path`, plus a run folder with the digest under `eval/auto_runs/`. Never `MEMORY.md` or frontmatter, never text from tool results; sending, deleting or publishing rules, weakening wording and edits over 1,500 characters are always held for your answer. Runs no git | None |
| `scripts/km_close.py` (run by `km` at close-out) | A JSON file of the confirmed items, kept in the temp folder; `eval/*.jsonl`, `log.md` and `build_backlog.md` in `memory_path` | Appends to those same files, through a temp file renamed into place; prints the paths it wrote | None |
| `scripts/bare_probe.py` (optional, Windows) | A token you stored in Windows Credential Manager (`ClaudeBareProbe-OAuth`) | An empty config folder and a work folder under `--root` / `KM_BARE_ROOT` (default `<system drive>\km-bare-probe`) | **network:** runs `claude -p` to send short test prompts to Anthropic, as you, with that token. A prompt is a scenario rebuilt from one of your recorded cases and, in one of the two arms, the text of the rule under test |
| `scripts/bare_probe_token_setup.py` (optional, once) | Your clipboard (the token you copied from `claude setup-token`) | The token into Windows Credential Manager; then it clears the clipboard. It prints only the token's length | None |

No telemetry, no other services, no MCP servers, and the plugin registers no hooks. The repo ships two example hooks in `hooks/`, neither active unless you install it ([enable guide](hooks/README.md)); neither uses the network. The rules-reminder hook reads only its own config. The PreCompact hook reads `<temp dir>/claude/km-keep.txt` when a compaction starts, passes it on as compaction instructions and deletes it; a file older than 30 minutes is removed unused. Each run appends one line (time, session id, trigger, outcome; never the Keep text) to `<temp dir>/claude/km-keep-hook.log`, which is never rotated or sent anywhere; delete it any time. The Keep file is shared, so another session compacting in the same profile can consume it first. Tested on Windows with a user-level copy of the hook; this repo copy, `km lean` end to end, auto-compaction, macOS and Linux are untested. The plugin itself stores your name, memory files and eval state only on your machine. As in any Claude Code session, whatever the skills read into the conversation (memory files, transcript excerpts) goes to the model you are using; beyond that, data leaves your machine only as probe prompts sent by `bare_probe.py` and whatever you choose to push to your own git remote.

### Python prerequisites

- Python 3 on `PATH` as `python`.
- `km_graph_check.py` needs nothing else.
- `bare_probe.py` (optional, Windows) needs pywin32: `python -m pip install pywin32`. One-time token setup, in a plain terminal outside Claude: run `claude setup-token`, copy the token, then `python scripts/bare_probe_token_setup.py`. The token goes straight to Windows Credential Manager; it is never echoed or written to disk.

### Try it on the example

`examples/graph/` is a small fictional Memory Graph (a hobby greenhouse) with hubs, spokes, one feedback rule of each basis and sample eval files:

```bash
python scripts/km_graph_check.py --mem examples/graph
```

Expected: 11 files, 0 islands, 0 unreachable, 0 dead links, nothing missing.

## Results so far

From my own profile's memory, 2026-11-20 to 2026-11-21. One person, one profile: indicative, not proof.

In short: the always-loaded index shrank by almost 40% while staying correct, and the one rule that looked safe to retire but wasn't was caught by real sessions. A second cluster retired nothing: the method kept every rule it could not back with a second source.

- **MEMORY.md:** 21,233 bytes before the first rules pilot; 20,580 at the start of the first audit; 15,316 after it; 13,039 bytes today. Always-loaded context in that first audit fell from 28,886 to 23,622 bytes.
- **Feedback rules:** 179 files before the pilot; 167 at the rules pass, when every one was tagged with a `basis`; 91 today. The rest were merged, moved to the tool docs where they apply, graduated into a hook, or retired to `dormant/`.
- **Graph health today:** 256 files, 0 islands, 0 unreachable, 0 dead links. The first audit took unreachable files from 8 to 0 and dead links from 2 to 0.
- **Probes:** 104 bare-context runs on 10 compensation rules across two models. 4 rules passed 3/3 without their text on both models and were retired; 3 were still needed. One rule passed its probes yet transcripts showed it broken in 614 of 1,073 shell calls on one model, so it went to a hook instead: a transcript violation outranks a probe pass.
- **Hooks:** 11 rules graduated into one reminder hook; their text left memory.
- **Second cluster (spreadsheet and document handling), later in November 2026:** 17 rules (8 compensation, 4 fact, 5 preference). 100 bare-context runs on 6 compensation rules across two models: 1 still needed; 4 passed every probe but were kept, because no transcripts covered that work and a probe pass alone never retires a rule; 1 passed but transcripts show 5 likely lapses (5 HTML writes, after dropping 1 non-HTML hit), so it stays as a hook candidate. 0 retired; rule count and index size unchanged. Scoring was model-graded except one regex check. Details: [docs/second-cluster.md](docs/second-cluster.md).

## Roadmap

The roadmap lives in [GitHub issues labelled `roadmap`](https://github.com/ChiefStarKid/kainosis/issues?q=is%3Aissue+is%3Aopen+label%3Aroadmap); [milestone v0.2](https://github.com/ChiefStarKid/kainosis/milestone/1) holds what has shipped. Headlines:
- **Shipped in v0.2:** capture from the owner's words only ([#10](https://github.com/ChiefStarKid/kainosis/issues/10)), a load receipt ([#8](https://github.com/ChiefStarKid/kainosis/issues/8)), a `supersedes:` field ([#12](https://github.com/ChiefStarKid/kainosis/issues/12)) and an example rules-reminder hook ([#5](https://github.com/ChiefStarKid/kainosis/issues/5)); in v0.2.1, an example PreCompact hook for `km lean` ([#6](https://github.com/ChiefStarKid/kainosis/issues/6)).
- **Shipped in v0.3 and v0.4:** a close-out verdict, SAFE or NOT SAFE, for ending a thread ([#19](https://github.com/ChiefStarKid/kainosis/issues/19)); restructuring an oversized index into theme hubs ([#20](https://github.com/ChiefStarKid/kainosis/issues/20)); `km lean auto`, first slice ([#23](https://github.com/ChiefStarKid/kainosis/issues/23)); scripted close-out appends; and CI on every push ([#21](https://github.com/ChiefStarKid/kainosis/issues/21)). See the [CHANGELOG](CHANGELOG.md).
- **Next:** the **Performance Layer**, a planned tuning process, not built yet. Here "performance" means how well the agent does the work, not speed. It would watch sessions, run checks and replay tests, and propose where each rule loads and which rules retire on each model. Unlike fine-tuning, every change is visible and reversible in git. It can only steer what the model already does; it can't add a capability the model lacks.
- **Later:** `bare_probe.py` beyond Windows, published error rates for each check, harder hooks and opt-in session grooming.

Items marked `data-handling` change what the plugin reads, writes or sends; they ship with a CHANGELOG "Data handling" note and a PRIVACY.md update. Several items came from comparing notes with [Link](https://github.com/gowtham0992/link), another implementation of the LLM Wiki pattern.

## Layout

```
.claude-plugin/   plugin.json (name, version, options) · marketplace.json
skills/km/        SKILL.md
skills/km-audit/  SKILL.md
scripts/          km_graph_check.py · km_close.py · km_auto_gate.py · km_verdict_check.py · km_index_restructure.py · km_load_receipt.py · bare_probe.py · bare_probe_token_setup.py
tests/            tests run by CI on every push
docs/             schema.md · evals.md · scope-rule.md · structure-rules.md · km-full.md · auto-km-lean.md · closeout-verdict.md · evolution.md · second-cluster.md
hooks/            example hooks, not registered: rules_reminder.py · precompact_keep.py
examples/graph/   fictional Memory Graph
PRIVACY.md · SECURITY.md · CHANGELOG.md · LICENSE · CITATION.cff
```

The plugin id (`kainosis`) sets the command prefix. To rename it, change `name` in `.claude-plugin/plugin.json`, the marketplace `name` and plugin entry `name` in `.claude-plugin/marketplace.json`, and the `/kainosis:` commands and `kainosis@kainosis` install line in this README. The skills never name it.

## Licence

MIT. See [LICENSE](LICENSE). To cite, see [CITATION.cff](CITATION.cff). Privacy: [PRIVACY.md](PRIVACY.md). Security reports and support: [SECURITY.md](SECURITY.md). Changes: [CHANGELOG.md](CHANGELOG.md).
