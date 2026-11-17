# Graveyard Killer

Your saved posts are a graveyard. Graveyard Killer turns them into a Library in your own Notion or Google Drive. Share a post from your phone, and your computer later watches it, reads what it says and files it. When something you saved is worth doing this week, such as a concert date or a recipe for the weekend, Claude messages you with an offer, and does nothing until you say yes. It needs no server and no API keys.

**Status: early release (0.9.0).** Tested with Claude on Android and on a Mac. A tester ran the Worker end to end on Windows 11 ([#1](https://github.com/andreadorizza/graveyard-killer/issues/1)). iPhone and Linux should work the same way but are untested. The Library lives in Notion or, new in 0.5.0, in Google Drive; saving to Drive from an iPhone is untested. New in 0.9.0, a [free route](#free-route-opencode) runs the daily run in OpenCode on a free model, and [Codex](#codex) runs it in the ChatGPT desktop app, on any ChatGPT plan; both are tested on a Mac only.

## What you need

- A paid Claude plan (Pro or above). Plugins and the Code tab, where setup and the daily run happen, are not on the free plan. With no paid plan, use the [free route](#free-route-opencode), or [Codex](#codex) with a ChatGPT account.
- Claude Desktop on your computer, and the Notion or Google Drive app on your phone.
- For a Notion Library, Notion connected to Claude in *Customize → Connectors*. For a Google Drive Library, both Google Drive and Google Sheets, connected there.

## Install

1. In Claude Desktop, open *Customize → Plugins → Add marketplace* and paste `https://github.com/andreadorizza/graveyard-killer`.
2. Find **Graveyard Killer** under *Discover* and add it. Adding the marketplace alone is not enough.
3. In the Code tab, open a session in an empty folder and type `Set up Graveyard Killer`. Setup asks what you save and whether your Library lives in Notion or Google Drive, creates it, schedules the daily run, tests one post end to end and shows you how to save from the phone.

To get a new version, open *Customize → Plugins* and choose *Check for updates* on this marketplace. After an update, the next tidy-up brings your Library up to date by itself, and its message tells you if something needs you, such as updating the schedule.

Other agents can install the skills with `npx skills add andreadorizza/graveyard-killer`, with a Notion, or Google Drive and Sheets, MCP server and your own scheduler. That route is untested.

## Free route: OpenCode

With no paid Claude plan, the daily run happens in [OpenCode](https://opencode.ai), a free coding agent, on one of its free models that keep no data and do not train on it. Your computer's own scheduler starts it every day. It needs:

- OpenCode on your computer: its desktop app or its terminal version, from [opencode.ai/download](https://opencode.ai/download). No account or API key is needed for its free models.
- A Notion Library. Google Drive needs Claude's connectors, so it is not on the free route.
- Python 3 on your computer, as for the paid route.

Then:

1. Open OpenCode, pick **DeepSeek V4.1 Flash Free** in its model list, and send:

   ```
   Install Graveyard Killer: follow https://raw.githubusercontent.com/andreadorizza/graveyard-killer/main/plugin/skills/graveyard-killer/references/opencode.md#install
   ```

   It downloads the skills, adds Notion and opens Notion in your browser to sign in.
2. Quit and reopen OpenCode, and type `Set up Graveyard Killer` in a new chat. Setup works as on the paid route. It schedules the daily run with your computer's scheduler: on a Mac it runs when the computer is awake, whether or not OpenCode is open, and a run missed while it slept happens when it wakes.

What is different from the paid route:

- **Pings** come as a notification on your computer, or not at all: OpenCode has no email connector. The whole message waits in the run's chat in OpenCode, in the `graveyard-killer` folder in your home folder. You can also answer from the Claude app on your phone, which works on the free plan: connect Notion to Claude and paste Setup's two lines into your Instructions.
- **Free models are free "for a limited time"**, as OpenCode says. They also have a usage limit that OpenCode does not show: when a run hits it, it switches to the second model, GLM-5.3-Flash Free. When a model goes for good, you pick a new one.
- **Updates**: tell OpenCode "update Graveyard Killer".
- Untested: Windows, Linux, OpenCode's desktop app and OpenCode 2.x. The tests used OpenCode 1.19.5 in a terminal on a Mac. Capture and Recall in a free Claude chat are untested too.

## Codex

With a ChatGPT account, on any plan, Free included, the daily run happens in Codex, the coding agent in the ChatGPT desktop app. The app's own *Scheduled* view starts it every day, and there you see each run, change its time or run it now. It needs:

- The ChatGPT desktop app, from [chatgpt.com/download](https://chatgpt.com/download/) for a Mac or Windows (Linux has a preview), signed in. OpenAI lists Codex on Free and Go "in the desktop app, subject to rollout".
- A Notion Library. Google Drive is tested with Claude only.
- Python 3 on your computer, as for the paid route.

Then:

1. In the ChatGPT app, open Codex, start a new chat and send:

   ```
   Install Graveyard Killer: follow https://raw.githubusercontent.com/andreadorizza/graveyard-killer/main/plugin/skills/graveyard-killer/references/codex.md#install
   ```

   It downloads the skills into `~/.agents/skills`, adds Notion and opens Notion in your browser to sign in. Codex asks you to approve each step.
2. Start a new chat and type `Set up Graveyard Killer`. Setup works as on the paid route, and creates a scheduled task that runs in the `graveyard-killer` folder in your home folder.

What is different from the paid route:

- **Your data and OpenAI.** On ChatGPT's personal plans, OpenAI may use your chats, Codex's included, to train its models unless you turn off *Improve the model for everyone* in *Settings → Data controls*. Setup asks you to turn it off, since your saved posts and Library go through those chats.
- **A fenced run.** The scheduled task starts the run with one command, and the run itself happens in the run folder, under Codex's own settings for that folder: its commands can read only the skills and that folder and cannot reach the internet, and only Graveyard Killer's own scripts can download and transcribe. The app would otherwise run a task with your usual Codex permissions, which can read your whole disk.
- **The run happens only while the ChatGPT app is running** and the computer is awake.
- **Pings** come as a notification on your computer, or not at all. The whole message waits in the run's chat, under *Scheduled* in the app.
- **Updates**: tell Codex "update Graveyard Killer".
- Untested: Windows, Linux, and plans other than Free. The tests used the ChatGPT app 26.1111 on a Mac, on a Free account, with GPT-6 Luna.

## How it works

- **Saving.** Share a post from Instagram, TikTok or YouTube to Notion, into your Library's Entries, or to Drive, into your Library's "Share here" folder. It costs no tokens and works with your computer off. *This changed after the launch video*, which shows sharing to the Claude app; that still works, as a second way.
- **Placeholders.** Your phone cannot watch the video, and neither can Claude on your phone. Until your computer reads a post, its card is a placeholder, and its title starts with ⏳.
- **The daily run.** A scheduled task in the Code tab, while the app is open and the computer is awake (on the free route, a job in your computer's scheduler). It downloads each new post, transcribes it, reads its on-screen text, completes the card and deletes the video. It runs on Sonnet, so it does not spend your Opus usage, and it skips old saves when your weekly usage is high.
- **Pings.** A run messages you only when it has something for you: an offer on a post it just read (a grocery list for a recipe, a concert in your calendar) or a problem only you can fix. You answer in that run's chat, in Claude Desktop on your computer, or from any Claude chat, on your phone too: say "Graveyard Killer, yes to 1". With email alerts, the email brings the whole message to your phone. The first time an offer comes up, Claude asks whether you want it always, each time, or never, and remembers your answer in your Library.
- **Recall.** Setup gives you two lines for your Claude Instructions. With them, any chat can look in your Library when you ask about something you saved, or when you talk about a topic it holds.
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
