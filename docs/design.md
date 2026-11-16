# Graveyard Killer: v1 design

Saved posts die in a folder nobody opens. Graveyard Killer takes a post you share from your phone, works out what it says, files it in your Library, and brings it back to you in a weekly Digest. It needs no server and no API keys. Terms are defined in [GLOSSARY.md](../GLOSSARY.md); the load-bearing decisions are in [docs/adr/](adr/).

## Changed in 0.4.0

This page records v1. Version 0.4.0 changes it after the launch feedback; where they differ, the skill files and the ADRs win.

- **Saving** goes through Notion's share sheet first, and the Worker adopts the rows it writes ([ADR-0004](adr/0004-notion-share-sheet-captures.md)). Sharing to the Claude app stays as the second way.
- **Every exchange is a chat** ([ADR-0003](adr/0003-every-exchange-is-a-chat.md)). No more Digest pages: a run sends a Ping with Proposals or fixes, remembers Preferences, and brings the Digest after a week with no Ping.
- **The Worker runs daily** on Sonnet, through its own `graveyard-killer-worker` skill, within download limits (20 a day, 100 a week) and the plan's usage ([ADR-0001](adr/0001-no-server-no-api-keys.md)).
- **Placeholders** carry ⏳ in their title until the Worker reads them, and replies never promise a time.
- **The pointer** to the Library, with a recall hint, lives in the account-wide Instructions instead of chat memory ([ADR-0002](adr/0002-settings-live-in-the-library.md)).

## Changed in 0.4.4

- **Library apps.** A Library lives in one Library app. Jobs name the operations in `library.md`, and each app has its own files that say how it does them, so an agent loads only its own app's rules ([ADR-0005](adr/0005-a-library-in-more-than-one-app.md)). Notion is the only app in 0.4.4; Google Drive follows.

## Changed in 0.5.0

- **Google Drive** is the second Library app: one Sheet with an Entries tab and a Settings tab, and the folders "Share here" and "Already read" ([ADR-0005](adr/0005-a-library-in-more-than-one-app.md)). Setup asks which app, recommending Notion.
- **A shared save with no link** is set aside. On Drive it moves to "Already read" and the next Ping names it; on Notion it stays where it is.

## Parts

- **Plugin.** A Claude plugin marketplace with one plugin. Inside it is a standard Agent Skill: `SKILL.md` plus Python scripts. Both scripts, Capture's link script and the Worker's post script, use only the Python standard library and run with `python3`, so the link script also runs in a phone app's sandbox. The tools the post script calls (yt-dlp, gallery-dl, Whisper) are installed with uv. Everything is written in English, and the agent talks in the user's language.
- **Library.** Notion, Google Sheets or a markdown folder, chosen at setup. Field names are in the user's language. The Library holds its own **Settings**: Categories and their fields, language, schedule. Markdown works from the computer only.
- **Memory.** One line on each agent surface says where the Library is. In Claude the apps share one chat memory and the Code tab keeps its own. Setup writes the Code tab's and gives the user the message that saves the chat one, since a Code tab session cannot write chat memory. If the line is missing, the skill asks for the link once.
- **Worker.** A local scheduled task in the Claude Desktop Code tab. It runs weekly by default (setup can change it), while the app is open and the computer is awake, and does one catch-up run after sleep. "Run the Graveyard Killer worker" runs it on demand.

## Flow

1. **Capture, on the phone.** You share a link to the agent app. For TikTok, YouTube and other links, the agent reads a preview from public pages, then files an Entry in the Inbox with a first Category, summary and Next action. For Instagram it files the link only, because Instagram refuses agent fetches and its embed page no longer carries the caption. The Worker fills in the rest. The same link twice stays one Entry, and the second capture is noted.
2. **Worker run, weekly.**
   - Download: yt-dlp for video, gallery-dl for photos and carousels.
   - Extract: YouTube's own captions when present. Otherwise speech-to-text: Parakeet-TDT v3 on Apple Silicon, which covers 25 European languages and makes up far less over music, with Whisper turbo for other languages. Whisper turbo alone elsewhere. The agent reads on-screen text from keyframes.
   - Finish the Entry: the agent's analysis, a stored thumbnail (none in Sheets), then the media is deleted (a setting keeps it).
   - Dig up the run's quota of Buried Entries, newest first.
   - Last step: write the "Week of …" Digest.
