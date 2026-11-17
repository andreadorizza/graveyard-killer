# Setup

Setup is a conversation on the user's computer, in the Claude Desktop Code tab after the plugin is added, in Codex in the ChatGPT desktop app after its [Install](codex.md#install), or in OpenCode, on a free model, after its [Install](opencode.md#install). In Codex, read [codex.md](codex.md) first: its [Setup in Codex](codex.md#setup-in-codex) replaces the steps below that name Claude Desktop. In OpenCode, read [opencode.md](opencode.md) first, for the same reason: [Setup in OpenCode](opencode.md#setup-in-opencode). At the end the user has their own Library, the tools, the scheduled Worker, saving from the phone and a way to get Pings. The user is probably not technical, so do the work yourself. Explain each step in a line, and ask one thing at a time. Setup runs once, on whatever model the user picked; only the Worker is pinned to Sonnet.

Setup starts when the user asks to set up Graveyard Killer, or when a Graveyard Killer job finds no Library. It does not need an existing Library, so skip SKILL.md's steps 2 and 3. Talk in the language the user writes in. It becomes the Settings language: say so in your first question, so the user can pick another.

**A user who says they already have a Library,** set up on another computer: ask for its link, read its Settings as SKILL.md's step 3 says, which also brings a Library made by an older version up to date ([upgrade.md](upgrade.md)), and do steps 4 and 6 to 9 here, skipping one the user says is already done. For a Library in a folder on the computer, such as Obsidian's, ask for that folder's path on this computer, in the vault synced here. Tell them to keep the scheduled Worker on one computer only, and to delete the task on the other one.

## Steps

1. **What do they save?** Ask what kinds of posts the user saves, such as recipes, places, workouts or AI prompts. If the user mentions an Instagram export already on the computer, run `python3 scripts/graveyard.py "<path>"` and offer its `collections` as Categories. Add one fallback Category for everything else, and confirm the list with the user in one question. Done when you have 2 to 8 Categories, each with a line on what goes in it, and maybe its own fields (a recipe's ingredients, a place's location).

