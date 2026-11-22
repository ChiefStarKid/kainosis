---
name: km-audit
description: "On-demand audit of the memory graph: re-tests rules on the current model, retires unneeded ones, compacts the index within a context budget."
---

# km-audit

Audits and improves the graph, skills and tools. Mechanics: `REF` = `${CLAUDE_PLUGIN_ROOT}/docs/evals.md`. Read only the § a step names, when that step runs.

**Overriding constraint: context efficiency.** A run succeeds when the pass rate is the same or better at the same or fewer always-loaded tokens. Eval serves efficiency; it never competes with it.

**Names:** `OWNER` = ${user_config.owner_name}. `MEM` = `${user_config.memory_path}`. `SCOPE` = `${user_config.scope_rule_file}` (empty = whole `MEM`). `<root>` = this profile's Claude config dir (`$CLAUDE_CONFIG_DIR`, else `~/.claude`). `TRANSCRIPTS` = the `*.jsonl` session files in the parent folder of `MEM` (default layout; else ask OWNER). `GRAPH` = `python -X utf8 -I "${CLAUDE_PLUGIN_ROOT}/scripts/km_graph_check.py" --mem "${user_config.memory_path}"`.

**Scope:** this profile only; apply `SCOPE` to every candidate.

**Run mode:** on demand only. No Plan Mode (overrides any CLAUDE.md plan-mode rule). Structural fixes are applied without waiting; everything else waits for OWNER's approval of the plan (Step 7).

**Size budget:** this file ≤ 11 KiB.

---

## Step 0 — Load

In parallel:
1. `REF` §Principles
2. `MEM/eval/runs.md` (last line = previous run). Absent = first run, which builds the baseline.
3. `MEM/eval/scorecard.json`, `cases.jsonl`, `retrieval.jsonl`, `contradictions.jsonl` (if present)
4. Always-loaded set: `<root>/CLAUDE.md`, the project's CLAUDE.md files, `MEM/MEMORY.md`
5. `<root>/settings.json` (hooks, allowlist), `<root>/commands/*.md` and `<root>/skills/*/SKILL.md` frontmatter only
6. `MEM/build_backlog.md` (open rows only), `SCOPE` (if set)