3. **Digest.** Written weekly, or on request in any chat. When it is shown, the agent may offer Proposals drawn from what the posts say (add a near event to the calendar, try a recipe this weekend), and it acts only on a yes. It also lists the Entries whose date is in the next 14 days, the Entries the Worker could not finish, and reminds you every 3 months to re-import your Graveyard.

**Statuses:** Inbox → Processed → Used or Dismissed. Also Unavailable (the post is gone; the preview is kept) and Buried.

## Instagram account safety

Instagram has locked sessions for "suspected scraping" after a few dozen downloads, and no safe rate is known. So:
- Every Instagram post is tried without login first.
- The login is a fallback: a few posts per run, with long random pauses.
- At the first Instagram challenge, the run stops reading Instagram, and those posts wait for next week. TikTok and YouTube posts carry on.

Setup states the risk. TikTok and YouTube use the normal path. A login failure leaves the Entry in the Inbox with a note ("log in to Instagram in Chrome"). Windows reads cookies from Firefox or an exported `cookies.txt`, since Chrome's are encrypted there.

## The Graveyard

- **Source:** official exports only.
  - Instagram's "Download your information" gives saved posts (link, date, author) and collections with their names. Parse it by structure, because labels follow the account language.
  - TikTok's "Download your data" gives Favorites (link, date).
  - Google Takeout gives YouTube Liked videos and playlists. Watch Later is excluded; copy it into a playlist first.
- **Import:** every post becomes a Buried Entry. Instagram collections seed the Categories at setup, and each Buried Entry starts in its collection's Category.
- **Drip:** each run digs up 10 Buried Entries by default; you can steer it ("dig up my recipes next"). An Amnesty Dismisses every Buried Entry older than a date.
- **Never touch the platforms:** nothing is unsaved or changed on Instagram, TikTok or YouTube. Re-imports skip links already in the Library.

## Setup

Setup is a conversation on the computer, in the Code tab, after the plugin is added.

1. "What do you save?" plus any Instagram collections → Categories and their fields.
2. Pick the Library; the agent creates it with its Settings.
3. Pick the weekly day.
4. Pick the browser you are logged in with.
5. The agent installs the tools, asking first: uv, ffmpeg, yt-dlp, gallery-dl, Parakeet (on Apple Silicon) and Whisper.
6. Test one link end to end, and approve the Library tools with "always allow" so scheduled runs never stall.
7. The agent saves the Library link to memory and creates the weekly task.
8. On the phone: connect Notion or Sheets, and share a test link.
9. Optional: request the Graveyard exports. They arrive in hours to about 2 days. Then say "import my Graveyard".

## Scope of v1

- **In:**
  - Instagram (reels, carousels, photos), TikTok and YouTube. Other links are filed with whatever the page shows.
  - Tested with Claude on Android (Pixel) and Mac. The iPhone's Share menu also sends to Claude (https://support.claude.com/en/articles/10263469), so iOS capture should work the same way, untested. Claude Desktop's Code tab also runs on Windows and Linux (beta), untested.
- **Out:**
  - Instagram Stories.
  - Terminal-agent scheduling.
  - Pushing into other apps.
  - Thumbnails in Sheets.

## Release

- MIT license, on a public GitHub repo that is a Claude plugin marketplace.
- Claude users add it from *Customize → Plugins → Add marketplace*. It reaches web, desktop, mobile and Claude Code. Each push to `main` raises the plugin's version, so the update reaches every install.
- Other agents install it with `npx skills add`. A ZIP upload is the fallback.
- Submit to Anthropic's directory once v1 works on the Pixel and the Mac.
- The README states the Instagram account risk.

## To verify while building

