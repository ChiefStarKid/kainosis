# Draft: Data handling text for issue 37 steps 3-6 (for the roadmap owner to place)

Not edited into CHANGELOG.md, PRIVACY.md, plugin.json or README.md.

## CHANGELOG "Data handling" line

- Two new scripts. `scripts/km_lint.py` is report-only: it reads the top-level memory files you name (or all of them) and checks that each path it finds in a code span exists on this machine; it writes nothing and makes no network request. `scripts/km_commit.py` is run at the end of a close-out: it runs `git` in your memory folder (status, add, commit) on exactly the files the run wrote, creates one local commit, and never pushes. `km_graph_check.py` gains a first output line, `preflight:`, and still only reads. The commit step and the closing block moved from the skill text into the script; the push stays in the skill and still follows your scope file or your instruction.

## PRIVACY.md text

**Local checks and commits.** `km_lint.py` reads memory files and tests whether paths mentioned in them exist; it reports and changes nothing. `km_commit.py` stages and commits the named memory files in the memory folder's own git repository when there is one; it never pushes, never stages other files, and sends nothing over the network. The commit subject contains the close-out topic you confirmed.

## Design note: why the commit can live in a script (issue 37 step 4)

The reasons #30 gave for keeping the commit in the skill, and how the script meets each:

- **Ordering.** The script is the last call that writes, after `km_close.py` and the lint. It takes the same input JSON as `km_close.py` and the `file:` paths it printed, so the commit cannot precede an append.
- **Scope-file push rules.** The script never pushes and has no push code. The branch, the permission and the "never force-push, never to the default branch" rules stay in the skill, which pushes after the script and then sets the `Pushed:` line.
- **Failure visibility in Step 9.** A git failure prints `Committed: FAILED: ...`, exits 1, and ends with `commit: null`. The Step 9 ledger quotes that value and `km_verdict_check.py` checks the commit and the written paths against git, so a failed or skipped commit cannot be reported as SAFE.
- **Other sessions' work.** Paths are explicit and `git commit -- <paths>` limits the commit to them, so changes another session staged in the same repository are not swept in. `.`, `-A`, globs, directories, absolute paths and paths outside the memory folder are refused with nothing staged.

## Not verified live

Whether the script paths expand in the skill body at run time (`${CLAUDE_PLUGIN_ROOT}`, `${user_config.*}`) is unchanged from issue 37's open list; the `preflight:` STOP line is the visible symptom if `memory_path` arrives empty or unexpanded.
