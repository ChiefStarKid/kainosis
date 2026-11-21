---
name: feedback_celsius_readings
description: "Sensor readings are integers in tenths of a degree Celsius (215 = 21.5 °C) — before quoting, charting or alerting on any temperature"
metadata:
  node_type: memory
  type: feedback
  basis: fact
---
**Related:** [[index_feedback]] · [[reference_sensor_logger]]

Divide the `temp` column by 10 before reporting it.

**Trigger:** any temperature from the readings sheet or logger output.
**Why:** a model can't know this firmware convention; it is not visible in the data.
**How to apply:** convert, and state the unit (°C) in every answer.
