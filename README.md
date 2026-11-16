# Graveyard Killer

Your saved posts are a graveyard. Graveyard Killer turns them into a Library in your own Notion or Google Drive. Share a post from your phone, and your computer later watches it, reads what it says and files it. When something you saved is worth doing this week, such as a concert date or a recipe for the weekend, Claude messages you with an offer, and does nothing until you say yes. It needs no server and no API keys.

**Status: early release (0.7.0).** Tested with Claude on Android and on a Mac. A tester ran the Worker end to end on Windows 11 ([#1](https://github.com/andreadorizza/graveyard-killer/issues/1)). iPhone and Linux should work the same way but are untested. The Library lives in Notion or, new in 0.5.0, in Google Drive; saving to Drive from an iPhone is untested. Claude only: Codex support is being tested ([#3](https://github.com/andreadorizza/graveyard-killer/issues/3)).

## What you need

- A paid Claude plan (Pro or above). Plugins and the Code tab, where setup and the daily run happen, are not on the free plan.
- Claude Desktop on your computer, and the Notion or Google Drive app on your phone.
- For a Notion Library, Notion connected to Claude in *Customize → Connectors*. For a Google Drive Library, both Google Drive and Google Sheets, connected there.

## Install

1. In Claude Desktop, open *Customize → Plugins → Add marketplace* and paste `https://github.com/andreadorizza/graveyard-killer`.
2. Find **Graveyard Killer** under *Discover* and add it. Adding the marketplace alone is not enough.
3. In the Code tab, open a session in an empty folder and type `Set up Graveyard Killer`. Setup asks what you save and whether your Library lives in Notion or Google Drive, creates it, schedules the daily run, tests one post end to end and shows you how to save from the phone.

To get a new version, open *Customize → Plugins* and choose *Check for updates* on this marketplace. After an update, the next tidy-up brings your Library up to date by itself, and its message tells you if something needs you, such as updating the schedule.

Other agents can install the skills with `npx skills add andreadorizza/graveyard-killer`, with a Notion, or Google Drive and Sheets, MCP server and your own scheduler. That route is untested.

## How it works

- **Saving.** Share a post from Instagram, TikTok or YouTube to Notion, into your Library's Entries, or to Drive, into your Library's "Share here" folder. It costs no tokens and works with your computer off. *This changed after the launch video*, which shows sharing to the Claude app; that still works, as a second way.
- **Placeholders.** Your phone cannot watch the video, and neither can Claude on your phone. Until your computer reads a post, its card is a placeholder, and its title starts with ⏳.
- **Gallery.** In Notion, your Library's Entries have a gallery tab: one card per post, with its image, grouped by Category, as well as a list of what waits to be read and a board by status. Drive keeps its table, since Sheets shows no images.
- **The daily run.** A scheduled task in the Code tab, while the app is open and the computer is awake. It downloads each new post, transcribes it, reads its on-screen text, completes the card and deletes the video. It runs on Sonnet, so it does not spend your Opus usage, and it skips old saves when your weekly usage is high.
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