- [x] The plugin's skill loads in the Claude Android app, and Capture works from Instagram's share menu. (Pixel, 2026-10-24: the Entry was created with Status Inbox.)
- [x] The synced plugin loads in the Desktop Code tab and inside its scheduled tasks. (2026-10-24: it loads in a new Code tab session. 2026-10-26: a scheduled run loaded it, used the Notion connector in Auto mode and stopped for no approval.)
- [ ] The installed plugin picks up a new version. (2026-10-26: the Claude app's copy was still at `c80c2cf` two days and several pushes later, and *Check for updates* said "No changes since the last release". Cause: `plugin.json` kept `"version": "0.1.0"` from the first commit, and an install gets new files only when the plugin's version changes (https://code.claude.com/docs/en/plugins/host-marketplace, "Release a new version"). Every push to `main` now raises the version (AGENTS.md, "Releases"), starting with 0.2.0. Per https://claude.com/docs/plugins/overview, *Check for updates* on the marketplace in *Customize → Plugins* pulls the latest, and Setup says so. The same page offers *Sync automatically* for a marketplace added from github.com but does not say what it does; for organisations it needs a webhook and admin rights on the repo (https://support.claude.com/en/articles/13837433), so Setup does not promise it. Not checked yet: the app's copy moves to 0.2.0.)
- [ ] ✗ Claude's fetch tool reads the caption from the embed page. (2026-10-24: refused on the Pixel. From a home connection, the embed page is now a page that JavaScript fills in, with no caption in its HTML, even for public posts.)
- [ ] Claude's fetch tool on the phone accepts a preview URL that the agent built (the embed page, YouTube oEmbed). Its docs say it fetches only URLs already in the conversation. (2026-10-24 on the Pixel: every Instagram preview URL was refused. A YouTube Short got a full preview, with author, title, Summary and Next action. Which of its two preview URLs served it is not recorded.)
- [ ] ✗ The fetch tool's text keeps the TikTok caption and the YouTube description from the post page. Their oEmbed endpoints do not return them. (2026-10-24 on the Pixel: a shared TikTok gave no preview at all. YouTube gave the title but not the description.)
- [x] A shared link with no text triggers the skill in the Android app, through the skill's description alone. Memory holds no Capture rule to fall back on. (Pixel, 2026-10-24.)
- [ ] TikTok short links and Instagram `/share/` links resolve to one canonical link, so the same post shared twice stays one Entry. (2026-10-24: TikTok's Android share gives a `vm.tiktok.com` short link. Capture could not resolve it on the Pixel, so the Worker must. yt-dlp resolves it: the `webpage_url` it returns, run through the link script, gives the canonical link.)
- [ ] The Notion connector stores a 2,200-character caption in one field. (Notion's limit is 2,000 characters per text value, so longer captions overflow into the page body. The connector also reads text as Markdown, so `*` and `_` must be escaped.)
- [x] The Worker finishes the Inbox by hand. (2026-10-25, a fresh agent following only the skill's files, on 3 Entries: all Processed in about 16 minutes. Parakeet transcribed all three. The TikTok short link resolved. Reading took 23 s for the reel, 4 m 49 s for a 10-minute video and 4 m 26 s for a 14-minute one.)
- [ ] ✗ The Notion connector uploads a local file and sets it as an Entry's page cover. (2026-10-25: the upload works, but a page cover can only be an external link. YouTube Entries use the stable `i.ytimg.com` thumbnail; Instagram and TikTok links expire, so those Entries get no cover.)
- [ ] The Notion connector moves an Entry to the trash (used for merging duplicates). (2026-10-25: it trashes a page only on the user's explicit say-so, so the Worker asks at the end of the run. A real duplicate has not been tested yet.)
- [x] The Digest brings up a near date and offers content-based Proposals. (2026-10-26: two fresh-agent "mostrami il riepilogo" runs on "Graveyard Killer Digest Test", a copy of the test Library with four made-up Entries: an event on 7 November, a recipe, a dug-up trek, an Inbox Entry with a Note. Run 1 listed Entries twice and flagged nine unclear lines; digest.md was fixed. Run 2 put the event under "In programma", each Entry once, and offered the calendar, a shopping list and a new Category, acting on none. The Worker writing a date into a real post's Next action is not tested yet.)
- [x] Instagram carousels and photo posts can be read without a login. (2026-10-25: gallery-dl was sent to the login page. yt-dlp with `--ignore-no-formats-error` read a 7-slide carousel's caption, its account and its 720x900 images, so yt-dlp reads photo posts and gallery-dl is only the fallback.)
- [ ] yt-dlp or gallery-dl reads TikTok photo posts.
- [x] Claude's Sheets connector can append rows to an existing sheet. (2026-11-12: `appendCells` and `updateCells` through `update_spreadsheet`, with text as `stringValue`, keep `=1+1`, `+39 333`, `3/4` and `007` as written, fill the empty rows below the data and keep the column's dropdown. `update_values` and `append_values` parse values as if typed, and appended rows lose the dropdown.)
- [x] Dates on Drive sort and read back as dates. (2026-11-13: `=DATE(2026,11,12)` sorts and counts as a date. It reads back through `get_values` as `2026-11-12` in a column formatted `yyyy-mm-dd`, and as `12/11/2026` in an en_GB Sheet without that format, so Setup formats the date columns.)
- [x] How much one Sheets read returns. (2026-11-13, a 1,000-row test tab, in Claude Code: one ~40-character column of 1,000 rows came back whole, about 38,000 characters. Five short columns of 1,000 rows (330,000 characters), and of 200 rows (66,000), were refused as larger than the tool result's limit and saved to a file. So a Drive Library is read one column at a time, in pages of 200 rows, and long cells one at a time.)
- [ ] A phone Capture and a Worker run write to a Drive Library at the same moment without colliding. (`appendCells` runs on Google's side, and three back-to-back writes did not collide on 2026-11-12. A real simultaneous write is untested.)
- [ ] Saving from an iPhone through Drive's share sheet. (Tested on Android on 2026-11-11, by the contributor who proposed the Drive Library.)
- [ ] The Instagram export parser handles a real export, including collections with no save date.
- [x] Anonymous yt-dlp works for public reels from a home connection. (2026-10-24, yt-dlp 2026.10.21, metadata only, no cookies: an Instagram reel gave its author, its full caption and 8 formats. A TikTok short link gave its author, its caption and 10 formats.)
- [x] The Worker runs on Sonnet. (2026-11-11, CLI with the plugin loaded from the repo: a plain `model: sonnet` line did nothing when the model invoked the skill, and every turn ran on Opus. With `context: fork`, Sonnet did the Worker's work and Opus only started it and passed on its message. 2026-11-14 and 2026-11-16, Desktop scheduled task: the fork ran on Sonnet, and the run's chat showed its final message word for word. The task's own model was Sonnet too, as Setup asks ([#4](https://github.com/andreadorizza/graveyard-killer/issues/4)).)
- [x] Notion's query allowance. (2026-11-11: on a plan below Business, filtered and SQL queries share an allowance that resets within the hour, and heavy testing used it up. Reading a database view still worked.)
- [ ] ✗ A push from a scheduled run reaches the phone. (2026-11-11, two runs: the push tool skipped it as "terminal active", and the Mac showed only the app's task-finished banner. Scheduled runs are not connected to Remote Control, so the tool has no route to the phone.)
- [ ] ✗ The user can answer a scheduled run's chat from the phone. (2026-11-11: the run's chat did not show in the phone app. Remote Control connects only sessions the user starts, and `set_remote_control` refuses unattended sessions. Still so on 2026-11-16: that day's run had Remote Control off.)
- [ ] The user answers the last Ping from a chat on the phone. (0.7.0 saves each Ping's numbered offers in the Settings' "Open offers", and the email carries the whole Ping. Worker eval 17 covers a fresh chat on the computer. Untested on the phone, [#2](https://github.com/andreadorizza/graveyard-killer/issues/2).)
- [x] Which fields a page shared from Instagram through Notion's share sheet fills, and where its link sits. (2026-11-11, Pixel, into the test Library: the Link field holds the reel's link with a `psln` query, the title is what the user typed, the body is an embed of the link, and Status is empty.)
- [x] An email to yourself from a scheduled run, through the Gmail connector, arrives (2026-11-11, Auto mode). Gmail showed no notification because it didn't mark it as important.
- [ ] ✗ A Notion comment mentioning the user, made through their own connector, notifies them. (2026-11-11: the comment was created; no notification came. Dropped in 0.4.2.)
- [x] A scheduled run can read the plan's usage. (2026-11-11: it could, with Claude Desktop's `get_usage`.)
