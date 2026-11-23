# Draft: CHANGELOG "Data handling" line for issue #19 (close-out verdict)

For the roadmap owner to paste into CHANGELOG.md. Not applied here.

> **Data handling:** no new data is read or written. The close-out ledger, loose-ends sweep, carry-over list, reverse sweep and SAFE / NOT SAFE verdict are shown in the chat only; `km` still writes only the memory files, `eval/` lines and `log.md` entry it wrote before. The verdict checks use read-only local calls (file exists, `git log`, process list) already within what `km` does.

Check before release: PRIVACY.md needs no change if the lines above hold. If a later change persists the verdict (for example a `log.md` field for session grooming, #3), that is new data written and needs its own line.
