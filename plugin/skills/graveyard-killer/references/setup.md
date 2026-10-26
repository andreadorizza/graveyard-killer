# Setup

Setup is a conversation on the user's computer, in the Claude Desktop Code tab, after the plugin is added. At the end the user has their own Library, the tools, the weekly Worker and Capture on the phone. The user is probably not technical, so do the work yourself. Explain each step in a line, and ask one thing at a time.

Setup starts when the user asks to set up Graveyard Killer, or when a Graveyard Killer job finds no Library. It does not need an existing Library, so skip SKILL.md's steps 2 and 3. Talk in the user's language. It becomes the Settings language.

## Steps

1. **What do they save?** Ask what kinds of posts the user saves, such as recipes, places, workouts or AI prompts. If their Instagram export is already on the computer, run `python3 scripts/graveyard.py "<path>"` and offer its `collections` as Categories. Done when you have 2 to 8 Categories, each with a line on what goes in it, and maybe its own fields (a recipe's ingredients, a place's location). Add one fallback Category for everything else.

2. **Create the Library.** Check that your Notion connector works. If it does not, ask the user to connect Notion first. Then create the Library exactly as [library.md](library.md) describes:
   - a private Notion page titled "Graveyard Killer", or the user's own name for it;
   - the Entries database inside it, with every field in the user's language, the six Statuses and the Category options;
   - the `Settings` page, with every section.

   Ask where the page should live only if the user cares. Done when you can read the Settings back.

3. **Pick the schedule.** Ask which weekday and time the weekly Worker should run. Suggest Sunday at 10:00, and say that it runs only while the Claude app is open and the computer is awake. Write the answer in the Settings' Schedule section. Done when the Settings hold it.

4. **Install the tools.** Follow step 1 of [worker.md](worker.md#steps). Done when `check` prints `"ok": true`.

5. **Test one link end to end.** Ask the user for the link of a public post they saved. Capture it as [capture.md](capture.md) says, then run the Worker on it as [worker.md](worker.md) says. Show them the finished Entry. Done when it is Processed.

6. **Remember the Library.** Save `Graveyard Killer Library: <link>` to your memory. Without a memory tool, ask the user to add the line to their Claude Code memory. Done when the line is saved.

7. **Schedule the Worker,** as [schedule.md](schedule.md) says. Done when the weekly task exists.

8. **Set up the phone.** Tell the user, step by step, in the Claude app on their phone:
   - connect Notion in the app's connectors;
   - ask Claude there to remember `Graveyard Killer Library: <link>`;
   - share a post from Instagram, TikTok or YouTube to the Claude app, with no text, and check that an Entry appears in the Library.

   Done when the user confirms the shared post arrived, or says they will do it later.

9. **Offer the Graveyard.** Explain that their old saves can come in as Buried Entries, and how to request the exports (see [graveyard.md](graveyard.md#import-the-graveyard)). The exports take a few hours to about 2 days. Once they arrive, the user says "import my Graveyard Killer graveyard". Done when you have told them.

10. **Say the Instagram risk once.** Graveyard Killer reads posts without the user's login, so their account is not used. Instagram may still slow down or block reading from their connection if it reads many posts at once, so a weekly run reads only a few. Done when you have told them.
