# Structure rules

Read by `km` before it creates a wiki, briefing or context-retention file for Claude, adds a file for a script, tool or integration, or finds a child CLAUDE.md. Moved out of `skills/km/SKILL.md` to keep that file small (it loads on every run).

- **Hub-and-spoke for Claude wikis.** Any wiki, briefing or context-retention file meant for Claude (not human reading) is `index.md` (10-15 lines: topic, filename, load trigger) plus one self-contained node per concept (<50 lines, wikilinks). Never one monolithic file. A project hub is the coordinator: decisions table, status, open questions, file map, corrections log; one spoke per workstream. Restructuring: build the new set in a subfolder; OWNER retires the old.
- **One memory file per component.** Separate scripts, tools or integrations get separate files unless they share code, DOM or API surface.
- **No child CLAUDE.md.** A CLAUDE.md in a subdirectory only loads when Claude Code is rooted there. Consolidate it into a memory file, update the index, then delete it (ask first).

The scope rule is in `scope-rule.md`.
