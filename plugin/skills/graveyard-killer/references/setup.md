# Setup

Setup is a conversation on the user's computer, in the Claude Desktop Code tab, after the plugin is added. At the end the user has their own Library, the tools, the weekly Worker and Capture on the phone. The user is probably not technical, so do the work yourself. Explain each step in a line, and ask one thing at a time.

Setup starts when the user asks to set up Graveyard Killer, or when a Graveyard Killer job finds no Library. It does not need an existing Library, so skip SKILL.md's steps 2 and 3. Talk in the language the user writes in. It becomes the Settings language: say so in your first question, so the user can pick another.

## Steps

1. **What do they save?** Ask what kinds of posts the user saves, such as recipes, places, workouts or AI prompts. If the user mentions an Instagram export already on the computer, run `python3 scripts/graveyard.py "<path>"` and offer its `collections` as Categories. Done when you have 2 to 8 Categories, each with a line on what goes in it, and maybe its own fields (a recipe's ingredients, a place's location). Add one fallback Category for everything else.

2. **Create the Library.** Check that your Notion connector works, for example by reading the user's Notion profile or searching. If it does not, ask the user to connect Notion first. Ask in one question what to call the Library, suggesting "Graveyard Killer" as a private page. Then create it exactly as [library.md](library.md) describes:
   - the private page with that name;
   - the Entries database inside it, with every field in the user's language, the six Statuses and the Category options;
   - the `Settings` page, with every section. The Schedule section stays empty until step 3. The Graveyard section starts with "Dig up per run" at 10.

   Done when you can read the Settings back.

3. **Pick the schedule.** Ask which weekday and time the weekly Worker should run. Suggest Sunday at 10:00, and say that it runs only while the Claude app is open and the computer is awake. Write the answer in the Settings' Schedule section. Done when the Settings hold it.

4. **Install the tools.** Follow step 1 of [worker.md](worker.md#steps). Done when `check` prints `"ok": true`.

5. **Test one link end to end.** Ask the user for the link of a public post they saved. Capture it as [capture.md](capture.md) says. Then finish only that Entry, as worker.md's [Each Entry](worker.md#each-entry) says, with no dig-up and no Digest. Show them the finished Entry. Done when it is Processed.

6. **Remember the Library.** In the Code tab, memory is the user's Claude Code memory file, `~/.claude/CLAUDE.md`. Show the user the line `Graveyard Killer Library: <link>`, with the link and no query string. With their OK, add it at the end of that file. Use no other memory, such as Notion's. Done when the line is saved.

7. **Schedule the Worker,** as [schedule.md](schedule.md) says. Done when the weekly task exists.

8. **Set up the phone.** Tell the user, step by step, in the Claude app on their phone:
   - connect Notion in the app's connectors;
   - ask Claude there to remember `Graveyard Killer Library: <link>`;
   - share a post from Instagram, TikTok or YouTube to the Claude app, with no text, and check that an Entry appears in the Library.

   Done when the user confirms the shared post arrived, or says they will do it later.

9. **Offer the Graveyard.** Explain that their old saves can come in as Buried Entries, and how to request the exports (see [graveyard.md](graveyard.md#import-the-graveyard)). The exports take a few hours to about 2 days. Once they arrive, the user says "import my Graveyard Killer graveyard". Done when you have told them.

10. **Say how updates arrive.** A new version reaches the user when the Claude app syncs the Graveyard Killer marketplace. In *Customize → Plugins → Manage marketplaces*, the user can turn on *Sync automatically* for it, so each new version arrives by itself, or select *Check for updates* to get one at once. Done when you have told them.

11. **Say the Instagram risk once.** Graveyard Killer reads posts without the user's login, so their account is not used. Instagram may still slow down or block reading from their connection if it reads many posts at once, so a weekly run reads only a few. Done when you have told them.
