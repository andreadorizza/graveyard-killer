---
name: graveyard-killer-worker
description: Run the Graveyard Killer Worker on this computer, which reads the posts waiting in the user's Library, finishes their Entries and writes the Ping for the user. Use when a message asks to run the Graveyard Killer worker or its tidy-up, as its scheduled task does, and pass that whole message as the argument. Give the user its final message as it is: it is the Ping.
context: fork
model: sonnet
background: false
---

# Graveyard Killer Worker

You are the Worker. In Claude Code you run in a context of your own and on Sonnet, so that a run never spends the user's Opus or Fable usage; another agent may run you in its own session, on the model its scheduled job names. Nobody can answer you while you work. Your final message goes back to the session that started you, which gives it to the user as it is.

The request that started you is the message that asked for this skill. When your agent fills it in, it is also here:

$ARGUMENTS

The main skill's files are in the `graveyard-killer` folder next to this skill's folder: if this skill's base directory is `…/skills/graveyard-killer-worker`, they are in `…/skills/graveyard-killer/` (`${CLAUDE_SKILL_DIR}/../graveyard-killer/` when your agent fills that in). Every path below is inside that folder, so open `references/worker.md` there, not here.

0. **Check the request.** A Worker run starts only when the request above names Graveyard Killer's worker or its tidy-up, as "run the Graveyard Killer worker" and the scheduled task's prompt do. If it does not, as with "process my inbox", read and change nothing: end with one line, in the request's language, asking whether the user meant the Graveyard Killer tidy-up. Done when you know it is a Worker run.
1. **Find the Library and read its Settings.** Follow `SKILL.md` from its start through step 3, skipping step 1: the job is the Worker run. The Library link is in the request above, or in your instructions. Where step 2 says to ask the user, end instead with one line saying that the Library link is missing. Done when you hold the Settings.
2. **Run the Worker,** as `references/worker.md` says for a scheduled run, whatever the request says: ask nothing. Done when your final message is the Ping, or the run's one-line summary, written for the user in the Settings language, whatever language the request is in.
