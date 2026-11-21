---
name: reference_backup_script
description: "Weekly backup of the logger's local buffer to an external drive — schedule, target, how to check it ran"
metadata:
  node_type: memory
  type: reference
---
**Related:** [[reference_tools]]

`~/greenhouse/backup.sh`, Sundays 03:00 via cron. Writes `buffer-YYYY-MM-DD.tar.gz` to the drive mounted at `/mnt/backup`. Check: the newest file's date is within 7 days.
