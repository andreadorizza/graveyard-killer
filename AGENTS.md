# Agent instructions

## Agent skills

### Issue tracker

Issues and specs are local markdown files under `.scratch/`, committed to git. See `docs/agents/issue-tracker.md`.

### Triage labels

The five default triage roles, written as a `Status:` line in each issue file. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `GLOSSARY.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.

## Releases

A push to `main` is a release. Installed copies get new files only when the plugin's `version` changes, so before every push to `main`, run `git diff --stat origin/main -- plugin/`. If it lists files, raise `version` in `plugin/.claude-plugin/plugin.json` in the same push: minor for a new job or a change in behaviour, patch for a fix.
