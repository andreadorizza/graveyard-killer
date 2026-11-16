# Libraries record their version and upgrade themselves

An install gets a new version only when the user chooses *Check for updates*, and each computer or phone updates on its own. The Library, the scheduled task and the phone's share setup outlive the version that made them. Until 0.7.0, each change that touched them added its own "a Library made before 0.x" note to the file it changed, and nothing told an agent how old a Library was.

So the Settings hold a **Version**: the newest step of `references/upgrade.md` that the Library has had. upgrade.md lists one idempotent step per version that changed what a Library holds, the scheduled prompt or what Setup makes, then an "every upgrade" pass that adds any missing section or row with its defaults. A Worker run brings an older Library up to date before its job, and Setup does it for a Library made elsewhere. Every other job only reads an older Library as upgrade.md describes, so a phone Capture stays one quick turn and two jobs never upgrade at once. What only the user can do, such as rewriting the scheduled task, goes into the Ping.

The Version follows the Library's format, not the plugin's version: it moves only in a release that adds an upgrade step. So a Library newer than an install's newest step means that install is out of date, and the Worker says so in its Ping.

## Considered Options

- **A note in each file, as until 0.7.0.** It works while changes are few and only add things. Each release must remember the right file, and a rename has no place to go. Replaced.
- **The plugin's version in the Settings.** It would change with every release, even one that leaves the Library alone, and could not say what an old Library lacks.
- **An upgrade script.** The Library is reached only through the user's connectors ([ADR-0001](0001-no-server-no-api-keys.md)), so a script cannot reach it. The agent does the steps.
- **Let the agent cope.** It often copes with a small mismatch, but it may also guess, skip or "fix" the wrong way without saying so.

## Consequences

- AGENTS.md's release rules: a release that changes what a Library holds, the scheduled prompt or what Setup makes adds its upgrade step, and never renames or removes without one.
- Worker eval 18 upgrades a frozen 0.3.0 Library (`evals/fixtures/settings-0.3.0.md`) to the current version.
- Entry fields and Statuses have not changed since 0.3.0, so upgrade.md has no step for them yet. The first release that changes one adds that step and the Library app operations it needs.
