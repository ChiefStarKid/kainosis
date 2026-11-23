# Second cluster: spreadsheet and document handling

A second data point for the method, November 2026. One person, one memory: indicative, not proof. The first cluster's results are in the [README](../README.md#results-so-far).

Terms used here: a **basis tag** marks each rule `fact` or `preference` (permanent) or `compensation` (guards a model weakness, so it can retire). A **probe** is a clean-room test of a rule, run with and without its text on the current model. To **retire** a rule is to move it to a dormant folder, where it stops loading and can be revived. See [evals.md](evals.md#probe).

## What was tested

The first cluster was general working habits (git, shell, permissions, time zones, reading whole sources). This one is rules about handling data files: what a data column means, formula edge cases, whether a document is final, what a sent file contains, scoped instructions, table styling. It was chosen because it had the most `compensation` rules not already probed (PRD 01: choose by rule count first).

- **Cluster:** 17 rules by my grouping: 8 `compensation`, 4 `fact`, 5 `preference`. Facts and preferences are permanent and were not probed.
- **Probed:** 6 `compensation` rules, labelled R1 to R6. The other 2 are marked severity high; those never retire on model evidence, so they were left out.
- **Models:** claude-sonnet-5-5 and claude-opus-5-5, through the [bare runner](evals.md#probe), after a clean canary on each.
- **Runs:** 100 probe runs plus 2 canaries, about $1.93 API-equivalent including grading. Round one: one run per arm, then three on rules that passed without their text. Round two: harder scenarios (noise, a leading request) for the rules that kept passing.
- **Scoring:** model-graded (Sonnet), except R6, which a regex scored. Scenarios were invented for the probe and never hinted at the rule.
- **Transcripts:** 414 sessions, scanned by script, then candidates read by hand.

## Results

| Rule | Without its text, Sonnet | Without its text, Opus | With its text | Transcript evidence | Outcome |
|---|---|---|---|---|---|
| R1 column meaning | fail (0/1) | 3/3 | pass | no check possible | still needed |
| R2 formula edge cases | 5/5 | 5/5 | pass | no exposure found | kept |
| R3 document status | 5/5 | 5/5 | pass | no exposure found | kept |
| R4 sent-file content | 5/5 | 5/5 | pass | no exposure found | kept |
| R5 scoped instructions | 5/5 | 5/5 | pass | no exposure found | kept |
| R6 table styling | 3/3 | 3/3 | pass | 5 violation candidates | kept; hook candidate |

- **Retired: 0 of 17.** Rule count and always-loaded bytes are unchanged (index 12,976 bytes before and after).
- **R1 is still needed:** the smaller model fails without it.
- **R6 is the evidence rule in action.** It passed 3/3 on both models, yet the transcripts held 5 file writes that look like lapses (violation candidates, not confirmed), so it stays and is a candidate for enforcement by a hook. The same pattern as the first cluster's shell rule.
- **R2 to R5 passed every clean-room test, but a probe pass alone does not retire a rule.** The evidence rule also asks for transcripts showing no lapses. The scan found no sessions doing this kind of work: it happens in another profile, so "no violations" meant no exposure, not good behaviour. Absence of evidence is not evidence, so the four were kept and marked as validated on probes only.
- **Check coverage:** 1 of 6 probed rules has a deterministic transcript check; the rest are judgment rules.

## What this does and does not show

- The method did not retire anything it could not back with a second source, and it flagged the one rule where probes and transcripts disagreed.
- It does not show that these rules are unneeded. The bare runner lacks the host app's own system prompt, so a pass may reflect only that the model knows the habit in a bare context.
- Scoring was model-graded except R6. Five of six rules passing without their text is a high rate, and invented scenarios may be easier than real sessions; a second, harder round changed no result.
- One person, one memory, two clusters. Whether it holds for other people's rules is open.
- Next step for stronger evidence: run the same transcript scan on the profile where this work happens.
