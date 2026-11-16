# Bring a Library up to date

A Library outlives the version of Graveyard Killer that made it. The Settings' **Version** names the newest step below that the Library has had. A Library with no Version was made before 0.8.0. The newest heading under [Steps](#steps) is this skill's Library version.

You came here from SKILL.md's step 3 ([read the Settings](../SKILL.md#3-read-the-settings)).

- **A Worker run,** or **Setup** for a Library made elsewhere, brings an older Library up to date before its job, as [Upgrade](#upgrade) says.
- **Any other job** changes nothing here. It reads an older Library as the steps describe: what a step would add counts as its default, and what a step would replace counts as its replacement. So a phone Capture stays one quick turn.
- **A Library newer than this skill,** whose Version is newer than the newest heading below: another computer or device runs a newer Graveyard Killer. Change nothing here, and do the job with what you understand. In a Worker run, add a fix to the Ping; in Setup, tell the user: this computer runs an older Graveyard Killer than the Library, so update it in *Customize → Plugins → Check for updates*.

## Upgrade

Do every step whose version is newer than the Library's Version, or every step when Version is missing, in the order below, then [Every upgrade](#every-upgrade). Write the Settings through the Library app's operations ([library.md](library.md#write-the-settings)). Each step checks before it changes anything, so a step that finds nothing to do changes nothing. Keep each thing a step asks of the user for the Ping's fixes ([ping.md](ping.md#gather-it)), or tell it to the user at once in Setup. Done when Version is the newest heading below.

## Steps

### 0.4.0

- **Dig up per run.** If the Graveyard section holds a "Dig up per run" row, remove it: the Limits replace it.
- **Ping by `notion`.** If "Ping by" is `notion`, write `none`: a Notion mention never notified the user. Ask the user whether Pings should come by email, which they can turn on by saying "Graveyard Killer, ping me by email".
- **The scheduled task.** If this run's request calls the run "unattended", the scheduled task's prompt is from before 0.4.0. Ask the user to say "update my Graveyard Killer schedule" in the Claude Desktop Code tab, which rewrites the task and makes the run daily. You cannot change the task from inside its own run.
- The Limits, Pings and Preferences sections arrive with [Every upgrade](#every-upgrade).

### 0.7.0

- The Pings section's "Open offers" row arrives with [Every upgrade](#every-upgrade), empty.

### 0.8.0

- The Version section arrives with [Every upgrade](#every-upgrade).

## Every upgrade

Last, whatever the Library's Version:

1. **Missing sections and rows.** Add each section of [library.md's Settings](library.md#the-settings) that the Settings lack, and each row of its Limits, Pings and Graveyard tables, in library.md's order, with library.md's defaults: the Limits at 20 a day and 100 a week, every other new setting empty. Leave the values already there, and leave any row library.md does not name.
2. **Version.** Set it to the newest heading under [Steps](#steps).
