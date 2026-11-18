# Graveyard Killer

Your saved posts are a graveyard. Graveyard Killer turns them into a Library in your own Notion, Google Drive or Obsidian. Share a post from your phone, and your computer later watches it, reads what it says and files it. When something you saved is worth doing this week, such as a concert date or a recipe for the weekend, Claude messages you with an offer, and does nothing until you say yes. It needs no server and no API keys.

**Status: early release (0.12.1).** Tested with Claude on Android and on a Mac. A tester ran the Worker end to end on Windows 11 ([#1](https://github.com/andreadorizza/graveyard-killer/issues/1)). iPhone and Linux should work the same way but are untested. The Library lives in Notion, in Google Drive (since 0.5.0) or, new in 0.12.0, in an Obsidian vault; saving to Drive or Obsidian from an iPhone is untested. New in 0.11.0, with no paid Claude plan, [Codex](#codex) runs the daily run in the ChatGPT desktop app, on any ChatGPT plan, and [OpenCode](#opencode) runs it on a free model; both are tested on a Mac only.

## Pick your setup

If you are not sure, pick the first one. It is the easiest and the most tested, so it is the safe choice.

- **Claude with a Notion Library (recommended).** You need a paid Claude plan and a Notion account. You type no commands: you add a plugin in Claude Desktop and answer Setup's questions in a chat. On your phone you save a post through Notion's share menu, and Notion shows each post's image.

Other Libraries, also with Claude:

- **Google Drive**, if your files live in Google and you have no Notion: your Library is a Google Sheet, a table with no images.
- **Obsidian**, if you already keep your notes in an Obsidian vault that syncs with your phone: your Library stays on your computer, but the sync is yours to set up, and no Claude chat on your phone can read your Library.

With no paid Claude plan, two routes do the daily run in another app, and both can cost nothing. Both need a Notion Library, ask more of you during setup, send Pings to your computer only, and were tested on a Mac only:

- **[Codex](#codex) in the ChatGPT app**, with the ChatGPT account you may already have, on any plan: OpenAI lists Codex on Free and Go "in the desktop app, subject to rollout". Setup asks you to turn off the setting that lets OpenAI train on your chats, and a run happens only while the ChatGPT app is open.
- **[OpenCode](#opencode)**, if you are at ease installing a coding agent. It needs no account, but its free models have a usage limit that can block them for hours, and they are free only "for a limited time".

## What you need

With Claude, whatever the Library:

- A paid Claude plan (Pro or above). Plugins and the Code tab, where setup and the daily run happen, are not on the free plan. With no paid plan, see [Pick your setup](#pick-your-setup).
- Claude Desktop on your computer, and the Notion, Google Drive or Obsidian app on your phone.
- For a Notion Library, Notion connected to Claude in *Customize → Connectors*. For a Google Drive Library, both Google Drive and Google Sheets, connected there. For an Obsidian Library, a vault on your computer that syncs with your phone, such as through Obsidian Sync, iCloud or Syncthing: no connector.

## Install

1. In Claude Desktop, open *Customize → Plugins → Add marketplace* and paste `https://github.com/andreadorizza/graveyard-killer`.
2. Find **Graveyard Killer** under *Discover* and add it. Adding the marketplace alone is not enough.
3. In the Code tab, open a session in an empty folder and type `Set up Graveyard Killer`. Setup asks what you save and whether your Library lives in Notion, Google Drive or Obsidian (Notion, if you are not sure), creates it, schedules the daily run, tests one post end to end and shows you how to save from the phone.

To get a new version, open *Customize → Plugins* and choose *Check for updates* on this marketplace. After an update, the next tidy-up brings your Library up to date by itself, and its message tells you if something needs you, such as updating the schedule.

Other agents can install the skills with `npx skills add andreadorizza/graveyard-killer`, with a Notion, or Google Drive and Sheets, MCP server and your own scheduler. That route is untested.

## Codex

With a ChatGPT account, on any plan, Free included, the daily run happens in Codex, the coding agent in the ChatGPT desktop app. The app's own *Scheduled* view starts it every day, and there you see each run, change its time or run it now. It suits you if you already use ChatGPT and have no paid Claude plan. It needs:

- The ChatGPT desktop app, from [chatgpt.com/download](https://chatgpt.com/download/) for a Mac or Windows (Linux has a preview), signed in. OpenAI lists Codex on Free and Go "in the desktop app, subject to rollout".
- A Notion Library. Google Drive and Obsidian are tested with Claude only.
- Python 3 on your computer, as for Claude.

Then:

1. In the ChatGPT app, open Codex, start a new chat and send:

   ```
   Install Graveyard Killer: follow https://raw.githubusercontent.com/andreadorizza/graveyard-killer/main/plugin/skills/graveyard-killer/references/codex.md#install
   ```

   It downloads the skills into `~/.agents/skills`, adds Notion and opens Notion in your browser to sign in. Codex asks you to approve each step.
2. Start a new chat and type `Set up Graveyard Killer`. Setup works as in Claude, and creates a scheduled task that runs in the `graveyard-killer-codex` folder in your home folder.

What is different from Claude:

- **Your data and OpenAI.** On ChatGPT's personal plans, OpenAI may use your chats, Codex's included, to train its models unless you turn off *Improve the model for everyone* in *Settings → Data controls*. Setup asks you to turn it off, since your saved posts and Library go through those chats.
- **A fenced run.** The scheduled task starts the run with one command, and the run itself happens in the run folder, under Codex's own settings for that folder: its commands can read only the skills and that folder and cannot reach the internet, and only Graveyard Killer's own scripts can download and transcribe. The app would otherwise run a task with your usual Codex permissions, which can read your whole disk.
- **The run happens only while the ChatGPT app is running** and the computer is awake.
- **Pings** come as a notification on your computer, or not at all. The whole message waits in the run's chat, under *Scheduled* in the app. Answer it there.
- **Your phone.** Save through Notion's share menu, which needs no Claude or ChatGPT. This route installs Graveyard Killer's skills in Codex on your computer only, so a chat on your phone, in the Claude app or the ChatGPT app, does not have them: it cannot be counted on to file a post you share to it, find what you saved or answer a Ping by its number.
- **Updates**: tell Codex "update Graveyard Killer".
- Untested: Windows, Linux, and plans other than Free. The tests used the ChatGPT app 26.1111 on a Mac, on a Free account, with GPT-6 Luna.

## OpenCode

With no paid Claude plan, the daily run can also happen in [OpenCode](https://opencode.ai), a free coding agent, on one of its free models that keep no data and do not train on it. Your computer's own scheduler starts it every day. It suits you if you are at ease installing a coding agent and pasting a command into it; if not, see [Pick your setup](#pick-your-setup). It needs:

- OpenCode on your computer: its desktop app or its terminal version, from [opencode.ai/download](https://opencode.ai/download). No account or API key is needed for its free models.
- A Notion Library. Google Drive needs Claude's connectors, so it is not on the OpenCode route, and Obsidian is tested with Claude only.
- Python 3 on your computer, as for Claude.

Then:

1. Open OpenCode, pick **DeepSeek V4.1 Flash Free** in its model list, and send:

   ```
   Install Graveyard Killer: follow https://raw.githubusercontent.com/andreadorizza/graveyard-killer/main/plugin/skills/graveyard-killer/references/opencode.md#install
   ```

   It downloads the skills, adds Notion and opens Notion in your browser to sign in.
2. Quit and reopen OpenCode, and type `Set up Graveyard Killer` in a new chat. Setup works as in Claude. It schedules the daily run with your computer's scheduler: on a Mac it runs when the computer is awake, whether or not OpenCode is open, and a run missed while it slept happens when it wakes.

What is different from Claude:

- **Pings** come as a notification on your computer, or not at all: OpenCode has no email connector. The whole message waits in the run's chat in OpenCode, in the `graveyard-killer` folder in your home folder. Answer it there.
- **Your phone.** Save through Notion's share menu, which needs no Claude. This route installs Graveyard Killer's skills in OpenCode only, so a chat in the Claude app, free plan included, does not have them: it cannot be counted on to file a post you share to it, find what you saved or answer a Ping by its number. Claude's free plan has the Notion connector and lets you [upload a skill](https://support.claude.com/en/articles/12512180-use-skills-in-claude), but Graveyard Killer is untested there.
- **Free models are free "for a limited time"**, as OpenCode says. They also have a usage limit that OpenCode does not show. In the tests, DeepSeek and GLM-5.3-Flash Free, the second model, reached it together after about 75 minutes of back-to-back runs, and stayed blocked for more than an hour and a half. So the second model does not help then: the run shows a notification, and the next run reads what it left. The second model takes over when the first goes for good; then you pick a new one.
- **Updates**: tell OpenCode "update Graveyard Killer".
- Untested: Windows, Linux, OpenCode's desktop app and OpenCode 2.x. The tests used OpenCode 1.19.5 in a terminal on a Mac.

## How it works

- **Saving.** Share a post from Instagram, TikTok or YouTube to Notion, into your Library's Entries, to Drive, into your Library's "Share here" folder, or to Obsidian, at the end of your Library's "Share here" note. It costs no tokens and works with your computer off. *This changed after the launch video*, which shows sharing to the Claude app; that still works, as a second way.
- **Placeholders.** Your phone cannot watch the video, and neither can Claude on your phone. Until your computer reads a post, its card is a placeholder, and its title starts with ⏳.
- **Gallery.** In Notion, your Library's Entries have a gallery tab: one card per post, with its image, grouped by Category, as well as a list of what waits to be read and a board by status. Drive keeps its table, since Sheets shows no images. In Obsidian, a Base shows the Entries as a table and as cards with their images.
- **The daily run.** A scheduled task in the Code tab, while the app is open and the computer is awake (in Codex, a scheduled task in the ChatGPT app; in OpenCode, a job in your computer's scheduler). It downloads each new post, transcribes it, reads its on-screen text, completes the card and deletes the video. It runs on Sonnet, so it does not spend your Opus usage, and it skips old saves when your weekly usage is high.
- **Pings.** A run messages you only when it has something for you: an offer on a post it just read (a grocery list for a recipe, a concert in your calendar) or a problem only you can fix. You answer in that run's chat, in Claude Desktop on your computer, or from any Claude chat, on your phone too: say "Graveyard Killer, yes to 1". With email alerts, the email brings the whole message to your phone. The first time an offer comes up, Claude asks whether you want it always, each time, or never, and remembers your answer in your Library.
- **Recall.** Setup gives you two lines for your Claude Instructions. With them, any chat can look in your Library when you ask about something you saved, or when you talk about a topic it holds.
- **Obsidian.** Your vault is on your computer, and no Claude chat on your phone can read it. So with an Obsidian Library you save from the phone by sharing to Obsidian, and you ask about your saves or answer a message in the Code tab on your computer. The email still brings each message to your phone.
- **Recap.** Ask "what's new in my Graveyard Killer?" in any chat. If a week passes with no message, the next run sends you the recap.

## Instagram account safety

Graveyard Killer reads posts without your login, so your account is not used. Instagram may still slow down or block reading from your connection if it reads many posts at once. So a run reads at most 20 posts a day and 100 a week, pauses between Instagram posts, and stops reading Instagram at the first challenge. You can change the limits in your Library's Settings.

## Windows

When Claude Desktop installs the tools, uv puts them in the app's own AppData folder (`Packages\Claude_…\LocalCache\Roaming\uv\tools`). They work inside Claude, but outside it they may not be where you expect ([#1](https://github.com/andreadorizza/graveyard-killer/issues/1)).

## Docs

- [Design](docs/design.md): how v1 works, and what changed since
- [Glossary](GLOSSARY.md): the words this project uses
- [Decision records](docs/adr/)
- [Known issues](https://github.com/andreadorizza/graveyard-killer/issues)

## License

[MIT](LICENSE)