2. **Create the Library.** Ask in one question which Library app the Library should live in: Notion, Google Drive or Obsidian. Most users are not technical, so lead with the easiest and safest choice: recommend Notion, the app Graveyard Killer was built on and the most tested, where the phone saves through Notion's share menu and each post shows its image, and say that it is the one to pick when they are not sure. Then give each other app one plain line on whom it suits and what it costs them, as an alternative: Google Drive suits a user whose files live in Google and who has no Notion account, and its Library is a Google Sheet, a table with no images; Obsidian suits a user who already keeps their notes in an Obsidian vault that syncs with their phone, and its Library stays on this computer, so the sync is theirs to set up, the phone saves by sharing to Obsidian, and asking Claude about their saves and answering a Ping work only here, in the Code tab. Read [library.md](library.md) and the chosen app's file, then follow its setup file: [setup-notion.md](setup-notion.md#create-the-library), [setup-google-drive.md](setup-google-drive.md#create-the-library) or [setup-obsidian.md](setup-obsidian.md#create-the-library). Done when you can read the Settings back.

3. **Pick the time.** Ask at what time the Worker should run every day. Suggest a time when the computer is usually on and awake, such as lunchtime, and say that it runs only while the Claude app is open and the computer is awake. Write the answer in the Settings' Schedule section. Done when the Settings hold it.

4. **Install the tools.** Follow step 1 of [worker.md](worker.md#steps). Done when `check` prints `"ok": true`.

5. **Test one link end to end.** Ask the user for the link of a public post they saved. Capture it as [capture.md](capture.md) says. Then finish only that Entry, as worker.md's [Each Entry](worker.md#each-entry) says, with no dig-up and no Ping. Show them the finished Entry. Done when it is Processed.

6. **Point this computer to the Library.** In the Code tab, the pointer goes in the user's Claude Code memory file, `~/.claude/CLAUDE.md`. Show the user [the pointer](#the-pointer). With their OK, add it at the end of that file. Done when it is saved, or the user said no.

7. **Schedule the Worker,** as [schedule.md](schedule.md) says. Done when the daily task exists and the user has set its model, or the user said to do it later: then tell them to say "schedule the Graveyard Killer worker" when they are ready.

8. **Set up the phone.** Walk the user through it, one step at a time. Done when a shared post arrived in the Library, or the user says they will do it later.
   - **The pointer.** Skip it for a Library that only this computer reaches, such as Obsidian's: no chat on the phone can use it. The Claude apps on the phone and the computer share one set of Instructions, in *Settings → Your Claude → Instructions* (in the Italian app *Impostazioni → Il tuo Claude → Istruzioni*; in another language, give the path in English), which apply to every chat. Give them [the pointer](#the-pointer) to paste there. You cannot write it yourself.
   - **Save through the Library app.** The main way to save, as your Library app's setup file says: [setup-notion.md](setup-notion.md#save-from-the-phone), [setup-google-drive.md](setup-google-drive.md#save-from-the-phone) or [setup-obsidian.md](setup-obsidian.md#save-from-the-phone).
   - **Save through Claude.** The second way, except for a Library that only this computer reaches: share the post to the Claude app's Chat with no text. It costs a short chat, and for TikTok, YouTube and web links it writes a first summary at once. From Instagram it gets only the link.

9. **Pick how Pings arrive.** Explain that a run sends a Ping only when it has an offer for them or a problem only they can fix. The Ping waits in that run's chat, in Claude Desktop on this computer, and they can answer it there or from any Claude chat, on the phone too, by naming Graveyard Killer, such as "Graveyard Killer, yes to 1". For a Library that only this computer reaches, such as Obsidian's, they answer only here, in the Code tab. Recommend `email`, which brings the whole Ping to the phone. Offer, and write the choice to "Ping by" in the Settings' Pings section. Then send a test Ping through it and ask whether it arrived. Done when the user confirms, or chose `none`.
   - `email`: the whole Ping, in an email to themselves through their Gmail connector. If their Gmail app notifies only for important mail, a Gmail filter on the subject "Graveyard Killer" with *Always mark it as important* makes it notify.
   - `push`: a notification on this computer, from Claude Desktop. It does not reach the phone, since scheduled runs are never connected to Remote Control.
   - `none`: no alert. They open the run's chat in the Claude app when they like, or ask any chat "Graveyard Killer, what did you offer?"

10. **Offer the Graveyard.** Explain that their old saves can come in as Buried Entries, and how to request the exports (see [graveyard.md](graveyard.md#import-the-graveyard)). An export can take up to 30 days on Instagram and a few days on TikTok, and its download link expires after a few days. Once they arrive, the user says "import my Graveyard Killer graveyard". Done when you have told them.

11. **Say how updates arrive.** To get the newest version, the user opens *Customize → Plugins* in the Claude app and selects *Check for updates* on the Graveyard Killer marketplace. Done when you have told them.

12. **Say the Instagram risk once.** Graveyard Killer reads posts without the user's login, so their account is not used. Instagram may still slow down or block reading from their connection if it reads many posts at once, so a run reads at most 20 posts a day and 100 a week, with a pause between Instagram posts, and stops reading Instagram at the first challenge. Done when you have told them.

## The pointer

Two lines in the user's language, with the Library link and no query string. The first line stays exactly as written; translate the second. In English:

```
Graveyard Killer Library: <link>
It holds the posts I saved. Look there when I ask about something I saved, or when we talk about a topic it may hold.
```

In Italian:

```
Graveyard Killer Library: <link>
Lì ci sono i post che ho salvato. Cercaci quando ti chiedo di qualcosa che ho salvato o quando parliamo di un argomento che potrebbe contenere.
```
