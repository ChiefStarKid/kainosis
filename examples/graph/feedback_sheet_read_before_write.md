---
name: feedback_sheet_read_before_write
description: "Before any write to a live spreadsheet, read its header row and target range first — no blind appends; applies to the readings sheet and any other"
metadata:
  node_type: memory
  type: feedback
  basis: compensation
---
**Related:** [[index_feedback]] · [[reference_greenhouse_sheet]]

Read the header row and the last 5 rows of the target tab before writing. Write only to `raw`, never to a formula tab.

**Trigger:** any append or update to a live spreadsheet.
**Why:** a blind append once wrote readings into the `daily` formula tab and broke its totals (case 2026-05-02).
**How to apply:** read, confirm the columns match, then write; on mismatch, stop and ask.
