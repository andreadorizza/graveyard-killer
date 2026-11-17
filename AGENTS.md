# Agent instructions

## Agent skills

### Issue tracker

Issues and specs are GitHub Issues on this repo, worked with the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

The five default triage roles, written as a `Status:` line in each issue file. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `GLOSSARY.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.

## Releases

A push to `main` is a release. Installed copies get new files only when the plugin's `version` changes, so before every push to `main`, run `git diff --stat origin/main -- plugin/`. If it lists files, raise `version` in `plugin/.claude-plugin/plugin.json` in the same push: minor for a new job or a change in behaviour, patch for a fix or a change that keeps behaviour. Build each release on its own branch, `release-<version>`, and merge it to `main` only after its evals pass: with fake posts while you work, then once with real posts in the live stage of `evals/README.md`. Tag the commit on `main` as `v<version>` and push the tag with it.

A Library, its scheduled task and the user's phone outlive the version that made them. So a release that changes what a Library holds (a Settings section, row or value, an Entry field, a Status), the scheduled task's prompt, or what Setup creates adds a step under its own version in `plugin/skills/graveyard-killer/references/upgrade.md`, and its evals include worker eval 18, which upgrades a frozen old Library. Never rename or remove anything in a Library without such a step. See ADR-0006.

## Library apps

Jobs read and write the Library only through the operations named in `plugin/skills/graveyard-killer/references/library.md`. How a Library app does each operation, and its own rules, go in `library-<app>.md`, and its Setup steps in `setup-<app>.md`. Never name an app's tools or quirks in a job file. See ADR-0005.
