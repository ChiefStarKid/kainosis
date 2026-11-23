# Draft: data-handling note for issue #20 (for the roadmap owner to place)

Not applied to CHANGELOG.md or PRIVACY.md; those belong to the roadmap-owner session.

## CHANGELOG (Unreleased → Added)

- `km-audit`: new compaction fix type, **restructure index into theme hubs**. A stdlib script (`scripts/km_index_restructure.py`) proposes grouping the feedback lines of an oversized `MEMORY.md` into a few hub files, keeping each one-line description verbatim, and replays reachability before and after. Any pass-to-fail, altered description or lost slug blocks it. It writes only to a scratch folder until the owner says yes.
- `km-audit`: a `truncated` load receipt now outranks the 17,000-byte target as the first finding.
- `km-audit` Step 0: after a rename, flags stale command names and non-existent paths in the owner's CLAUDE.md files (report only).

## PRIVACY.md (data handling)

- **CLAUDE.md check (new read of content).** The audit already opens the owner's CLAUDE.md files in Step 0 to count always-loaded bytes. The stale-name check now also searches their text for renamed command/skill names and tests whether the paths they name exist on disk (existence check only; no other file is opened). Results appear in the local audit plan; nothing is sent anywhere, and CLAUDE.md is never edited without the owner's yes.
- **Restructure writes only on the owner's yes.** `propose` and `replay` are read-only on the memory folder (the candidate goes to a scratch folder). `apply` refuses without `--owner-approved`, re-runs replay first, and then writes only `MEMORY.md` and new `index_feedback_<theme>.md` hub files in the memory folder. The change is a normal commit, reverted with `git revert`.
- No network access, no new data leaves the machine.
