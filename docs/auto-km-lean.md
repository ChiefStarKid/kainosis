# Auto km lean: the gate (first slice)

`scripts/km_auto_gate.py` decides, for each proposed memory edit, whether it is safe to apply without asking. Anything that fails a gate or cannot be judged is held for you. This slice is the gate and the digest only. It is **not wired into `km` yet**: you run it by hand, and it is off unless you pass `--opt-in`.

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

A `fix_fact` also needs a read-only check (a path that exists, or a file that contains the value), and the checked value must appear in the new text.

Approving a held edit (`--approve <id>`) skips the gates but never the structural checks: the path stays inside the memory folder, an anchor or old text is found exactly once, a file to edit exists and a file to create does not. Approved edits are marked as such in the digest.

## The digest

Each run writes `digest.md` with: what was applied (one revert command each), what is held and why (with its approve command), options that were not recommended, warnings (for example a created file nothing links to yet), and a prepared `git add` and `git commit` that are printed, not run. You commit.

## Tests

`python tests/test_km_auto_gate.py` builds a synthetic memory folder from `tests/fixtures/auto_gate/` and checks 18 edits against their expected decisions, that `gate` writes nothing, that `apply` refuses without `--opt-in`, that a CRLF file stays CRLF, that revert restores bytes exactly, and that approval applies a held edit.

Hit-rate figures for the proposal step live on issue #23.
