# Eval mechanics

On-demand reference for `km-audit`, read one § at a time by the step that names it. Also the file formats `km` writes. Never needed at session start.

## §Principles

**Context efficiency is the overriding constraint.** A run succeeds when the pass rate is the same or better at the same or fewer always-loaded tokens.
1. Eval state costs nothing at session start: `eval/` is never indexed.
2. Every fix records its token delta; each run reports net always-loaded change next to pass rate.
3. Additions to always-loaded context (CLAUDE.md, MEMORY.md lines) need the owner's yes. On-demand nodes are fine.
4. Graduating a rule to a hook or script removes its text. No "just in case" duplicates.
5. Both skills carry a size budget; detail lives in on-demand files like this one.
6. Retiring obsolete scaffolding is a primary output.

**Budget: tiered, escalate on surprise.** Triage (scripted, every run) → probe (~5 cases per flagged item) → expand only where evidence contradicts expectation → ceiling, then ask.

**Known limits.** Replay tests stated intent, not behaviour in long noisy sessions: a real transcript violation always outranks a replay pass; never retire on replay alone or on absence of evidence. Subagents inherit CLAUDE.md and memory, so they can't be the without-rule arm (use the bare runner). Deterministic checks exist mainly for tool-call rules; report coverage as its own metric. Model-graded fixes never auto-apply.

## §Files (`<memory>/eval/`, never indexed)

### cases.jsonl — one failure case per line
```json
{"rule":"feedback_sheet_read_before_write",
 "session":"<session id>",
 "model":"claude-sonnet-5-5",
 "date":"2026-05-02",
 "situation":"User asks to add a row to the live tracking sheet",
 "expected":"Read the current header row before writing; no blind append",
 "check":{"type":"tool_call_absent","tool":"Bash","pattern":"sheet_tool.py append(?!.*--dry-run)"},
 "kind":"violation | correction | re-explanation",
 "captured_by":"km | km-audit",
 "status":"open | passing | retired"}
```
- Dedup key: `rule` + `session`. `model` = model of the failing assistant message, never the session's.
- `check`: object or `null`. `check.type`: `tool_call_absent`, `tool_call_present`, `arg_matches`, `file_unchanged`; `null` = judgment rule, counts against coverage.
- `km` appends at session close (owner-confirmed: the primary source for `failing`). The audit appends only triage candidates the owner confirms in the plan.

