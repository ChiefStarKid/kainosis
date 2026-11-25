# Auto km lean: the gate (first slice)

`scripts/km_auto_gate.py` decides, for each proposed memory edit, whether it is safe to apply without asking. Anything that fails a gate or cannot be judged is held for you. You can run it by hand (it is off unless you pass `--opt-in`) or through `km lean auto`, below.

## What it does

- `gate` reads a list of proposed edits and prints APPLY or HOLD for each one. It writes nothing.
- `apply --opt-in` writes only the APPLY edits, plus a run folder `eval/auto_runs/<run>/` with `manifest.json`, `digest.md` and `held.json`.
- `revert` undoes one applied edit. It refuses unless the text it added is still there exactly once (a created file: unless its bytes are unchanged).

It never runs git, never pushes, and never touches the network.

## The gates

Edits are checked one after another against a temporary copy of the memory folder, so edits to the same file stack.

| Gate | Rule |
|---|---|
| Kind | Only `create`, `append`, `insert_line` and `fix_fact`. Delete, move, rewrite and supersede are held. |
| Reachability | A stored retrieval query whose expected file was within 2 hops of `MEMORY.md` must still be. No file becomes unreachable, no new dead link, no link removed. With no stored queries, `insert_line` and `fix_fact` are held because they cannot be checked. |
| Protected | `MEMORY.md` is never edited (new index lines wait for you). The frontmatter block of an existing file stays byte-identical. |
| Never automatic | Rule files that touch sending, deleting or publishing. Added text that weakens a rule ("no longer", "skip", "unless", ...). A source other than your own words (for example text from a tool result). Edits over 1,500 characters. |
| Recommended | An edit not marked recommended is held and listed in the digest as an option. |

A `fix_fact` also needs a read-only check (a path that exists, or a file that contains the value). The checked value must be at least 4 characters, appear in the new text and not in the old text. A `fix_fact` never edits a rule file.

Approving a held edit (`--approve <id>`) skips the gates but never the structural checks: the path stays inside the memory folder, an anchor or old text is found exactly once, a file to edit exists and a file to create does not. Approved edits are marked as such in the digest.

## Limits

- `source: owner` is a label the proposer sets; the gate cannot verify it. The owner-words-only rule rests on whatever builds the edit list.
- The sending and weakening checks are word lists. A softened rule that avoids those words passes them, so they reduce risk and are not airtight. The reachability and frontmatter gates do not depend on them.
- `apply` refuses, and writes nothing, if a file it would change was edited after the run started. The revert record is written before any memory file changes.
- Created files are written with LF line endings, even in a CRLF folder.

## The digest

Each run writes `digest.md` with: what was applied (one revert command each), what is held and why (with its approve command), options that were not recommended, warnings (for example a created file nothing links to yet), and a prepared `git add` and `git commit` that are printed, not run. You commit.

## Wiring: `km lean auto`

`km lean auto` is a lean run (see the km skill) where memory edits that pass the gate are written without a question. The word `auto` in the command is the opt-in; typing plain `km lean` never writes unasked. Steps, in the km skill's Step 4:

1. Run Behaviours D, E and G on each candidate's text as usual, then write one edit per candidate that is a new file, an appended or inserted line, or a one-line fact fix, into a temp edits file (format in the script header). `source` is `owner` or `owner_paraphrase` only for candidates from OWNER's own turns; a candidate tagged `[from <source>]` is not an edit, it is asked as today. Set `recommended: true` only for candidates you would pre-flag "(Recommended)". New index lines are not edits. The retrieval query for each new file is an `append` edit to `eval/retrieval.jsonl`.
2. `gate`, then `apply --opt-in --run-id <timestamp>`. Show OWNER the applied list with its one-line summaries and the held list with reasons.
3. Round 1 and 2 (one call) cover only the held and not-recommended candidates, plus cases and the correction question. A yes to a held edit is applied with `apply --edits <run>/held.json --opt-in --approve <id>`. Everything else confirmed is written as in Step 8; skip what the gate already wrote.
4. Behaviour H still runs. Step 8 commits once, covering the run folder too. The Step 9 ledger marks gate-applied edits `written` with the run's digest as where, and the verdict stays `SAFE TO COMPACT` / `NOT SAFE TO COMPACT`.

## Tests

`python tests/test_km_auto_gate.py` builds a synthetic memory folder from `tests/fixtures/auto_gate/` and checks 18 edits against their expected decisions, that `gate` writes nothing, that `apply` refuses without `--opt-in`, that a CRLF file stays CRLF, that revert restores bytes exactly, and that approval applies a held edit.

Hit-rate figures for the proposal step live on issue #23.
