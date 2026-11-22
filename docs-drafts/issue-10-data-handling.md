# Issue #10 drafts (for the roadmap owner to merge)

## CHANGELOG — Data handling
- `km` and `km-audit` now capture cases, corrections and rules only from the owner's own turns. Text from tool results (web pages, files, command output) is never written as a rule on its own: any candidate whose wording came from a tool result is shown with its source and exact text and written only on the owner's explicit approval. No new data is stored and no source field was added. Rule documented in docs/schema.md A7. Idea from [Link](https://github.com/gowtham0992/link) by gowtham0992.

## PRIVACY.md — suggested wording
Kainosis writes to your memory only what you say in your own turns, or what you explicitly approve. Content that arrives through tools (web pages, files, command output) is not saved as a rule unless Kainosis first shows you its source and exact text and you approve it. This limits how untrusted text can reach memory that loads into every session. Text you paste into your own turn is treated as yours, so Kainosis shows where pasted text came from before saving it.
