# Graveyard Killer in Codex

A user with a ChatGPT account, on any plan, Free included, runs Graveyard Killer in **Codex**, the coding agent in the ChatGPT desktop app. The app's own Scheduled tasks start the Worker every day, so the user can see, change and run it from the app ([ADR-0008](https://github.com/andreadorizza/graveyard-killer/blob/main/docs/adr/0008-a-worker-in-codex.md)). This file holds what differs from Claude Desktop: installing the skills, Setup's steps that name the Code tab, the schedule, running the scripts and updates. Every other step works as written.

You are in Codex when your tools and instructions are Codex's or ChatGPT's. Codex works with a Notion Library only: a Drive Library needs Google connectors that are tested with Claude only.

Paths here use `~/.agents/skills`, where Codex reads a user's skills, and `~/.codex`, Codex's own folder. On Windows they are `%USERPROFILE%\.agents\skills` and `%USERPROFILE%\.codex`.

## What OpenAI keeps

On ChatGPT's individual plans (Free, Go, Plus and Pro), OpenAI may use the chats, Codex's included, to train its models, unless the user turns off **Improve the model for everyone** in ChatGPT's *Settings → Data controls*. Business, Enterprise and Edu workspaces are not used for training by default. Graveyard Killer sends Codex the user's saved posts, their Library and their answers. So before Setup's step 1, tell the user this in two lines and ask them to turn that setting off, or to confirm that it is off. If they choose to leave it on, go on: it is their call. Done when they have answered.

## Install

The user's first message in Codex points here, from the README, before the skills exist on the computer. Explain each step in a line. Each step changes something outside the chat's folder, so Codex asks the user to approve it. Done when the user has started a new chat with the skills and Notion.

1. **Download the skills** into `~/.agents/skills`, replacing an older copy. On macOS:

   ```
   mkdir -p ~/.agents/skills && cd ~/.agents/skills && rm -rf graveyard-killer graveyard-killer-worker && curl -fsSL https://github.com/andreadorizza/graveyard-killer/archive/refs/heads/main.tar.gz | tar -xz --strip-components=3 graveyard-killer-main/plugin/skills
   ```

   On Windows, in PowerShell:

   ```
   $d = "$env:USERPROFILE\.agents\skills"; New-Item -ItemType Directory -Force $d | Out-Null; Remove-Item -Recurse -Force "$d\graveyard-killer", "$d\graveyard-killer-worker" -ErrorAction SilentlyContinue; curl.exe -fsSL https://github.com/andreadorizza/graveyard-killer/archive/refs/heads/main.tar.gz -o "$env:TEMP\graveyard-killer.tar.gz"; tar -xzf "$env:TEMP\graveyard-killer.tar.gz" -C $d --strip-components=3 graveyard-killer-main/plugin/skills
   ```

   Done when `~/.agents/skills/graveyard-killer/SKILL.md` exists.

2. **Add Notion** with `codex mcp add notion --url https://mcp.notion.com/mcp`. It opens Notion in the browser: the user picks their workspace and allows access. It waits for them, so give it a few minutes. Done when it says the sign-in worked. If it was added before, `codex mcp login notion` signs in again.

3. **Start a new chat.** Codex finds new skills by itself, but loads Notion's tools only when a chat starts. Ask the user to start a new chat and type "Set up Graveyard Killer". If the skill is not found there, they quit the ChatGPT app and open it again.

## Setup in Codex

