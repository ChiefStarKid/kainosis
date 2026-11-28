# PRD: Close-out across parent and child sessions: each thread closes itself, the parent routes the questions

Issue: https://github.com/ChiefStarKid/kainosis/issues/13 · Stage: Later · Labels: roadmap, km, data-handling

## Problem
With several sessions running, one piece of work is split across a parent and its children. Closing out goes wrong in these ways:
- The owner has to open every child to answer its questions, so many threads need attention at once.
- If the parent and a child both run `km`, they can suggest different things for the same work, and lessons are captured twice.
- A child archived without a close-out loses its corrections.
- Sessions share one git index, so one commit can sweep up another's unfinished files, and stale whole-file rewrites can overwrite newer memory (the commit half is #34 requirement 6).
- A parent that summarises a child's corrections retypes the owner's words, so the wording and the case details drift. This was seen in practice.

## Principle
The parent and the child hold different information and do different jobs. Neither replaces the other. The thread that did the work holds its own transcript, its own exact words and the right model, so **that thread runs its own close-out**. The parent holds the view of the whole family, so it **decides where the owner is asked and in what order**. It does not process the child's content.

## Goal
Each thread is closed out exactly once, in the thread that did the work. When the parent leads, the owner answers every question screen in the parent.

## Non-goals
- A parent reading a child's history, or retyping a child's candidates or cases. A parent's message never supplies a rule, a case or a candidate (#10 stays).
- Auto-confirming any candidate. The owner's answer is still the only confirmation (the gate from #23 is the model for what may apply without one).
- Finding a rule that recurs across several children. That is a later addition.

## Modes
Two ways to start the same run. The run itself is the same in both: the child does the work, writes, commits.
1. **Child-led.** The owner types `km` in a child. The child runs the full close-out with its own question screens, then reports a status line to its parent.
2. **Parent-led.** The owner asks the parent to close out its children. The parent triggers a child, relays that child's question screens to the owner as its own, and returns the owner's chosen labels to the child. The child continues, writes and reports.

A session with no parent and no child runs as today. If the parent cannot be reached, a child asks locally.

## Requirements
1. **Question relay.** In parent-led mode a child sends its questions to the parent as structured text: question, options with their tags, and whether multiple choice. It then stops and waits. The parent shows them as its own question screen and sends back the labels chosen, and the child resumes. The child accepts only labels it offered; any other reply is treated as no answer and the child asks locally.
2. **A relay confirms or dismisses; it never adds.** Rules, cases and candidates come only from the owner's own typed words in the child's own transcript (#10). The relayed answer is a weaker guarantee than a local one, since the child cannot tell who sent it; the docs say so.
3. **Covered marker.** When a run ends, the child writes a short status file to a path the caller names, outside the memory folder: session id, date, last turn covered, verdict, counts of files written and cases recorded, and the plugin version loaded. It extends the #34 result file, which is the trigger and result half of this issue.
4. **Skip what is covered.** The parent lists its children and skips any with a valid marker. A missing or invalid marker means not covered. A child that kept working after its marker is eligible again for the turns after the recorded one.
5. **Order only for dependencies.** Children that do not depend on each other may run together; their question screens queue in the parent and the owner answers one at a time. The parent orders runs only where it knows of a dependency (one child's decision changes what another should capture). The parent never has to order runs for correctness.
6. **Memory lock.** A child takes a lock in the memory folder before it writes, re-reads the files that overlap its candidates, then writes and commits only the paths it wrote (#34 requirement 6), and releases the lock. A second child that wants the same rule updates the file the first created instead of creating a duplicate (the existing update-before-create rule). Without a parent the lock is the solo fallback.
7. **Which thread asks.** Remove the "ask which thread owns KM" step. Mode follows how the owner started the run.
8. **Tests.** A relayed reply with a label that was not offered is rejected; a child that gets no reply asks locally; a child with a valid marker is skipped; two children writing the same rule give one file; the lock is released after a failed write.

## Data handling
No cross-session reading: each child reads only its own conversation. The relay sends question text and chosen labels between the owner's own sessions. The status file holds slugs, file names and counts, with no transcript text. Needs a CHANGELOG 'Data handling' note, the PRIVACY.md sentence, and a check against the directory policy on cross-session messages before release. This replaces the earlier plan to read other sessions' chat history.

## Risks and open questions
- **Not yet tested:** a child pausing at a question, stopping, and resuming on the parent's reply. Messages between sessions are already used for handoffs, but a pause inside a close-out has not been run. If it does not resume cleanly, a child asks locally.
- **The relay is not proof of who answered.** See requirement 2.
- **Same correction in several children:** no single child sees the pattern. A later parent step could count cases across the family.
- **A marker is a claim.** A child can misreport. Missing or invalid means not covered; the parent checks the file's shape with a script (extends `km_verdict_check.py`).
- The session tools exist only in the desktop app. Elsewhere the skill runs as today.

## Dependencies
#34 (trigger, result file, staged paths), #10 (owner-words-only), #23 (gate model), #37 (scripting; the lock and marker check go in scripts, not skill text, as the skill is near its size ceiling).

## Done when
In parent-led mode the owner answers a child's questions in the parent, the child writes its own memory and commits only its paths, the parent skips children already covered, two children never create the same rule twice, and the tests above pass in CI.
