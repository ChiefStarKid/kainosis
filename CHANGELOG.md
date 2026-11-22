# Changelog

Versions follow `plugin.json`. Installed copies update only when the version is bumped.

Any change to what the plugin reads, writes or sends is listed under **Data handling** in its release, and [PRIVACY.md](PRIVACY.md) is updated in the same release.

## 0.1.0

First public release.

- `/kainosis:km` and `/kainosis:km lean`: session close-out to a hub-and-spoke memory graph; corrections recorded as eval cases.
- `/kainosis:km-audit`: re-tests rules on the current model, retires the ones it no longer needs, compacts the index within a byte budget.
- `scripts/km_graph_check.py`: graph health (islands, unreachable files, dead links, path bytes).
- `scripts/bare_probe.py` and `bare_probe_token_setup.py`: bare-context rule probes (Windows only).
- `examples/graph/`: fictional sample graph.

**Data handling:** as described in [PRIVACY.md](PRIVACY.md).
