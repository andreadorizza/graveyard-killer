# Graveyard Killer in OpenCode

A user with no paid Claude plan runs Graveyard Killer in **OpenCode**, on one of its free models, and their computer's own scheduler starts the Worker every day ([ADR-0007](https://github.com/andreadorizza/graveyard-killer/blob/main/docs/adr/0007-a-free-worker-in-opencode.md)). This file holds what differs from Claude Desktop: installing the skills, Setup's steps that name the Code tab, the schedule and updates. Every other step works as written.

You are in OpenCode when your tools and instructions are OpenCode's, or when this skill was loaded from `~/.config/opencode/skills`. The free route works with a Notion Library only: a Drive Library needs Google connectors that OpenCode does not have, and an Obsidian Library is tested with Claude only.

Paths here use `~/.config/opencode`, OpenCode's global folder on every system. On Windows that is `%USERPROFILE%\.config\opencode`. Both OpenCode 1.x and 2.x read this folder, `AGENTS.md` and the config shape below.

## Pick the model

Graveyard Killer sends OpenCode's model the user's saved posts, their Library and their answers, so it uses only free models that keep no data and train on nothing: **DeepSeek V4.1 Flash Free** (`opencode/deepseek-v4.1-flash-free`), and **GLM-5.3-Flash Free** (`opencode/glm-5.3-flash-free`) as the second. Both passed the Worker evals; DeepSeek was three times faster. Hy4 flash Free (`opencode/hy4-flash-free`) keeps no data either and comes next. OpenCode's other free models may keep data or train on it, or cannot read images. Free models are free "for a limited time": when the first one goes, the Worker switches to the second, and the user picks a new one from this list.

Before Setup, ask the user to pick DeepSeek V4.1 Flash Free in OpenCode's model list for this chat, too. A free model has a usage limit that OpenCode does not show. On 2026-11-17 DeepSeek and GLM reached it together, after about 75 minutes of back-to-back runs, and still answered "Free usage limit reached" more than an hour and a half later, while Hy4 flash Free still answered. So when a chat says it, picking the second model does not help: tell the user that it can last hours, and to try again later.

## Install

The user's first message in OpenCode points here, from the README, before the skills exist on the computer. Explain each step in a line. Done when the user has reopened OpenCode with the skills and Notion.

1. **Download the skills** into OpenCode's global skills folder, replacing an older copy. On macOS and Linux:

   ```
   mkdir -p ~/.config/opencode/skills && cd ~/.config/opencode/skills && rm -rf graveyard-killer graveyard-killer-worker && curl -fsSL https://github.com/andreadorizza/graveyard-killer/archive/refs/heads/main.tar.gz | tar -xz --strip-components=3 graveyard-killer-main/plugin/skills
   ```

   On Windows, in PowerShell:

   ```
   $d = "$env:USERPROFILE\.config\opencode\skills"; New-Item -ItemType Directory -Force $d | Out-Null; Remove-Item -Recurse -Force "$d\graveyard-killer", "$d\graveyard-killer-worker" -ErrorAction SilentlyContinue; curl.exe -fsSL https://github.com/andreadorizza/graveyard-killer/archive/refs/heads/main.tar.gz -o "$env:TEMP\graveyard-killer.tar.gz"; tar -xzf "$env:TEMP\graveyard-killer.tar.gz" -C $d --strip-components=3 graveyard-killer-main/plugin/skills
   ```

   Done when `~/.config/opencode/skills/graveyard-killer/SKILL.md` exists.

2. **Add Notion.** In OpenCode's global config, `~/.config/opencode/opencode.json` or `opencode.jsonc`, whichever exists, add this server to `mcp`, keeping everything else. Create the file with `"$schema": "https://opencode.ai/config.json"` if there is none.

   ```json
   "mcp": {
     "notion": { "type": "remote", "url": "https://mcp.notion.com/mcp" }
   }
   ```

   Done when the file has it and is still valid JSON.

3. **Sign in to Notion.** Run `opencode mcp auth notion`. It opens Notion in the browser: the user picks their workspace and allows access. It waits for them, so give it a few minutes. Done when it says the sign-in worked.

4. **Restart OpenCode.** OpenCode reads its config and skills only when it starts. Ask the user to quit OpenCode, open it again, and type "Set up Graveyard Killer" in a new chat.

## Setup in OpenCode

