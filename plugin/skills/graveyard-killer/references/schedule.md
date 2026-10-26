# Schedule the Worker

The weekly Worker is a scheduled task in the Claude Desktop Code tab. It runs on the day and at the time in the Settings, while the app is open and the computer is awake. If the computer is asleep or the app is closed at that time, the task runs at the next launch. Each run starts fresh, so its prompt carries everything it needs.

You have chosen this job, found the Library and read its Settings (see SKILL.md). You need your scheduling tool, the one that creates scheduled tasks in the Code tab. Without it, tell the user that the weekly Worker is set up from the Claude Desktop Code tab, and stop.

## Steps

1. **Read the schedule** from the Settings' Schedule section: a weekday and a time, such as `Domenica 10:00`. Done when you hold both. With no time given, use 10:00.

2. **Create or update the task.** List the scheduled tasks first. If one named `graveyard-killer-worker` exists, update it. Otherwise create it with:
   - **taskId:** `graveyard-killer-worker`
   - **title:** "Graveyard Killer: weekly Worker", in the Settings language
   - **schedule:** a weekly cron expression in local time, such as `0 10 * * 0` for Sunday at 10:00 (0 is Sunday, 1 is Monday)
   - **prompt:** exactly this, with the Library link filled in:

     ```
     Run the Graveyard Killer worker.

     Graveyard Killer Library: <the Library link>

     This is an unattended scheduled run: nobody can answer a question. Ask nothing. Where the skill says to ask, do what it says for an unattended run.
     ```

   Done when the tool confirms the task and its next run time.

3. **Tell the user**, in the Settings language: the day and time of the runs, and that a run only happens while the Claude app is open and the computer is awake. A missed run catches up once at the next launch. If the session is not in Auto mode, the first run may stop for tool approvals. In that case the user should open the run and choose "always allow" for each tool, so that later runs never stop. Done when you have sent it.
