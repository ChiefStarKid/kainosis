# Issue #8 (load receipt): data-handling wording (draft, not applied)

**CHANGELOG, "Data handling" line:**
> Load receipt: reads the same session transcripts triage already reads (the loaded-instructions attachments and first few messages) and `MEMORY.md`. No new data source; nothing is stored or sent beyond the audit report's per-session `whole / truncated / absent / unknown` status and hub count. If you pass `--history`, the script also runs read-only `git log` and `git show` in your memory repo to read the earlier `MEMORY.md`; it writes nothing and contacts nothing.

**README / PRIVACY.md (only if either lists what km-audit reads):**
> km-audit's triage also checks, per session, whether `MEMORY.md` was loaded whole. It reads the loaded-instructions entries of the session transcripts it already scans; session ids and a status appear in the local audit report. With the optional `--history` flag it also runs read-only `git log`/`git show` in your memory repo to compare against the earlier index. Nothing leaves your machine.

Credit: idea from [Link](https://github.com/gowtham0992/link) by gowtham0992.