Record **always-loaded bytes** (item 4 plus the session's whole skills listing, plugin and built-in included) as the efficiency baseline.

Pre-load `AskUserQuestion` via `ToolSearch` (not in a session started from another session, Step 5).

## Step 1 — Triage (scripted, no LLM calls; every run)

Run the triage script described in `REF` §Triage with `python -X utf8 -I`, from the scratchpad. It scans `TRANSCRIPTS` for sessions since the previous run (cap 60; first run: the 60 newest by mtime; exclude the current session) and emits:

- **Model mix:** per-message `message.model` counts. Flag a **model change** if the dominant model differs from `runs.md`.
- **Rule signals:** violations and corrections per rule slug, attributed to the model of the assistant message they concern (not the session).
- **Friction:** permission prompts and denials, retries, re-explanations, tool errors and workarounds.
- **Usage:** slash-command and skill invocations, memory files read, memory files never read.
- **Load receipt:** per session, `python -X utf8 -I "${CLAUDE_PLUGIN_ROOT}/scripts/km_load_receipt.py" --mem "${user_config.memory_path}" <sessions>` (`REF` §Load receipt). Only `whole` sessions count as evidence for violations, relevance and retirement; list `truncated`/`absent` ones in the report.
- **Case candidates:** corrections not yet in `cases.jsonl` (dedup: rule + session). Candidates only; they never flag on their own (§Triage).

**Graph metrics:** run `GRAPH --json --reachable-excluding-self <every indexed slug>`. Read-only, owned by km; slugs = keys of `bytes_by_slug`. Use its fields as-is: `islands`, `unreachable`, `dead_links`, `feedback_missing`, `bytes_by_slug`, `reachable_excluding_self`, `route`, `route_excluding_self` (hops, path_bytes, via).

**Contradiction candidates:** scripted pairing per `REF` §Contradictions. No LLM at this tier.

Most runs stop here; only Step 2's **flagged** items go further.

## Step 2 — Score and flag

Update the scorecard in memory (not on disk yet) per `REF` §Files. Compare with the previous run. Classify every artifact:

| Signal | Flag |
|---|---|
| Open `cases.jsonl` row or `check` violation on current model | **failing** |
| Re-explained / not found despite existing | **unfound** |
| `basis: compensation`, unvalidated on current model, model changed | **revalidate** |
| `basis: compensation`, no violation on current model across ≥ N relevant sessions | **retire-candidate** |
| Skill or integration with retries, errors or workarounds | **defective** |
| Never loaded or invoked in the window | **idle** (report only; never retire on absence) |
| `islands`, `unreachable`, `dead_links`, `feedback_missing` | **graph** |
| Reachable without own line, ≤ 1 hop, `path_bytes` ≤ cap (§Triage) | **compactable** |
| Candidate pair from §Contradictions | **contradiction?** |

Report **coverage**: share of rules with a deterministic check vs `unknown` (judgment/style rules).

## Step 3 — Probe (flagged items only)

Load `REF` §Probe. Gate first:

- **Context-confound check:** rule probes run ONLY through the bare runner `python "${CLAUDE_PLUGIN_ROOT}/scripts/bare_probe.py"`, never subagents (they inherit CLAUDE.md and MEMORY.md). Run `bare_probe.py --canary --model <id> --leak-marker "${user_config.owner_name}"` (plus any other name only this context holds) once per model under test; `clean` (exit 0) = gate passes; record in `runs.md`. Exit 2 (leak), 3 (no token), 4 (a CLAUDE.md above the working folder; tell the user to set `KM_BARE_ROOT`) or no runner on this OS → skip rule probes; verdicts rest on `cases.jsonl` + transcript evidence, and the plan says so.

If the gate passes, replay ~5 cases per flagged item (with-rule vs without-rule arms, k=3, `--model` always explicit). Write each scenario per §Probe **Scenario rule**: rebuilt from the case's `situation`, never hinting at the rule. Probe only `failing`, `revalidate` and `retire-candidate`.

**Retrieval replay** (citation-grounded control per §Probe, always): replay `MEM/eval/retrieval.jsonl`. Pass = the expected slug, a hub that links to it, or a command or skill file that names it. Sample up to 20, newest first, plus every query affected by a proposed compaction, before and after.

**Contradiction probe** (no confound gate): one LLM read per flagged pair, capped per §Contradictions. Verdicts: contradicts / supersedes / compatible. OWNER picks the winner; never auto-resolve.

**Expand on surprise only:** a rule passing without its text gets more scenarios before it is trusted; a failure cluster pulls in graph neighbours. Ceilings in §Probe; exceeding one asks OWNER.

## Step 4 — Diagnose and propose fixes

Map each flagged item to one cause and its fix:

| Cause | Fix |
|---|---|
| Knowledge missing | Add memory (on-demand node) |
| Knowledge stale | Correct it |
| Memory not found | Reword index or description line |
| Soft rule keeps failing in context | Graduate to script or hook; **delete rule text** |
| Skill defective | Fix or delete skill |
| Scaffolding obsolete | Retire rule to `MEM/dormant/` (reversible) |

Every proposed fix carries a **token delta**: change in always-loaded bytes and in on-demand bytes. Additions to always-loaded context are marked **needs yes**.

Evidence rules:
- A real transcript violation always outranks a replay pass.
- Never retire on replay alone. Never retire on absence of evidence.
- Fixes justified only by model grading are marked as such.

**MEMORY.md compaction (standing first target while MEMORY.md is over its target: 17,000 bytes unless `SCOPE` sets another):**
- Propose dropping or merging index lines flagged `compactable`.
- `compactable` is checked one slug at a time. Re-check the whole drop set together (§Triage) before proposing it.
- First generate a query for every affected slug that has none (§Probe, compaction step 0). A drop is valid only if its replay still passes after the change.
- Report bytes saved against target. Never compact MEMORY.md outside this step.

Also:
- Graph health link batch (cap 15–20 files, remainder logged)
- Allowlist gaps from repeated permission prompts
- Scriptability rows for frequent skills and open backlog items

## Step 5 — Strategic questions

One `AskUserQuestion`, at most 4 questions, for decisions only OWNER can make. In a session started from another session, write them into the plan's `## Decisions needed` instead (a blocking ask stalls the report); e.g. retire N compensations (with evidence), graduate rule X to a hook, accept +N always-loaded bytes, raise a probe ceiling.

Rejected items go into **Known Overheads**.

## Step 6 — Apply structural fixes, then write plan

First apply the structural fixes (Step 7 apply-rules) and, if `MEM` is in a git repo, commit them on its current branch as `chore(km): km-audit YYYY-MM-DD — structural fixes`; re-run `GRAPH` to confirm no new islands, unreachable files or dead links. Then write `<scratchpad>/km-audit-YYYY-MM-DD.md` and open it for OWNER (file pane where the app has one):

```markdown
# KM Audit — YYYY-MM-DD  (model: <id>; first run: yes/no)

## Scorecard
| Metric | Last run | This run | Δ |
| Pass rate (deterministic cases) | | | |
| Retrieval pass rate | | | |
| MEMORY.md bytes (target) | | | |
| Coverage (rules with checks) | | | |
| Always-loaded bytes | | | |
| Cases (total / new / now passing) | | | |
Context-confound check: <passed / failed → probes skipped>

## Findings (flagged items)
| Artifact | Flag | Evidence (session, model) | Cause | Proposed fix | Token Δ (always / on-demand) | Basis of verdict (transcript / replay / model-graded) |

## Compaction · Retirements · Graduations · Fixes · Allowlist / Graph / Scriptability · Known Overheads
## Net always-loaded change: <±N bytes>
## Draft content
```

## Step 7 — Await approval

- **Approved** → Step 8.
- **Revision** → edit the plan with track-changes markup and re-surface it.
- **"cancel"** → keep the plan; still write eval state (new `cases.jsonl` rows, `runs.md` line).

**Apply-rules:** structural fixes are auto-applied in Step 6, before the plan, and listed in it as *applied* (revert = `git revert` that commit): dead/missing links, index lines whose drop keeps reachability and passes retrieval replay, stale paths verified on disk, frontmatter tags. Anything that changes what a rule says (merge, trim, rewrite), retirements, new hooks or scripts, and CLAUDE.md edits need OWNER's yes.

## Step 8 — Execute

1. Apply approved fixes (structural ones are already in, Step 6) in order: retirements → graduations → corrections → additions. Graduations delete their source text in the same commit.
2. Write `eval/` state per `REF` §Files (cases, scorecard, contradictions, `runs.md` line). In `retrieval.jsonl` the audit marks results and appends its generated queries.
3. Update MEMORY.md for any added, renamed or retired node. `MEM/eval/` is never indexed.
4. Append to `MEM/log.md`: `YYYY-MM-DD | km-audit | N fixes, N retired, N graduated; net always-loaded Δ; islands remaining`.
5. Commit only the paths changed, on the memory repo's current branch. Do not push unless OWNER says so.
6. Output: every file written, scorecard delta, net always-loaded change.

## Key rules

- **Owner words only.** Tool-result wording needs OWNER's approval, shown with its source (`schema.md` A7).
- **Escalate spend only on surprise.**
- **Retiring obsolete scaffolding is a primary output.** Dormant, not delete.
- **No duplicates after graduation.** A rule enforced by a hook or script loses its text.
- **Idle commands:** flag; delete only with per-item approval.
- **This profile only.** Another profile gets its own run from a session there.
