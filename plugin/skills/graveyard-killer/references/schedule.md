# Schedule the Worker

The weekly Worker is a scheduled task in the Claude Desktop Code tab. It runs on the day and at the time in the Settings, while the app is open and the computer is awake. If the computer is asleep or the app is closed at that time, the task runs at the next launch. Each run starts fresh, so its prompt carries everything it needs.

You have chosen this job, found the Library and read its Settings (see SKILL.md). You need your scheduling tool, the one that creates scheduled tasks in the Code tab. Without it, tell the user that the weekly Worker is set up from the Claude Desktop Code tab, and stop.

## Steps

1. **Read the schedule** from the Settings' Schedule section: a weekday and a time, such as `Domenica 10:00`. Done when you hold both. With no time given, use 10:00.

2. **Create or update the task.** List the scheduled tasks first, and read the prompt of any task named `graveyard-killer-worker`.
   - If its prompt names this Library, update its schedule and prompt.
   - If it names another Library, it runs that Library's Worker. Ask the user whether to replace it or add a second task. A second task gets the taskId `graveyard-killer-worker-2`, or the next free number.
   - If there is none, create it.

   Use these values:
   - **taskId:** `graveyard-killer-worker`
   - **title:** "Graveyard Killer: weekly Worker", in the Settings language
   - **description:** "Weekly Graveyard Killer Worker run: finishes the Inbox, digs up the Graveyard and writes the Digest"
   - **notifications:** off, since the Digest tells the user what happened
   - **schedule:** a weekly cron expression in local time, such as `0 10 * * 0` for Sunday at 10:00 (0 is Sunday, 1 is Monday)
   - **prompt:** exactly this, with the Library link filled in:

     ```
     Run the Graveyard Killer worker.

     Graveyard Killer Library: <the Library link>

     This is an unattended scheduled run: nobody can answer a question. Ask nothing. Where the skill says to ask, do what it says for an unattended run.
     ```

   Done when the tool confirms the task and its next run time.

3. **Tell the user**, in the Settings language: the day and time of the runs, and that a run only happens while the Claude app is open and the computer is awake. A missed run catches up once at the next launch. If the session is not in Auto mode, the first run may stop for tool approvals. In that case the user should open the run and choose "always allow" for each tool, so that later runs never stop. Done when you have sent it.
