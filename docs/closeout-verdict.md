# Close-out verdict

Definitions for the close-out verdict that `km` ends every run with. `skills/km/SKILL.md` holds the short steps; this page holds the formats and rules. A full run reads it at Step 9; a lean run never opens it (the skill carries the lean rules).

**Purpose.** OWNER archives, deletes or compacts a thread on the strength of close-out. The verdict turns that into a checked decision. It is also the input for session grooming: **only sessions whose last close-out verdict is SAFE are archive or delete candidates.** NOT SAFE, lean verdicts and sessions with no verdict are never candidates.

## The pieces (full run)

1. **Disposition ledger.** Every capture candidate (Round 1, Round 2 and case candidates, Round 3 items, Round 4 discards, reverse-sweep finds) gets exactly one disposition:
   - `written`: new file created.
   - `merged`: folded into an existing file (Behaviour B), or `supersedes:` set.
   - `rejected`: OWNER dismissed it, or it routed to `drop`.
   - `deferred`: not done now; it names where it lives (a `build_backlog.md` row, an issue, a file) or is carried over.

   Format, one row per candidate: `# | candidate | disposition | where (file, row, issue) | claim verified (evidence)`.
2. **Loose-ends sweep.** Things outside memory that still matter if this thread disappears: unsent drafts, files written outside `MEM` (deliverable, scratch or unsaved work), uncommitted or unpushed changes, running processes or background tasks, child or linked sessions still working, scheduled items that point at this thread, a failed push or commit from Step 8. Each is `clear`, `tracked` (names where) or `open`.
3. **Carry-over list.** What the next session must pick up and exists only in this thread: paths, IDs, URLs, names, numbers, pending actions. Each item: `what — where it lives now`. An item with no home outside the thread is `unanchored`.
4. **Reverse sweep.** After the forward scan, re-read the session once more from the last turn back to the first, looking only for anything that matters and is not in the ledger, loose ends or carry-over (a decision, a path, a pending action, a correction). Each find is added as a candidate, a loose end or a carry-over item. It must say how it ran ("re-read N turns, M finds"). This is what makes "nothing was lost" a checked claim.
5. **Verdict.** One line, `SAFE` or `NOT SAFE — <reasons>`.

## Verdict rules

**Never issue SAFE on an unverified claim.** A claim is any statement the verdict leans on: "written" (the file exists with the content), "committed" or "pushed" (the commit or remote ref exists), "sent" or "saved" (the item exists), "not running" (the process is gone), "deferred to X" (X exists). Verified means one local read-only call in this run confirmed it, and the ledger names the evidence. Not checked, not checkable here, or not run yet → the claim is unverified.

`SAFE` requires all of:
- every candidate has a disposition; `written` and `merged` rows have verified evidence; `deferred` rows have a home;
- the reverse sweep ran and everything it found is reconciled;
- no loose end is `open`; `tracked` ones name where;
- no carry-over item is `unanchored`;
- no claim is unverified.

Otherwise `NOT SAFE — <reason per blocker, with the action that clears it>`. OWNER may accept a blocker explicitly ("accept: unsent draft is scratch"); it is then marked `accepted by OWNER` in the ledger and no longer blocks. Claude never accepts on OWNER's behalf.

SAFE means safe to archive, delete or compact. NOT SAFE prints "KM close-out written — thread NOT yet safe to close" instead of "KM close-out complete."

## Zero-candidate checkpoint

If the forward scan and the reverse sweep produce no candidates and no case, `AskUserQuestion` before Step 4: **Verdict only (Recommended)** or **Full run**. Verdict only skips the Q&A rounds, the Behaviours and the Step 6 summary; it still runs the reverse sweep and the loose-ends sweep (they back the verdict), and prints the short form:

```
Disposition ledger: none (zero candidates)
Reverse sweep: re-read N turns, 0 finds
Loose ends: <list or none>
Carry-over: <list or none>
VERDICT: SAFE | NOT SAFE — <reasons>
```

A loose end or carry-over item does not force the full run, but a find the owner wants captured does: offer it. There is no "never partial" rule: the owner chooses the run, and `km lean` stays a cheaper owner-chosen run.

## `km lean` and the verdict

Decision: **lean never issues `SAFE`.** It may issue `SAFE TO COMPACT` or `NOT SAFE TO COMPACT`, and nothing about archiving or deleting.

Why:
- Lean skips the reverse sweep and the loose-ends sweep (that is what makes it cheap), so it cannot back a claim that nothing outside memory was lost.
- A non-empty Keep line means content lives only in this thread. Deleting it loses that content; compacting does not, because the Keep line carries it.
- Even with an empty Keep line, the unrun sweeps mean the absence of loose ends is unchecked, which the never-SAFE-on-unverified rule forbids.

`SAFE TO COMPACT` requires: every candidate in the lean ledger has a disposition with verified evidence for `written`/`merged` rows, every `thread` item is in the Keep line, and no claim is unverified. The line states what it did not check: `SAFE TO COMPACT (lean: no reverse sweep, no loose-ends sweep; not an archive/delete verdict)`. For archive or delete, run a full `km`.

## Worked example: an unverified claim

Session: OWNER corrected a send-mode rule; one candidate was `written`, one `merged`, one `deferred`.

| # | candidate | disposition | where | claim verified |
|---|---|---|---|---|
| 1 | confirm before bulk delete | written | `feedback_confirm_bulk_delete.md` | yes: file exists, `GRAPH --reachable` ok |
| 2 | reply-all default | merged | `feedback_reply_all.md` | **no**: Step 8 write was never re-read |
| 3 | build a retry wrapper | deferred | `build_backlog.md` row | yes |

Reverse sweep: re-read 41 turns, 1 find (a path OWNER pasted, now carry-over, anchored in the backlog row). Loose ends: none. Result:

`NOT SAFE — row 2 claims "merged" but the edit was not re-read this run. Clear it: read feedback_reply_all.md and confirm the merged text.`

After the read confirms it, the same ledger gives `SAFE`. `tests/test_km_verdict.py` runs exactly this case (fixtures in `tests/fixtures/verdict/`) plus the other rules above. Step 9 runs `scripts/km_verdict_check.py` on a ledger the model writes as JSON (fields in the script's docstring). The script checks the rules above, plus what is file-backed when given `--mem`: a row's `file` exists, the recorded commit exists (`git cat-file -e`), written paths are committed with no pending change. A full or verdict-only ledger must quote the `Full-load marker` from `docs/km-full.md` as `full_loaded_marker`, or the verdict is `NOT SAFE`; a lean ledger needs none. It cannot check a draft sent, a process gone or a deferred home outside memory: it lists those as `Model-verified`, and the model must have checked each with a read-only call. The script is stdlib only and read-only.

## Data handling

No new data is read or written. The ledger and verdict are shown in the chat; the only files `km` writes are the ones it already wrote.