### scorecard.json — per artifact, per run
```json
{"run":"2026-05-10","model":"claude-opus-5-5",
 "artifacts":{
  "feedback_sheet_read_before_write":{
    "kind":"memory","basis":"compensation","enforced_by":"memory",
    "bytes_always":140,"bytes_on_demand":820,
    "relevant":7,"violations":{"claude-sonnet-5-5":0},
    "corrections":0,"loaded":5,"flag":"retire-candidate","verdict_basis":"transcript"}}}
```
- `bytes_always` = bytes the artifact adds to always-loaded context: its MEMORY.md line, CLAUDE.md text, or skill description (plugin and built-in skills included, taken from the session's skills listing).
- Run-level always-loaded bytes = CLAUDE.md files + MEMORY.md + the whole skills listing.

### retrieval.jsonl — written by km, replayed by the audit
```json
{"query":"where do the greenhouse readings end up?",
 "expected":"reference_greenhouse_sheet",
 "session":"…","date":"2026-05-02",
 "last_result":"pass | fail | null","last_run":"2026-05-10"}
```
The audit writes `last_result`/`last_run` and appends its generated pre-compaction queries with `"session":"audit:YYYY-MM-DD"`. A query whose natural answer is a command (not a memory) is re-seeded, not kept failing.

### runs.md — one line per run
`YYYY-MM-DD | model | pass N/M | retrieval N/M | coverage X% | always-loaded B bytes (Δ) | MEMORY.md B bytes | confound: ok/uncontrolled | changes: …`

## §Triage (scripted, no LLM)

Throwaway Python in the scratchpad, run with `python -X utf8 -I`. Stream the `.jsonl` transcripts; never load them whole.

**Window:** sessions modified since the previous run, newest first, cap 60, excluding the current one. First run: the 60 newest by mtime.

| Signal | How detected |
|---|---|
| Model | `message.model` on assistant entries; user turns inherit the preceding assistant's model |
| Correction (candidate) | High precision first: a `tool_result` rejection carrying user text; `[Request interrupted by user]` followed by a user message; "I told you" / "we agreed" / "remember". Then short user messages after an assistant turn with friction phrases ("no,", "don't", "I said", "again", "wrong", "not what"). Maps to a slug only with ≥ 2 rare-term overlaps with the rule's name + description; else unmapped |
| Relevant session (N = 5) | The rule's keyword map hits a `tool_use` input or a user turn |
| Violation | A rule's `check` pattern matches a `tool_use` input |
| Re-explanation | User restates a fact that exists in memory (keyword overlap with a description) |
| Permission friction | `tool_use` followed by a denial `tool_result` |
| Retry / defect | Same tool, near-identical input ≥ 3 times in a row, or a known error string |
| Memory read | `Read` on a memory path |
| Skill use | `<command-name>` tags and `Skill` tool calls |

**Triage corrections never flag on their own** (first run: 5 hits in 60 sessions, ~4 false). They go into the plan as candidates; confirmed ones become `cases.jsonl` rows (`captured_by: km-audit`).

**Compactable** (per slug, from `route_excluding_self`): still reachable, `hops_from_index ≤ 1`, and `path_bytes ≤ PATH_CAP`. PATH_CAP is uncalibrated: report `path_bytes` and `via` for every proposed drop and let the owner judge.

**Drop-set recheck:** single-slug checks can miss a chain that two drops break together. Copy the top-level `*.md` to a scratch folder, write the candidate MEMORY.md there, run `km_graph_check.py --mem <folder> --json`; `unreachable` must not grow.

## §Load receipt (triage, no LLM)

If the index is cut short at load time, rules stop applying and the audit could read that as the model not needing them. Triage records a receipt per session it scans, using only text it already reads: the session's `instructions` attachments (where Claude Code puts the loaded memory files; they can appear after the first lines of a resumed or long-starting session), the first 6 message entries of its transcript, and `MEMORY.md`.

**Whole** = the index's final non-empty line AND every `.md` link target in the index appear in that text. The hub count is the number of distinct link targets in `MEMORY.md`. Receipt values:
- `whole`: both markers present.
- `truncated`: index text present, final line or a target missing, and the index has not changed since the session started (or the index at session start, read from git history, confirms the cut).
- `absent`: no index text found (not loaded, or not captured in the transcript).
- `unknown`: the receipt is not whole, `MEMORY.md` was modified after the session started (`stale_index`), and no index-at-start is available (no `--history`, or no commit that old). The mismatch may be an edit, not a cut, so it is never called `truncated`.

**Index at session start (optional):** `--history <git repo> --index-path <MEMORY.md path relative to that repo>`. For a stale non-whole receipt the script runs read-only `git log --before=<session start> -1 -- <path>` and `git show <commit>:<path>` in that repo, and re-judges against that older index. Nothing is written or fetched.

**Evidence rule:** only `whole` sessions count as evidence for violations, relevant-session counts and retire-candidates. `truncated` is a real cut and is listed. `unknown` sessions are listed separately with their hub count, are never reported as truncated, and likewise do not count as evidence either way (a violation seen in one is not counted against a rule, and its silence does not support retiring one). Script: `scripts/km_load_receipt.py` (test: `tests/test_km_load_receipt.py`). Deliberately simple: if the index format changes (no `](x.md)` links), the receipt reads `absent` rather than guessing. It does not repair a load.

## §Restructure (index into theme hubs)

For an index that has to be restructured, not just trimmed (drop-lines candidates too few or failing replay; load receipts show `truncated`). Moving lines keeps every memory reachable at a lower always-loaded cost; dropping them does not. Script: `scripts/km_index_restructure.py` (test: `tests/test_km_index_restructure.py`, synthetic 120-rule graph). Stdlib only; reachability is `km_graph_check.analyse()` itself.

1. **Propose** (`propose --mem M --out D`): the feedback index lines are grouped greedily by the slug, title or description word shared by most lines (words in over half of all lines are ignored as too generic) (min 3, at most 4 hubs; the remainder forms an `other` hub, so no line stays behind). It writes a candidate folder `D` (never `M`): one `index_feedback_<theme>.md` hub per group holding the original lines byte-identical plus a `**Members:**` wikilink row, and a MEMORY.md with one line per hub in place of the moved lines. The owner may instead supply the grouping: `--themes themes.json` (`{"theme": ["slug", ...]}`; unlisted lines go to `other`; unknown or duplicate slugs are refused). Edited candidates are re-checked with `replay`.
2. **Queries:** one per moved slug. An existing `retrieval.jsonl` query is reused; otherwise one is generated from the line's title and description (the audit may reword it per §Retrieval replay and appends it with `"session":"audit:YYYY-MM-DD"`).
3. **Replay before and after:** each query's expected slug must be reachable from MEMORY.md within the hop budget (default 2: the hub, then the member) in the current and the candidate index. The LLM retrieval replay (§Retrieval replay, citation-grounded) runs on the same queries against the candidate index.
4. **Blocks** (exit 1): any query pass→fail; a one-line description missing or altered; a newly unreachable file. No partial approval of the groups: fix the candidate and replay again.
5. **Apply** only on the owner's yes: `apply --mem M --candidate D --owner-approved` re-runs replay, refuses when it blocks, and copies MEMORY.md and the new hubs. Commit it like other structural changes; revert = `git revert`.

Report in the plan: groups and sizes, bytes before/after, queries and results, hop budget.

**Truncation priority.** A `truncated` load receipt (§Load receipt) means rules were cut off at load time. It outranks the 17,000-byte target and every other finding, and applies even when the index is under target (the loader limit, not the target, is what cut it).

**Stale-name check (Step 0).** After a rename of a skill or command, the owner's CLAUDE.md files may still name the old command or a path that no longer exists. It searches the CLAUDE.md files Step 0 item 4 already loads, and checks that the paths they name exist (existence only; no file outside them is opened). Hits are reported with file and line, never edited without a yes.

## §Contradictions (whole graph, tiered)

Lint for meaning: contradictions, and claims superseded by newer ones. `km` reads only files it touches, so this is the only graph-wide check.

**Triage (no LLM):** rank candidate pairs, keep the top 30:
- feedback ↔ feedback and feedback ↔ CLAUDE.md rule blocks: ≥ 3 shared rare terms (TF-IDF over name, description, first 40 body lines) or a shared slug mention.
- Linked neighbours whose `modified` dates differ by ≥ 60 days (supersession risk).
- Opposing polarity ("never/always" vs "default/may/only when" on the same term) adds rank only.
- Skip pairs already judged `compatible` unless either file changed.

**Probe (LLM):** read each pair in full (cap 10 per run). Return `contradicts | supersedes (which is newer) | compatible`, a one-line quote from each side, and a resolution. The owner picks the winner; the loser is corrected or retired. Append each verdict to `eval/contradictions.jsonl`: `{"a":slug,"b":slug,"verdict":…,"run":date,"a_mod":…,"b_mod":…}`.

## §Probe

### Context-confound check: the bare runner
Subagents inherit CLAUDE.md and MEMORY.md, so rule probes run only through `scripts/bare_probe.py`: `claude -p` with an empty config dir, a cwd outside the home folder, no tools, no MCP, auto-memory off, auth via a setup-token in the OS credential store. Windows only in v0.1.
- `bare_probe.py --canary --model <id> --leak-marker "<owner name>"`: exit 0 `clean` = gate passes; 2 = leak; 3 = no token; 4 = a CLAUDE.md sits above the working folder (default `<system drive>\km-bare-probe`; override with `--root` or `KM_BARE_ROOT`); 1 = claude failed. Record in `runs.md`.
- Always pass `--model`; the runner's default may not be the model under test. A model newer than the CLI fails until `claude update`.
- Arm A: the rule text prepended as "Working rule: …". Arm B: the scenario alone. Same scenario, same model.
- `--json` reports `cost_usd`, the API-equivalent figure; on a subscription token it draws on the plan allowance rather than billing.

### Replay
- About 5 cases per flagged item; 2 arms × k=3 samples.
- **Scenario rule:** rebuild the scenario from the case's `situation`: setting and task only. Never state or hint at what the rule requires. One hinting sentence flipped the first probe from fail to pass; a hinted scenario makes every rule look retirable.
- The runner has no tools: ask for the message or the exact tool calls it would make, as text.
- The runner also lacks the host app's system prompt, which may itself cover some rules. A probe pass is not proof the rule is unneeded in the app. For rules with a deterministic check, scan transcripts too: one rule passed 3/3 per model in probes while transcripts showed it broken in more than half of the relevant tool calls.
- Score with the case's `check`. Without one, the result is model-graded and labelled so.

### Retrieval replay
- Cold subagent; its prompt holds the index under test and the query; it answers which file(s) or command it would open.
- **Citation-grounded control (required):** the inherited MEMORY.md still holds lines being dropped. Paste the index under a distinct label (`INDEX_UNDER_TEST`), tell the agent to ignore any other index, and require a verbatim quote of the line it chose, or NONE. A quote not in the supplied text = fail (leak).
- Pass = the expected slug; a hub whose links reach it (`--reachable`); or a command or skill file that links or names it.
- Compaction: (0) generate a query for every touched slug with none, phrased as the owner would ask, without copying its rare terms; append it. (1) Replay every affected query against current and candidate index; any pass→fail blocks that drop.
- Cap 20 sampled queries per run, plus all compaction-affected ones.

### Decision table
| Without rule | With rule | Transcript (current model) | Verdict |
|---|---|---|---|
| 3/3 pass | pass | no violations in ≥ N relevant sessions | retire-candidate → owner decides |
| 3/3 pass | pass | any violation in 90 days | keep (transcript wins) |
| fail | pass | any | still needed; stamp `validated_model` |
| fail | fail | any | soft rule failing → graduate |
| mixed | any | any | expand (more scenarios) |

`severity: high` rules (outbound or irreversible: send, delete, money) never go dormant on model evidence; they graduate to hooks.

### Ceilings
- 5 cases × 2 arms × k=3 = 30 runs per flagged item; 3 flagged items per run without asking.
- +10 scenarios per surprising item; beyond that, ask.

## §Dormant
`<memory>/dormant/` holds retired rules. Each gets a one-line tombstone in a `dormant` hub so graph health doesn't flag it. Revive = move it back and restore its index line.
