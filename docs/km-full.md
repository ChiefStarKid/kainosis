# km — full-run steps

Steps that only a full `km` run performs, moved out of `skills/km/SKILL.md` so a `km lean` run (right before `/compact`) does not load them. A full run reads this file at Step 1, before Step 2. A lean run never opens it. Step numbers match the skill. Names (`OWNER`, `MEM`, `GRAPH`, `SCHEMA`, `VERDICT`) are defined in the skill.

Full-load marker: `km-full-v1-3b-r34-s6-s9`. The Step 9 ledger of a full run quotes it as `full_loaded_marker`; `scripts/km_verdict_check.py` answers `NOT SAFE` without it.

A full run reaches `SAFE` only after Step 3b, Round 3, Round 4, Step 6 and the Step 9 loose-ends sweep and carry-over list have run.

## Step 3 addition — Round 4 candidate reads

Full run only: also read the files you will name as Round 4 discard candidates. Source those from `GRAPH` signals (unreachable, dead links), contradictions seen in this conversation, supersession by CLAUDE.md, and log.md recency. Never a full read.

## Step 3b — Reverse sweep

Re-read the conversation last turn to first for anything that matters and is not yet a candidate or carry-over item (decision, path, pending action, correction). Add each find. Report "re-read N turns, M finds".

**Zero-candidate checkpoint** (trigger: the skill, Step 4). Ask via `AskUserQuestion`: **Verdict only (Recommended)** or **Full run**. Verdict only skips Steps 4–8; it runs the loose-ends sweep, then Step 9 (short form: `VERDICT`). Full run goes on with every operation "None", still records cases and still reports C and F. The owner picks the run.

## Step 4 — Rounds 3 and 4

Asked in the same `AskUserQuestion` flow as Rounds 1 and 2 (rules in the skill's Step 4).

- **Round 3 — Workflow & Build.** Changes to how future sessions run (skills, scripts, commands, config, triggers), and items worth building or automating, prefixed **[BUILD]**. Plus "No workflow changes needed". Workflow items are flagged in the summary, not executed. [BUILD] items go to `build_backlog.md` in Step 8.
- **Round 4 — Discard.** "Which of these memory files should be deleted or retired?" One option per candidate with a one-line reason. Plus "Keep everything".

## Step 5 — Behaviours (full halves)

- **A — Stale review.** On files read this run:
  - `project`: stale if concluded or superseded
  - `reference`: stale if a path or URL is no longer current
  - `feedback`: only if explicitly contradicted this session
  - `user`: only if directly contradicted

  Propose UPDATE or DELETE. The repo-wide stale sweep belongs to km-audit.
- **C — MEMORY.md budget, full run.** At ≥170 lines, propose merges or trims from the index lines already in context. (Lean half and the shared index-line rule: skill, Behaviour C.)
- **F — Graph health, full run.** Report density, islands, unreachable files and dead links, and propose a fix for each, reading only the files involved. (Lean half and the inbound-link rule: skill, Behaviour F.)

## Step 6 — Summary

Assemble this; write it to a file only if a DELETE is ambiguous or OWNER asks.
- Summary (1–3 sentences)
- CREATE / UPDATE / DELETE tables (file, type or change or reason), or "None"
- MEMORY.md line count and budget status
- Why/basis completeness
- Verification Gate (fact | file | check | result)
- Graph Health (density, islands, unreachable, dead links)
- Workflow Suggestions (flagged, not executed)
- Build Backlog additions
- Cases and retrieval queries recorded
- Draft content for each CREATE, in the file format of `SCHEMA` (A1 frontmatter, A4 body): `name`, `description`, `metadata.node_type`, `type`, `basis` for feedback; a `**Related:**` hub link; the rule or fact first; `**Trigger:**`, `**Why:**`, `**How to apply:**`.

## Step 9 — Loose-ends sweep, carry-over list

Run before the verdict. Formats in `VERDICT`. A full run cannot issue `SAFE` unless this sweep and the carry-over list have run.
