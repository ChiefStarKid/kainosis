---
name: project_greenhouse
description: "Hub for the backyard greenhouse automation project — sensor logging, the readings sheet, seed ordering; start here for any greenhouse question"
metadata:
  node_type: memory
  type: project
---
**Cluster:** [[reference_sensor_logger]] · [[reference_greenhouse_sheet]] · [[project_seed_order]] · [[feedback_sheet_read_before_write]]

Goal: keep the greenhouse between 18 and 27 °C without daily checks. Status: logging live since 2026-05-02; automatic vent control not started.

| Decision | Date |
|---|---|
| Log every 10 minutes, not every minute (sheet row limit) | 2026-05-02 |
| Readings stay in the owner's sheet; the graph stores only its location | 2026-05-02 |

**Trigger:** any question about the greenhouse, its sensors or its data.
**Why:** one entry point keeps the index to one line for the whole project.
**How to apply:** open this hub, then the one spoke the question needs.
