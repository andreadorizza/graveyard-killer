# Settings live in the Library; memory only points to it

The phone's chat agent and the Worker must agree on the exact Categories and field names, but they do not share memory. The Claude apps share one memory, Claude Code keeps its own, and other agents keep theirs separately. Memory is also rewritten by the model, so it cannot hold names that must match character for character. So the Settings live inside the Library, as a page, a tab or a file. Each agent's memory holds one line: where the Library is. If that line is missing, the skill asks for the link once.

## Consequences

- If a phone app cannot run the uploaded skill, the memory line also carries the Capture rule: "When I share a social link without text, file it in my graveyard-killer Library at <link>, following the Settings there." Capture then needs only memory and a connector.
- Editing a Category means editing the Library's Settings, not the skill or a local file.
