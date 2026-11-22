# Issue #12: supersedes field. CHANGELOG draft

**Data handling:** adds one optional frontmatter field (`supersedes:`) in memory files. No new data read or sent.

Suggested Added line: `supersedes:` frontmatter field, written by `km` when a close-out replaces a node; `km-audit` skips contradiction pairs it resolves but still lists them; `km_graph_check.py` reports a missing target as a dead link. Idea from [Link](https://github.com/gowtham0992/link) by gowtham0992.