[Setup](setup.md#steps) runs as written, in an OpenCode chat, except these steps.

- **Step 2, the Library:** Notion only. If the user wants Google Drive or Obsidian, say that the free route needs Notion, and that Drive and Obsidian need a paid Claude plan.
- **Step 3, the time:** say that the Worker runs while the computer is on and awake, whether or not OpenCode is open. A run missed while it slept or was off runs once when it is back: at once on a Mac, after about 10 minutes on Windows, and on Linux at the next login, since Linux starts a user's timers only after they log in.
- **Step 6, the pointer:** it goes in `~/.config/opencode/AGENTS.md`, which OpenCode reads in every chat. Add [the pointer](setup.md#the-pointer) at the end of that file, creating it if needed, with the user's OK.
- **Step 7, the schedule:** [schedule the Worker](#schedule-the-worker) below.
- **Step 8, the phone:** only *Save through the Library app*, Notion's share menu. Skip the pointer in Claude's Instructions and *Save through Claude*: the free route puts the skills in OpenCode only, so a chat in the Claude app does not have them, and Graveyard Killer is untested on Claude's free plan.
- **Step 9, Pings:** offer `push` or `none`. `email` needs a Gmail connector that OpenCode does not have.
  - `push`: a notification on this computer, shown by `post.py notify` ([ping.md](ping.md#send-it)). On a Mac it comes from Script Editor: if it does not show, the user turns on notifications for Script Editor in *System Settings → Notifications*. On Linux it needs `notify-send`.
  - Both: the whole Ping waits in the run's chat, and in `last-run.json` in the run folder. The user opens OpenCode in the run folder and picks the run's chat, whose id `schedule.py show` prints, or answers from any OpenCode chat by naming Graveyard Killer.
  - The test Ping: send the alert through `post.py notify` and ask whether it showed.
- **Step 11, updates:** to get a new version, the user tells OpenCode "update Graveyard Killer", which [updates the skills](#update).

## Schedule the Worker

Graveyard Killer's own script installs one job in the computer's scheduler: launchd on a Mac, Task Scheduler on Windows, a systemd timer on Linux. The job runs the Worker in OpenCode with the scheduled prompt from [schedule.md](schedule.md#steps), in its own run folder. It tries the second model when the first fails, which helps when the first model is gone, not at the usage limit, which reaches both ([Pick the model](#pick-the-model)). It shows a notification when both fail and writes each run to `worker.log` in that folder. Run the script from this skill's folder, the copy OpenCode loads, since the job may read only that copy. Every command prints one JSON object; `"error"` means it did nothing. Done when `show` prints the job.

1. **Read the schedule** from the Settings, as schedule.md's step 1 says.
2. **Install the job** with the time and days from the Settings, the model and the second model from [Pick the model](#pick-the-model), the Library link, and two texts in the Settings language: the job's name, as schedule.md's title, and the line a notification shows when a run fails. The run folder is `graveyard-killer` in the user's home folder: never under Desktop, Documents or Downloads, where macOS stops a background job to ask, and never Codex's run folder. If the script says that the folder is Codex's, a Codex task made by version 0.11.0 runs there: use `~/graveyard-killer-opencode` instead. Installing again replaces the job, so this also changes its time.

   ```
   python3 scripts/schedule.py install --time 13:00 --model opencode/deepseek-v4.1-flash-free --fallback-model opencode/glm-5.3-flash-free --folder ~/graveyard-killer --library "<the Library link>" --title "Graveyard Killer: riordino" --alert "Graveyard Killer non è riuscito a fare il riordino di oggi."
   ```

   Add `--days mon,wed,fri` when the Settings name weekdays. The script also writes the run folder's `opencode.json`, which adds Notion and lets the run read only the skills, the run folder and its own work folders, and run only the skill's scripts, and an `AGENTS.md` with the pointer if there is none.
3. **Check it** with `python3 scripts/schedule.py show`. Done when it prints the time, the model and the Library.
4. **Tell the user**, in the Settings language, the time of the runs and when a missed run catches up, as Setup's step 3 says. On Linux, a user's timer runs only after they log in, unless `loginctl enable-linger` is on. `python3 scripts/schedule.py remove` stops the runs.

Install again after moving the run folder, or when the Python that ran `install` is upgraded or removed: the job runs with that Python.

## Update

The user asked to update Graveyard Killer. Run [Install](#install)'s step 1 again, which replaces the skills with the newest version, and tell the user to start a new chat. The next Worker run brings the Library up to date by itself ([upgrade.md](upgrade.md)). Done when the new `SKILL.md` is in place.
