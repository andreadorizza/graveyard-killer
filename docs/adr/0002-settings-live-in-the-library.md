# Settings live in the Library; memory only points to it

The phone's chat agent and the Worker must agree on the exact Categories and field names, but they do not share memory. The Claude apps share one memory, Claude Code keeps its own, and other agents keep theirs separately. Memory is also rewritten by the model, so it cannot hold names that must match character for character. So the Settings live inside the Library, as a page, a tab or a file. Each agent's memory holds one line: where the Library is. If that line is missing, the skill asks for the link once.

## Consequences

- The memory line holds only the Library's location: `Graveyard Killer Library: <link>`. The Capture instructions live only in the skill. The skill starts on its own when the user shares a link, through its description. A memory line that also carried the Capture rule was considered and rejected, for two reasons: the instructions would live in two places that drift apart, and the model rewrites memory. So Capture needs the skill: an app that cannot run the skill cannot Capture.
- Editing a Category means editing the Library's Settings, not the skill or a local file.