Tell the user [what OpenAI keeps](#what-openai-keeps) first. Then [Setup](setup.md#steps) runs as written, in a Codex chat in the ChatGPT app, except these steps.

- **Step 2, the Library:** Notion only. If the user wants Google Drive, say that Graveyard Killer in Codex needs Notion, and that Drive works in Claude.
- **Step 3, the time:** say that the Worker runs only while the ChatGPT app is running and the computer is on and awake.
- **Step 6, the pointer:** it goes in `~/.codex/AGENTS.md`, which Codex reads in every chat. Add [the pointer](setup.md#the-pointer) at the end of that file, creating it if needed, with the user's OK.
- **Step 7, the schedule:** [schedule the Worker](#schedule-the-worker) below.
- **Step 8, the phone:** as written. To answer a Ping from the phone, the Claude app works on its free plan, with connectors: the user connects Notion to Claude, in *Customize → Connectors* on claude.ai, and pastes the pointer into their Instructions.
- **Step 9, Pings:** as written, except that Codex has no push tool: `push` shows a notification on this computer through `post.py notify` ([ping.md](ping.md#send-it)). Send the test Ping outside the sandbox: run `post.py notify` as [Run the scripts](#run-the-scripts) says, asking for the user's approval, since in the sandbox it cannot show a notification. On a Mac it comes from Script Editor: if it does not show, the user turns on notifications for Script Editor in *System Settings → Notifications*. Offer `email` only when you have a Gmail tool. The whole Ping waits in the run's chat, under *Scheduled* in the ChatGPT app.
- **Step 11, updates:** to get a new version, the user tells Codex "update Graveyard Killer", which [updates the skills](#update).

## Schedule the Worker

The ChatGPT app's Scheduled tasks start the Worker, so the user sees each run, its Ping and its time under *Scheduled*. But the app runs a task with the user's default permissions, which read the whole disk, and a post is untrusted input. So the task runs one command, `schedule.py codex-run`, which runs the Worker with `codex exec` in its own run folder. There the folder's settings fence the run: its commands may read only the skills and that folder, and reach no network, and only the skill's own scripts run outside that sandbox. The task's chat gives the user the Ping that `codex-run` prints. Done when the task shows in the app's *Scheduled* view.

1. **Read the schedule** from the Settings, as schedule.md's step 1 says.
2. **Prepare the run folder.** The run folder is `graveyard-killer-codex` in the user's home folder: never under Desktop, Documents or Downloads, where macOS asks before an app reads them, and never OpenCode's `graveyard-killer`, which the script refuses. Run the script from this skill's folder, by its full path, with the line a failed run shows, in the Settings language:

   ```
   python3 ~/.agents/skills/graveyard-killer/scripts/schedule.py codex --folder ~/graveyard-killer-codex --library "<the Library link>" --alert "Graveyard Killer non è riuscito a fare il riordino di oggi."
   ```

   When the app has a Graveyard Killer task already whose prompt runs `codex-run` in another folder, such as `~/graveyard-killer` from version 0.11.0, add `--old-folder` with that folder: the script removes the files it wrote there, so that OpenCode's Worker can have that folder.

   It prints one JSON object; `"error"` means it did nothing. It writes the folder's `AGENTS.md` with the pointer, unless one is there, and its `.codex` folder: the sandbox's profile and rules, the Library link and the alert, Notion's server, approved for writes since nobody watches the run, and the Worker's model, GPT-6 Luna at high effort. `codex-run` gives the unattended run only the Notion tools a Worker needs: never one that deletes, moves or shares. It also marks the folder as trusted in `~/.codex/config.toml`, since Codex ignores an untrusted folder's `.codex`. Done when it lists what it wrote.

3. **Create the task** with your scheduling tool, which asks the user to approve it. When a Graveyard Killer task is there already, update it with these values instead of adding a second one. If you have no scheduling tool, walk the user through *Scheduled → New task* in the app's sidebar, or the task's *Edit*, with the same values. Done when the task shows in *Scheduled*.
   - a standalone task, which starts a new chat for each run
   - **project:** the run folder
   - **name:** "Graveyard Killer: tidy-up", in the Settings language ("Graveyard Killer: riordino")
   - **schedule:** every day at the time in the Settings, or on the weekdays it names
   - **model:** GPT-6 Luna, with reasoning effort High: the task's chat also answers the user's replies, and at medium effort it said it had saved a Preference that it never wrote
   - **prompt:** the `prompt` the script printed, exactly, as plain text
   - **notifications**, under *Advanced* in the task's *Edit*: *Failed runs only*. The Ping alerts the user, and a failed `codex-run` shows a notification of its own.

4. **Tell the user**, in the Settings language, the time of the runs, and that a run happens only while the ChatGPT app is running and the computer is awake. Each run's chat, with its Ping, is under *Scheduled* in the app, where they can also change the time or run it now. The run's log is `worker.log` in the run folder.

Prepare the run folder again after moving the skills or the folder, with `--old-folder` for a moved folder.

## Run the scripts

In the run folder, every command runs in Codex's sandbox, where the scripts find no Python, no network and no GPU, except the skill's own scripts called in the one form the folder's rules let out:

- by their full path, written out as the folder's `AGENTS.md` gives it, such as `python3 /Users/<name>/.agents/skills/graveyard-killer/scripts/post.py`, never with `~` or `scripts/`;
- with the link or the text as arguments in single quotes, never through a heredoc or a pipe, which keep the whole command in the sandbox. So `python3 <scripts>/post.py read --language it '<the Entry's Link>'`, `python3 <scripts>/link.py '<the link>'`, `python3 <scripts>/post.py notify 'Graveyard Killer' '<one short line>'` and, for a cover, `python3 <scripts>/post.py upload '<image>' '<upload URL>' --header '<name>: <value>'`. Write a `'` inside a link as `%27`, and leave a `'` out of a notification's line;
- one command at a time, or joined with `&&`.

A script that fails with "No developer tools were found" or "Operation not permitted", or a `post.py notify` whose reason names error -2741 ("syntax error: Expected end of line but found identifier"), ran in the sandbox: run it again in this form. Never install anything because of such an error.

In a chat anywhere else, Setup's included, a command starts in that chat's sandbox, and no rules let the scripts out. So run the skill's scripts in the same form, and ask the user to approve running them outside the sandbox.

## Update

The user asked to update Graveyard Killer. Run [Install](#install)'s step 1 again, which replaces the skills with the newest version, and tell the user to start a new chat. The next Worker run brings the Library up to date by itself ([upgrade.md](upgrade.md)). Done when the new `SKILL.md` is in place.
