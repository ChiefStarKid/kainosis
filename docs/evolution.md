# Evolution

Dated changes that shaped the design, each with the constraint behind it (see the constraint table in the [README](../README.md#who-it-is-for)). Short by design; the full history is on the Roadmap.

| Date | Change | Constraint |
|---|---|---|
| 2026-04-04 | Karpathy publishes the LLM Wiki gist: LLM-maintained wiki, index, log, lint. | — |
| 2026-07-06 | A planned second tier of sub-index files between MEMORY.md and the leaves sat unwired for weeks; deleted. The index became hub-and-spoke: MEMORY.md links hubs, hubs' `Cluster:` lines link spokes. | Small token budget |
| 2026-07-08 | Close-out plan gate removed; the Q&A round is the confirmation step. | Small token budget |
| 2026-07-20 | Only `[[ ]]` wikilinks count as graph links; group hubs gained a `Members:` line after ~40 members read as islands. | — |
| 2026-11-20 | Objective reset: context efficiency first, and eval asks "does the current model still need this rule?". Added `basis` tags, `eval/cases.jsonl`, the lean pre-compact run, targeted reads (the old full read of the graph exceeded the context window), and `km_graph_check.py`. | Can't always use the best model; small token budget |
| 2026-11-20 | Audit redesigned around triage → probe → retire. First run: MEMORY.md 20,580 → 15,316 bytes, unreachable files 8 → 0. | Small token budget |
| 2026-11-20 | First rules-separation pilot on one 9-rule cluster: rules moved to their point of use, a read-only checker, a hook; one retired. | Small token budget |
| 2026-11-21 | Bare-context probe runner: subagents inherit memory, so they can't be the without-rule arm. | Can't always use the best model |
| 2026-11-21 | Rules pass: every feedback file tagged with `basis`; rules retired on probe evidence; 11 rules graduated into a reminder hook. Apply-rules fixed: structural fixes auto-apply, rule changes need a yes. | Can't always use the best model |
| 2026-11-21 | Sources by reference: the graph stores pointers, repairs them on use, never copies or reorganises sources. | No control over repositories; locations change |
| 2026-11-21 | v0.1 packaged as a Claude Code plugin: namespaced skills, per-profile config through `userConfig`. | Separate profiles; generic names collide |
