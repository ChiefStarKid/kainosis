# Issue #8 (load receipt): data-handling wording (draft, not applied)

**CHANGELOG, "Data handling" line:**
> Load receipt: reads the same session transcripts triage already reads (the loaded-instructions attachments and first few messages) and `MEMORY.md`. No new data source; nothing is stored or sent beyond the audit report's per-session `whole / truncated / absent` status and hub count.

**README / PRIVACY.md (only if either lists what km-audit reads):**
> km-audit's triage also checks, per session, whether `MEMORY.md` was loaded whole. It reads the loaded-instructions entries of the session transcripts it already scans; session ids and a status appear in the local audit report. Nothing leaves your machine.

Credit: idea from [Link](https://github.com/gowtham0992/link) by gowtham0992.
