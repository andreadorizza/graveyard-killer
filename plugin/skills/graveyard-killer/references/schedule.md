# Schedule the Worker

The Worker is a scheduled task in the Claude Desktop Code tab. It runs every day at the time in the Settings, while the app is open and the computer is awake. If the computer is asleep or the app is closed at that time, the task runs at the next launch. Each run starts fresh, so its prompt carries everything it needs.

You have chosen this job, found the Library and read its Settings (see SKILL.md). In OpenCode, follow [opencode.md](opencode.md#schedule-the-worker) instead. Elsewhere you need your scheduling tool, the one that creates scheduled tasks in the Code tab. Without it, tell the user that the Worker is scheduled from the Claude Desktop Code tab, or by OpenCode on the free route, and stop.

## Steps

1. **Read the schedule** from the Settings' Schedule section: a time, every day unless it names weekdays, such as `Ogni giorno 13:00`. Done when you hold it. With no time given, use 13:00.

2. **Create or update the task.** List the scheduled tasks first, and read the prompt of any task named `graveyard-killer-worker`.
   - If its prompt names this Library, update its title, description, schedule and prompt. This also brings a task made by an older version up to date.
   - If it names another Library, it runs that Library's Worker. Ask the user whether to replace it or add a second task. A second task gets the taskId `graveyard-killer-worker-2`, or the next free number.
   - If there is none, create it.

   Use these values:
   - **taskId:** `graveyard-killer-worker`
   - **title:** "Graveyard Killer: tidy-up", in the Settings language ("Graveyard Killer: riordino")
   - **description:** "Reads the new posts, brings back a few old saves and pings you when something needs you", in the Settings language
   - **notifications:** off, since the Ping alerts the user
   - **schedule:** a cron expression in local time, such as `0 13 * * *` for every day at 13:00
   - **prompt:** exactly this, with the Library link filled in:

     ```
     Run the Graveyard Killer worker with the graveyard-killer-worker skill, and pass it this whole message.

     Graveyard Killer Library: <the Library link>

     This is a scheduled run. When the skill returns, give its final message to the user as it is: it is the Ping. Then answer the user's replies in this chat with the graveyard-killer skill.
     ```

   Done when the tool confirms the task and its next run time.

3. **Set the model and the approvals.** Your scheduling tool cannot set a task's model, so walk the user through it. Done when the user says both are done.
   - In the Code tab's list of scheduled tasks, they open the Graveyard Killer task, edit it, and pick Sonnet as its model. The Worker itself always runs on Sonnet; this setting also puts the run's chat, which passes on the Ping and answers the user, on Sonnet.
   - They select *Run now* once and choose "always allow" for each tool the run asks for, so that later runs never stop for an approval.

4. **Tell the user**, in the Settings language: the time of the runs, that a run only happens while the Claude app is open and the computer is awake, and that a missed run catches up once at the next launch. Done when you have sent it.
