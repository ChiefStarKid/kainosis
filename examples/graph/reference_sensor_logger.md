---
name: reference_sensor_logger
description: "Greenhouse sensor logger — device IDs, sampling interval, where readings land; for any question about sensor data or a missing reading"
metadata:
  node_type: memory
  type: reference
---
**Related:** [[project_greenhouse]] · [[reference_tools]] · [[feedback_celsius_readings]]

Script `~/greenhouse/logger.py` on a single-board computer in the shed. Two sensors: `gh-1` (bench), `gh-2` (roof). Every 10 minutes it appends one row per sensor to the readings sheet ([[reference_greenhouse_sheet]]). A missing row usually means the shed Wi-Fi dropped; the logger buffers up to 24 hours and backfills.
