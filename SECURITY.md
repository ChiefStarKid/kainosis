# Security

## Reporting a vulnerability

Please report security problems privately through GitHub: open this repository's **Security** tab and choose **Report a vulnerability**. Do not open a public issue for them.

Useful to include: what you ran, your OS and Claude Code version, and what you expected versus what happened. You should get a reply within 7 days.

In scope, for example:
- a secret (the probe token or anything else) written to disk, printed, or sent anywhere other than Anthropic's API
- a write outside `memory_path`, the session scratchpad or the probe folder
- a push to a remote or branch your scope rule file did not name, or any force-push
- the bare probe runner leaking your CLAUDE.md, memory or other context into a probe

## Support

For bugs, questions and feature requests, open a GitHub issue.

## Supported versions

Only the latest release is supported. Fixes ship as a new version in [CHANGELOG.md](CHANGELOG.md).
