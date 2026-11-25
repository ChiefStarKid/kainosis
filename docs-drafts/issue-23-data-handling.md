# Draft: Data handling text for the auto km lean gate (for the roadmap owner to place)

Not edited into CHANGELOG.md, PRIVACY.md, plugin.json or README.md.

## CHANGELOG "Data handling" line

- `scripts/km_auto_gate.py` can write memory files without asking, only when you pass `--opt-in`. It writes new notes, appended or inserted lines and one-line fact fixes in your memory folder, and a run folder under `eval/auto_runs/`. It never edits `MEMORY.md`, never runs git, never pushes, and makes no network request. Text from tool results is never written automatically.

## PRIVACY.md text

**Automatic memory edits (opt-in).** When you run `km_auto_gate.py apply --opt-in`, the script reads your memory folder and a list of proposed edits you supply, and writes the edits that pass its checks into the same folder, with a record of the run in `eval/auto_runs/`. It is off by default and not yet called by any skill. It does not edit `MEMORY.md`, does not commit or push, does not read anything outside the memory folder except the single path or file named by a fact check, and sends nothing over the network.
